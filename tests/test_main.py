from typer.testing import CliRunner

from gcc_portable.main import app

runner = CliRunner()


def test_help():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0


def test_version():
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "gcc_portable" in result.stdout


def test_package_help():
    result = runner.invoke(app, ["package", "--help"])
    assert result.exit_code == 0
    assert "GCC version" in result.stdout


def test_test_help():
    result = runner.invoke(app, ["test", "--help"])
    assert result.exit_code == 0
    assert "archive" in result.stdout.lower()
