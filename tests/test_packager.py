import tarfile
from pathlib import Path
from unittest.mock import patch

from gcc_portable.packager import GccPackager, PackageConfig


def _create_fake_conda_env(env_path: Path) -> None:
    """Create a minimal fake conda environment directory structure."""
    for dir_name in ("bin", "lib", "include", "share"):
        (env_path / dir_name).mkdir(parents=True)
    (env_path / "bin" / "gcc").write_text("#!/fake/conda/env/bin/python\nprint('gcc')\n")
    (env_path / "bin" / "g++").write_bytes(b"\x7fELF binary content")
    (env_path / "lib" / "libgcc.dylib").write_text("fake lib")
    (env_path / "include" / "gcc_header.h").write_text("#pragma once")
    # Create libexec structure matching real conda-forge layout
    libexec_ver = env_path / "libexec" / "gcc" / "arm64-apple-darwin20.0.0" / "15.2.0"
    libexec_ver.mkdir(parents=True)
    (libexec_ver / "cc1").write_text("fake cc1")


def test_extract_portable_tree_copies_expected_dirs(tmp_path):
    env_path = tmp_path / "conda_env"
    portable_dir = tmp_path / "gcc-14"
    _create_fake_conda_env(env_path)

    config = PackageConfig(gcc_version="14", output_dir=tmp_path / "dist")
    packager = GccPackager(config, "micromamba")
    packager._extract_portable_tree(env_path, portable_dir)

    assert (portable_dir / "bin" / "gcc").exists()
    assert (portable_dir / "lib" / "libgcc.dylib").exists()
    assert (portable_dir / "include" / "gcc_header.h").exists()
    assert (portable_dir / "share").exists()


def test_extract_portable_tree_skips_missing_dirs(tmp_path):
    env_path = tmp_path / "conda_env"
    portable_dir = tmp_path / "gcc-14"
    (env_path / "bin").mkdir(parents=True)
    (env_path / "bin" / "gcc").write_text("#!/usr/bin/env python\nprint('gcc')\n")

    config = PackageConfig(gcc_version="14", output_dir=tmp_path / "dist")
    packager = GccPackager(config, "micromamba")
    packager._extract_portable_tree(env_path, portable_dir)

    assert (portable_dir / "bin" / "gcc").exists()
    assert not (portable_dir / "lib").exists()


def test_patch_shebangs_replaces_conda_prefix(tmp_path):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    script = bin_dir / "my-script"
    script.write_text("#!/some/conda/env/bin/python\nimport sys\n")

    config = PackageConfig(gcc_version="14", output_dir=tmp_path / "dist")
    packager = GccPackager(config, "micromamba")
    packager._patch_shebangs(bin_dir, "/some/conda/env")

    content = script.read_text()
    assert content.startswith("#!/usr/bin/env python\n")
    assert "import sys" in content


def test_patch_shebangs_preserves_non_matching_shebangs(tmp_path):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    script = bin_dir / "other-script"
    original = "#!/usr/bin/env bash\necho hello\n"
    script.write_text(original)

    config = PackageConfig(gcc_version="14", output_dir=tmp_path / "dist")
    packager = GccPackager(config, "micromamba")
    packager._patch_shebangs(bin_dir, "/some/conda/env")

    assert script.read_text() == original


def test_create_archive_produces_tarball(tmp_path):
    portable_dir = tmp_path / "gcc-14"
    portable_dir.mkdir()
    (portable_dir / "bin").mkdir()
    (portable_dir / "bin" / "gcc").write_text("fake gcc")
    output_dir = tmp_path / "dist"

    output_dir.mkdir(parents=True)
    config = PackageConfig(gcc_version="14", output_dir=output_dir)
    packager = GccPackager(config, "micromamba")
    archive_path = packager._create_archive(portable_dir)

    assert archive_path.exists()
    assert archive_path.name.startswith("gcc-14-0-darwin-")
    assert archive_path.suffix == ".gz"
    with tarfile.open(archive_path, "r:gz") as tar:
        names = tar.getnames()
        assert any("bin/gcc" in name for name in names)


def test_fix_libexec_rpaths_creates_lib_symlink(tmp_path):
    portable_dir = tmp_path / "gcc-15"
    (portable_dir / "lib").mkdir(parents=True)
    (portable_dir / "lib" / "libtapi.dylib").write_text("fake")
    triple_dir = portable_dir / "libexec" / "gcc" / "arm64-apple-darwin20.0.0"
    (triple_dir / "15.2.0").mkdir(parents=True)

    config = PackageConfig(gcc_version="15", output_dir=tmp_path / "dist")
    packager = GccPackager(config, "micromamba")
    packager._fix_libexec_rpaths(portable_dir)

    lib_link = triple_dir / "lib"
    assert lib_link.is_symlink()
    assert (lib_link / "libtapi.dylib").exists()


def test_fix_libexec_rpaths_skips_existing_lib(tmp_path):
    portable_dir = tmp_path / "gcc-15"
    (portable_dir / "lib").mkdir(parents=True)
    triple_dir = portable_dir / "libexec" / "gcc" / "some-triple"
    (triple_dir / "lib").mkdir(parents=True)
    (triple_dir / "15.0.0").mkdir(parents=True)

    config = PackageConfig(gcc_version="15", output_dir=tmp_path / "dist")
    packager = GccPackager(config, "micromamba")
    packager._fix_libexec_rpaths(portable_dir)

    assert not (triple_dir / "lib").is_symlink()


def test_package_end_to_end(tmp_path):
    output_dir = tmp_path / "dist"
    config = PackageConfig(gcc_version="14", output_dir=output_dir)
    packager = GccPackager(config, "/usr/local/bin/micromamba")

    def fake_create_env(env_path: Path, packages: list[str], channel: str, micromamba_exe: str) -> None:
        _create_fake_conda_env(env_path)

    with (
        patch("gcc_portable.packager.micromamba.create_environment", side_effect=fake_create_env),
    ):
        archive_path = packager.package()

    assert archive_path.exists()
    assert archive_path.name.startswith("gcc-14-0-darwin-")
    with tarfile.open(archive_path, "r:gz") as tar:
        names = tar.getnames()
        assert any("bin/gcc" in name for name in names)
        assert any("lib/libgcc.dylib" in name for name in names)
