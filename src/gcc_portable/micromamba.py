"""Thin wrapper around micromamba CLI subprocess calls."""

import shutil
import subprocess
from pathlib import Path

from py_app_dev.core.exceptions import UserNotificationException
from py_app_dev.core.logging import logger


def find_micromamba() -> str:
    """Find micromamba executable in PATH."""
    exe = shutil.which("micromamba")
    if not exe:
        raise UserNotificationException("micromamba not found in PATH. Install it via poks or https://mamba.readthedocs.io/en/latest/installation/micromamba-installation.html")
    return exe


def create_environment(env_path: Path, packages: list[str], channel: str, micromamba_exe: str) -> None:
    """Create a new micromamba environment with the specified packages."""
    args = [micromamba_exe, "create", "-p", str(env_path), "-c", channel, "-y", *packages]
    logger.info(f"Creating environment at {env_path} with packages: {packages}")
    _run_command(args)


def remove_environment(env_path: Path, micromamba_exe: str) -> None:
    """Remove a micromamba environment. Best-effort, logs warning on failure."""
    args = [micromamba_exe, "env", "remove", "-p", str(env_path), "-y"]
    try:
        _run_command(args)
    except UserNotificationException:
        logger.warning(f"Failed to remove environment at {env_path}, manual cleanup may be needed")


def _run_command(args: list[str]) -> subprocess.CompletedProcess[str]:
    """Run a micromamba command and return the result."""
    logger.debug(f"Running: {' '.join(args)}")
    try:
        return subprocess.run(args, check=True, capture_output=True, text=True)
    except FileNotFoundError as err:
        raise UserNotificationException(f"Command not found: {args[0]}") from err
    except subprocess.CalledProcessError as err:
        raise UserNotificationException(f"Command failed: {' '.join(args)}\n{err.stderr}") from err
