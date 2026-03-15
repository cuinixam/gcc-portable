"""CLI entry point for gcc_portable."""

import sys
from pathlib import Path
from typing import Annotated

import typer
from py_app_dev.core.exceptions import UserNotificationException
from py_app_dev.core.logging import logger, setup_logger, time_it

from gcc_portable import __version__
from gcc_portable.micromamba import find_micromamba
from gcc_portable.packager import GccPackager, PackageConfig
from gcc_portable.tester import GccTester

package_name = "gcc_portable"


app = typer.Typer(
    name=package_name,
    help="Package GCC from conda-forge into a portable macOS archive.",
    no_args_is_help=True,
    add_completion=False,
)


@app.callback(invoke_without_command=True)
def version(
    version: Annotated[bool, typer.Option("--version", "-v", is_eager=True, help="Show version and exit.")] = False,
) -> None:
    if version:
        typer.echo(f"{package_name} {__version__}")
        raise typer.Exit()


@app.command(help="Package GCC into a portable macOS archive.")
@time_it("package")
def package(
    gcc_version: Annotated[str, typer.Argument(help="GCC version to package (e.g. '15.2.0').")] = "15.2.0",
    output_dir: Annotated[Path, typer.Option("--output", "-o", help="Output directory for the archive.")] = Path("build/dist"),
    build_number: Annotated[str, typer.Option("--build-number", "-b", help="Build number for the archive name.")] = "0",
) -> None:
    micromamba_exe = find_micromamba()
    config = PackageConfig(gcc_version=gcc_version, output_dir=output_dir, build_number=build_number)
    packager = GccPackager(config, micromamba_exe)
    archive_path = packager.package()
    logger.info(f"Archive created: {archive_path}")


@app.command(help="Test the GCC portable archive by compiling a hello world program.")
@time_it("test")
def test(
    archive_dir: Annotated[Path, typer.Argument(help="Directory containing the GCC portable archive (.tar.gz).")],
    output_dir: Annotated[Path, typer.Option("--output", "-o", help="Output directory for test files.")] = Path("build/dist"),
) -> None:
    archives = list(archive_dir.glob("gcc-*.tar.gz"))
    if not archives:
        raise UserNotificationException(f"No gcc-*.tar.gz archive found in {archive_dir}")
    tester = GccTester(archive_path=archives[0], output_dir=output_dir)
    tester.run()


def main() -> int:
    try:
        setup_logger()
        app()
        return 0
    except UserNotificationException as e:
        logger.error(f"{e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
