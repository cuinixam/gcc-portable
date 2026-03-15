"""Core packaging logic for creating portable GCC archives."""

import platform
import re
import shutil
import tarfile
from dataclasses import dataclass
from pathlib import Path

from py_app_dev.core.logging import logger

from gcc_portable import micromamba

PORTABLE_DIRS = ("bin", "lib", "libexec", "include", "share")
CONDA_CHANNEL = "conda-forge"
ARCH_MAP = {"x86_64": "x64"}


@dataclass
class PackageConfig:
    """Configuration for GCC packaging."""

    gcc_version: str
    output_dir: Path
    build_number: str = "0"


class GccPackager:
    """Packages GCC from conda-forge into a portable macOS archive."""

    def __init__(self, config: PackageConfig, micromamba_exe: str) -> None:
        self.config = config
        self.micromamba_exe = micromamba_exe
        self.arch = ARCH_MAP.get(platform.machine(), platform.machine())

    def package(self) -> Path:
        """Create a portable GCC archive. Returns the path to the archive."""
        self.config.output_dir.mkdir(parents=True, exist_ok=True)
        env_path = self.config.output_dir / "conda_env"
        portable_dir = self.config.output_dir / f"gcc-{self.config.gcc_version}"
        try:
            micromamba.create_environment(env_path, [f"gcc={self.config.gcc_version}"], CONDA_CHANNEL, self.micromamba_exe)
            self._extract_portable_tree(env_path, portable_dir)
            return self._create_archive(portable_dir)
        finally:
            logger.info("Cleaning up intermediate directories")
            shutil.rmtree(env_path, ignore_errors=True)
            shutil.rmtree(portable_dir, ignore_errors=True)

    def _extract_portable_tree(self, conda_env_path: Path, portable_dir: Path) -> None:
        """Copy relevant directories from conda environment to portable directory."""
        portable_dir.mkdir(parents=True, exist_ok=True)
        for dir_name in PORTABLE_DIRS:
            source = conda_env_path / dir_name
            if not source.exists():
                logger.debug(f"Skipping {dir_name} (not found in conda environment)")
                continue
            destination = portable_dir / dir_name
            logger.info(f"Copying {dir_name} to portable directory")
            shutil.copytree(source, destination, dirs_exist_ok=True)
        old_prefix = str(conda_env_path.resolve())
        self._patch_shebangs(portable_dir / "bin", old_prefix)
        self._patch_specs_files(portable_dir, old_prefix)
        self._fix_libexec_rpaths(portable_dir)

    def _create_archive(self, portable_dir: Path) -> Path:
        """Create a tar.gz archive of the portable directory."""
        archive_name = f"gcc-{self.config.gcc_version}-{self.config.build_number}-darwin-{self.arch}.tar.gz"
        archive_path = self.config.output_dir / archive_name
        logger.info(f"Creating archive: {archive_path}")
        with tarfile.open(archive_path, "w:gz") as tar:
            tar.add(portable_dir, arcname=portable_dir.name)
        return archive_path

    def _fix_libexec_rpaths(self, portable_dir: Path) -> None:
        """
        Create lib symlinks in libexec/gcc/<triple>/ so @loader_path/../lib resolves correctly.

        Binaries in libexec/gcc/<triple>/<version>/ have @loader_path/../lib/ as their rpath.
        This resolves to libexec/gcc/<triple>/lib/ which doesn't exist — the actual libraries
        are in the top-level lib/. We create a relative symlink to bridge the gap.
        This works regardless of GCC version or target triple.
        """
        libexec_gcc = portable_dir / "libexec" / "gcc"
        if not libexec_gcc.exists():
            return
        for triple_dir in libexec_gcc.iterdir():
            if not triple_dir.is_dir():
                continue
            lib_link = triple_dir / "lib"
            if lib_link.exists():
                continue
            # Compute relative path: from libexec/gcc/<triple>/ to top-level lib/
            relative_target = Path(*([".."] * len(triple_dir.relative_to(portable_dir).parts))) / "lib"
            lib_link.symlink_to(relative_target)
            logger.info(f"Created symlink: {lib_link.relative_to(portable_dir)} -> {relative_target}")

    def _patch_specs_files(self, portable_dir: Path, old_prefix: str) -> None:
        """
        Patch GCC specs files to remove hardcoded conda environment paths.

        Conda injects paths into the specs file in two ways:
        1. -idirafter <prefix>/include and -L <prefix>/lib — rewrite to portable dir
        2. -rpath <prefix>/lib in link_command — remove to avoid duplicate with darwin_rpaths
        """
        new_prefix = str(portable_dir.resolve())
        for specs_file in portable_dir.rglob("*.specs"):
            content = specs_file.read_text(encoding="utf-8")
            if old_prefix not in content:
                continue
            # Remove the redundant -rpath that duplicates %(darwin_rpaths)
            patched = re.sub(rf"\s*-rpath\s+{re.escape(old_prefix)}/lib", "", content)
            # Rewrite remaining references (includes, -L paths, darwin_rpaths)
            patched = patched.replace(old_prefix, new_prefix)
            specs_file.write_text(patched, encoding="utf-8")
            logger.info(f"Patched specs file: {specs_file.relative_to(portable_dir)}")

    def _patch_shebangs(self, bin_dir: Path, old_prefix: str) -> None:
        """Replace hardcoded conda prefix in shebangs with portable alternatives."""
        if not bin_dir.exists():
            return
        for file_path in bin_dir.iterdir():
            if not file_path.is_file():
                continue
            try:
                content = file_path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, PermissionError):
                continue
            if not content.startswith("#!"):
                continue
            first_line, _, rest = content.partition("\n")
            if old_prefix not in first_line:
                continue
            binary_name = Path(first_line.split()[-1]).name
            new_shebang = f"#!/usr/bin/env {binary_name}"
            logger.debug(f"Patching shebang in {file_path.name}: {first_line} -> {new_shebang}")
            file_path.write_text(f"{new_shebang}\n{rest}", encoding="utf-8")
