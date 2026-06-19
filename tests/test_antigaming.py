"""Tests for anti-gaming detection."""

import subprocess
from pathlib import Path

import pytest

from receipts.antigaming import (
    check_hardcoded_outputs,
    check_skipped_tests,
    check_test_file_edits,
    run_anti_gaming,
)


def _init_git_repo(path: Path):
    """Initialize a git repo with an initial commit."""
    subprocess.run(["git", "init"], cwd=str(path), capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@test.com"],
        cwd=str(path),
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test"],
        cwd=str(path),
        capture_output=True,
    )
    # Create initial commit
    (path / "README.md").write_text("init")
    subprocess.run(["git", "add", "."], cwd=str(path), capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "init"], cwd=str(path), capture_output=True
    )


class TestCheckTestFileEdits:
    def test_no_edits(self, tmp_path):
        _init_git_repo(tmp_path)
        result = check_test_file_edits(tmp_path)
        assert result.passed

    def test_edited_test_file(self, tmp_path):
        _init_git_repo(tmp_path)
        test_file = tmp_path / "test_example.py"
        test_file.write_text("def test_pass(): assert True")
        result = check_test_file_edits(tmp_path)
        assert not result.passed
        assert "test_example.py" in result.evidence

    def test_edited_tests_dir(self, tmp_path):
        _init_git_repo(tmp_path)
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        (tests_dir / "test_foo.py").write_text("def test_ok(): pass")
        result = check_test_file_edits(tmp_path)
        assert not result.passed


class TestCheckSkippedTests:
    def test_no_skips(self, tmp_path):
        test_file = tmp_path / "test_clean.py"
        test_file.write_text("def test_one(): assert True\n")
        result = check_skipped_tests(tmp_path)
        assert result.passed

    def test_pytest_skip_decorator(self, tmp_path):
        test_file = tmp_path / "test_skip.py"
        test_file.write_text(
            "import pytest\n\n@pytest.mark.skip\ndef test_skip(): pass\n"
        )
        result = check_skipped_tests(tmp_path)
        assert not result.passed
        assert "skip" in result.evidence.lower()

    def test_pytest_skip_call(self, tmp_path):
        test_file = tmp_path / "test_skip.py"
        test_file.write_text(
            "import pytest\n\ndef test_skip(): pytest.skip('reason')\n"
        )
        result = check_skipped_tests(tmp_path)
        assert not result.passed


class TestCheckHardcodedOutputs:
    def test_no_hardcoded(self, tmp_path):
        test_file = tmp_path / "test_clean.py"
        test_file.write_text(
            "def test_one():\n    expected = get_expected()\n    assert result == expected\n"
        )
        result = check_hardcoded_outputs(tmp_path)
        assert result.passed

    def test_hardcoded_string(self, tmp_path):
        test_file = tmp_path / "test_hard.py"
        test_file.write_text(
            'def test_api():\n    assert response == "ok"\n'
        )
        result = check_hardcoded_outputs(tmp_path)
        assert not result.passed


class TestRunAntiGaming:
    def test_no_config(self, tmp_path):
        results = run_anti_gaming({}, tmp_path)
        assert len(results) == 1
        assert results[0].passed

    def test_with_config(self, tmp_path):
        (tmp_path / "test_clean.py").write_text("def test_ok(): assert True\n")
        config = {"forbid_skipped_tests": True}
        results = run_anti_gaming(config, tmp_path)
        assert len(results) == 1
        assert results[0].passed
