import tarfile

import pytest
from py_app_dev.core.exceptions import UserNotificationException

from gcc_portable.tester import GccTester


def _create_fake_archive(archive_path, gcc_dir_name="gcc-15.2.0"):
    """Create a minimal fake GCC archive for testing."""
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    import tempfile
    from pathlib import Path

    with tempfile.TemporaryDirectory() as temp_dir:
        gcc_dir = Path(temp_dir) / gcc_dir_name
        bin_dir = gcc_dir / "bin"
        bin_dir.mkdir(parents=True)
        (bin_dir / "gcc").write_text("#!/bin/sh\necho 'fake gcc'\n")
        (bin_dir / "gcc").chmod(0o755)
        with tarfile.open(archive_path, "w:gz") as tar:
            tar.add(gcc_dir, arcname=gcc_dir_name)


def test_extract_archive(tmp_path):
    archive_path = tmp_path / "gcc-15.2.0-darwin-arm64.tar.gz"
    _create_fake_archive(archive_path)
    tester = GccTester(archive_path=archive_path, output_dir=tmp_path / "out")
    (tmp_path / "out").mkdir()
    gcc_dir = tester._extract_archive()
    assert gcc_dir.exists()
    assert (gcc_dir / "bin" / "gcc").exists()


def test_find_gcc_finds_gcc_binary(tmp_path):
    gcc_dir = tmp_path / "gcc-15.2.0"
    bin_dir = gcc_dir / "bin"
    bin_dir.mkdir(parents=True)
    (bin_dir / "gcc").write_text("fake")
    tester = GccTester(archive_path=tmp_path / "archive.tar.gz", output_dir=tmp_path)
    assert tester._find_gcc(gcc_dir).name == "gcc"


def test_find_gcc_finds_prefixed_binary(tmp_path):
    gcc_dir = tmp_path / "gcc-15.2.0"
    bin_dir = gcc_dir / "bin"
    bin_dir.mkdir(parents=True)
    (bin_dir / "arm64-apple-darwin20.0.0-gcc").write_text("fake")
    tester = GccTester(archive_path=tmp_path / "archive.tar.gz", output_dir=tmp_path)
    result = tester._find_gcc(gcc_dir)
    assert "darwin" in result.name
    assert result.name.endswith("-gcc")


def test_find_gcc_raises_when_not_found(tmp_path):
    gcc_dir = tmp_path / "gcc-15.2.0"
    bin_dir = gcc_dir / "bin"
    bin_dir.mkdir(parents=True)
    (bin_dir / "some-other-tool").write_text("fake")
    tester = GccTester(archive_path=tmp_path / "archive.tar.gz", output_dir=tmp_path)
    with pytest.raises(UserNotificationException, match="No gcc binary found"):
        tester._find_gcc(gcc_dir)


def test_run_raises_when_archive_missing(tmp_path):
    tester = GccTester(archive_path=tmp_path / "nonexistent.tar.gz", output_dir=tmp_path)
    with pytest.raises(UserNotificationException, match="Archive not found"):
        tester.run()
