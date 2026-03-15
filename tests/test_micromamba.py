from unittest.mock import patch

import pytest
from py_app_dev.core.exceptions import UserNotificationException

from gcc_portable.micromamba import create_environment, find_micromamba


def test_find_micromamba_returns_path_when_found():
    with patch("gcc_portable.micromamba.shutil.which", return_value="/usr/local/bin/micromamba"):
        assert find_micromamba() == "/usr/local/bin/micromamba"


def test_find_micromamba_raises_when_not_found():
    with patch("gcc_portable.micromamba.shutil.which", return_value=None):
        with pytest.raises(UserNotificationException, match="micromamba not found"):
            find_micromamba()


def test_create_environment_calls_subprocess(tmp_path):
    env_path = tmp_path / "test_env"
    with patch("gcc_portable.micromamba.subprocess.run") as mock_run:
        create_environment(env_path, ["gcc=14"], "conda-forge", "/usr/local/bin/micromamba")
        mock_run.assert_called_once_with(
            ["/usr/local/bin/micromamba", "create", "-p", str(env_path), "-c", "conda-forge", "-y", "gcc=14"],
            check=True,
            capture_output=True,
            text=True,
        )


def test_create_environment_raises_on_failure(tmp_path):
    env_path = tmp_path / "test_env"
    with patch("gcc_portable.micromamba.subprocess.run", side_effect=FileNotFoundError):
        with pytest.raises(UserNotificationException, match="Command not found"):
            create_environment(env_path, ["gcc=14"], "conda-forge", "micromamba")
