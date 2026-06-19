"""Tests for spec parser."""

import tempfile
from pathlib import Path

import pytest
import yaml

from receipts.spec import parse_spec


def test_parse_valid_spec(tmp_path):
    spec = {
        "goal": "Test goal",
        "probes": [
            {"shell": {"cmd": "echo hello", "exit_code": 0}},
            {"file": {"path": "README.md", "exists": True}},
        ],
    }
    spec_file = tmp_path / "task.yaml"
    spec_file.write_text(yaml.dump(spec))

    result = parse_spec(str(spec_file))

    assert result["goal"] == "Test goal"
    assert len(result["probes"]) == 2
    assert result["probes"][0]["type"] == "shell"
    assert result["probes"][0]["cmd"] == "echo hello"
    assert result["probes"][1]["type"] == "file"
    assert result["probes"][1]["path"] == "README.md"
    assert result["anti_gaming"] == {}


def test_parse_missing_file():
    with pytest.raises(FileNotFoundError):
        parse_spec("/nonexistent/task.yaml")


def test_parse_missing_goal(tmp_path):
    spec_file = tmp_path / "task.yaml"
    spec_file.write_text(yaml.dump({"probes": []}))

    with pytest.raises(ValueError, match="goal"):
        parse_spec(str(spec_file))


def test_parse_missing_probes(tmp_path):
    spec_file = tmp_path / "task.yaml"
    spec_file.write_text(yaml.dump({"goal": "test"}))

    with pytest.raises(ValueError, match="probes"):
        parse_spec(str(spec_file))


def test_parse_anti_gaming_config(tmp_path):
    spec = {
        "goal": "Test",
        "probes": [{"shell": {"cmd": "echo ok"}}],
        "anti_gaming": {"forbid_test_edits": True},
    }
    spec_file = tmp_path / "task.yaml"
    spec_file.write_text(yaml.dump(spec))

    result = parse_spec(str(spec_file))
    assert result["anti_gaming"]["forbid_test_edits"] is True
