"""Tests for probes."""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from receipts.probes.base import ProbeResult
from receipts.probes.shell import ShellProbe
from receipts.probes.file import FileProbe
from receipts.probes.tests import TestProbe


class TestProbeResult:
    def test_str_pass(self):
        r = ProbeResult(passed=True, evidence="all good")
        assert "[PASS]" in str(r)

    def test_str_fail(self):
        r = ProbeResult(passed=False, evidence="broken")
        assert "[FAIL]" in str(r)


class TestShellProbe:
    def test_success(self, tmp_path):
        probe = ShellProbe({"cmd": "echo hello", "exit_code": 0})
        result = probe.run(tmp_path)
        assert result.passed
        assert "hello" in result.details["stdout"]

    def test_wrong_exit_code(self, tmp_path):
        probe = ShellProbe({"cmd": "exit 1", "exit_code": 0})
        result = probe.run(tmp_path)
        assert not result.passed
        assert "1" in result.evidence

    def test_no_command(self, tmp_path):
        probe = ShellProbe({})
        result = probe.run(tmp_path)
        assert not result.passed

    def test_timeout(self, tmp_path):
        probe = ShellProbe({"cmd": "sleep 10", "timeout": 1})
        result = probe.run(tmp_path)
        assert not result.passed
        assert "timed out" in result.evidence


class TestFileProbe:
    def test_file_exists(self, tmp_path):
        (tmp_path / "test.txt").write_text("hello")
        probe = FileProbe({"path": "test.txt", "exists": True})
        result = probe.run(tmp_path)
        assert result.passed

    def test_file_not_exists(self, tmp_path):
        probe = FileProbe({"path": "missing.txt", "exists": True})
        result = probe.run(tmp_path)
        assert not result.passed

    def test_file_should_not_exist(self, tmp_path):
        probe = FileProbe({"path": "missing.txt", "exists": False})
        result = probe.run(tmp_path)
        assert result.passed

    def test_contains(self, tmp_path):
        (tmp_path / "f.txt").write_text("hello world")
        probe = FileProbe({"path": "f.txt", "contains": "world"})
        result = probe.run(tmp_path)
        assert result.passed

    def test_contains_fail(self, tmp_path):
        (tmp_path / "f.txt").write_text("hello world")
        probe = FileProbe({"path": "f.txt", "contains": "xyz"})
        result = probe.run(tmp_path)
        assert not result.passed

    def test_matches_regex(self, tmp_path):
        (tmp_path / "f.txt").write_text("version: 1.2.3")
        probe = FileProbe({"path": "f.txt", "matches_regex": r"version: \d+\.\d+\.\d+"})
        result = probe.run(tmp_path)
        assert result.passed

    def test_is_dir(self, tmp_path):
        (tmp_path / "mydir").mkdir()
        probe = FileProbe({"path": "mydir", "is_dir": True})
        result = probe.run(tmp_path)
        assert result.passed

    def test_no_path(self, tmp_path):
        probe = FileProbe({})
        result = probe.run(tmp_path)
        assert not result.passed


class TestTestProbe:
    def test_parse_pytest_output(self):
        probe = TestProbe({"cmd": "echo"})
        info = probe._parse_output("10 passed, 2 failed, 1 skipped in 3.5s")
        assert info["passed"] == 10
        assert info["failures"] == 2
        assert info["skipped"] == 1

    def test_parse_unittest_output(self):
        probe = TestProbe({"cmd": "echo"})
        info = probe._parse_output("Ran 5 tests in 0.1s\n\nOK")
        assert info["passed"] == 5

    def test_no_command(self, tmp_path):
        probe = TestProbe({})
        result = probe.run(tmp_path)
        assert not result.passed
