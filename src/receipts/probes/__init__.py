"""Probe runner and registry."""

from pathlib import Path
from typing import Any

from receipts.probes.base import Probe, ProbeResult


def run_probe(probe_def: dict[str, Any], cwd: Path) -> ProbeResult:
    """Run a single probe from its definition.

    Args:
        probe_def: Probe definition dict with 'type' key and probe-specific config.
        cwd: Working directory for probe execution.

    Returns:
        ProbeResult indicating pass/fail with evidence.
    """
    probe_type = probe_def.get("type", "")
    probe_map = {
        "shell": _run_shell,
        "http": _run_http,
        "file": _run_file,
        "tests": _run_tests,
    }

    runner = probe_map.get(probe_type)
    if runner is None:
        return ProbeResult(
            passed=False,
            evidence=f"Unknown probe type: {probe_type}",
            details={"type": probe_type},
        )

    return runner(probe_def, cwd)


def _run_shell(config: dict, cwd: Path) -> ProbeResult:
    from receipts.probes.shell import ShellProbe
    return ShellProbe(config).run(cwd)


def _run_http(config: dict, cwd: Path) -> ProbeResult:
    from receipts.probes.http import HttpProbe
    return HttpProbe(config).run(cwd)


def _run_file(config: dict, cwd: Path) -> ProbeResult:
    from receipts.probes.file import FileProbe
    return FileProbe(config).run(cwd)


def _run_tests(config: dict, cwd: Path) -> ProbeResult:
    from receipts.probes.tests import TestProbe
    return TestProbe(config).run(cwd)
