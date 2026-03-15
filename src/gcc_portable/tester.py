"""Test the portable GCC archive by compiling and running a hello world program."""

import os
import subprocess
import tarfile
from pathlib import Path

from py_app_dev.core.exceptions import UserNotificationException
from py_app_dev.core.logging import logger

HELLO_WORLD_C = """\
#include <stdio.h>
int main() {
    printf("Hello from portable GCC!\\n");
    return 0;
}
"""


class GccTester:
    """Extract a GCC portable archive and verify it can compile and run a program."""

    def __init__(self, archive_path: Path, output_dir: Path) -> None:
        self.archive_path = archive_path
        self.output_dir = output_dir

    def run(self) -> None:
        """Extract archive, compile hello world, and run the resulting binary."""
        if not self.archive_path.exists():
            raise UserNotificationException(f"Archive not found: {self.archive_path}")
        gcc_dir = self._extract_archive()
        gcc_bin = self._find_gcc(gcc_dir)
        env = self._build_env(gcc_dir)
        hello_c = self.output_dir / "hello.c"
        hello_bin = self.output_dir / "hello"
        hello_c.write_text(HELLO_WORLD_C)
        self._compile(gcc_bin, hello_c, hello_bin, env)
        self._run_binary(hello_bin)
        logger.info("GCC portable archive test passed!")

    def _extract_archive(self) -> Path:
        """Extract the archive and return the path to the GCC directory."""
        logger.info(f"Extracting {self.archive_path} to {self.output_dir}")
        with tarfile.open(self.archive_path, "r:gz") as tar:
            top_level = {member.name.split("/")[0] for member in tar.getmembers()}
            tar.extractall(path=self.output_dir)
        if len(top_level) != 1:
            raise UserNotificationException(f"Expected single top-level directory in archive, found: {top_level}")
        return self.output_dir / top_level.pop()

    def _find_gcc(self, gcc_dir: Path) -> Path:
        """Find the gcc binary in the extracted directory."""
        bin_dir = gcc_dir / "bin"
        for candidate in bin_dir.iterdir():
            if candidate.name == "gcc" or (candidate.name.endswith("-gcc") and "darwin" in candidate.name):
                logger.info(f"Found GCC binary: {candidate}")
                return candidate
        raise UserNotificationException(f"No gcc binary found in {bin_dir}")

    def _build_env(self, gcc_dir: Path) -> dict[str, str]:
        """Build environment with gcc bin directory prepended to PATH."""
        env = os.environ.copy()
        bin_dir = str(gcc_dir.resolve() / "bin")
        lib_dir = str(gcc_dir.resolve() / "lib")
        env["PATH"] = f"{bin_dir}:{env.get('PATH', '')}"
        env["DYLD_LIBRARY_PATH"] = f"{lib_dir}:{env.get('DYLD_LIBRARY_PATH', '')}"
        logger.info(f"Added {bin_dir} to PATH")
        return env

    def _compile(self, gcc_bin: Path, source: Path, output: Path, env: dict[str, str]) -> None:
        """Compile the source file using the portable GCC."""
        logger.info(f"Compiling {source} with {gcc_bin}")
        try:
            result = subprocess.run(
                [str(gcc_bin), str(source), "-o", str(output)],
                check=True,
                capture_output=True,
                text=True,
                env=env,
            )
            if result.stderr:
                logger.warning(f"Compiler warnings: {result.stderr}")
        except subprocess.CalledProcessError as err:
            raise UserNotificationException(f"Compilation failed:\n{err.stderr}") from err

    def _run_binary(self, binary: Path) -> None:
        """Run the compiled binary and verify output."""
        logger.info(f"Running {binary}")
        try:
            result = subprocess.run(
                [str(binary)],
                check=True,
                capture_output=True,
                text=True,
            )
            logger.info(f"Output: {result.stdout.strip()}")
        except subprocess.CalledProcessError as err:
            raise UserNotificationException(f"Binary execution failed:\n{err.stderr}") from err
