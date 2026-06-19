"""Test suite runner probe — runs a test command and parses output."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import Any

from receipts.probes.base import Probe, ProbeResult


class TestProbe(Probe):
    """Runs a test suite command and checks for pass/fail.

    Config keys:
        cmd: Test command to run (e.g., 'pytest tests/').
        must_pass: Whether all tests must pass (default: true).
        timeout: Timeout in seconds (default: 120).
        working_dir: Override working directory (relative to cwd).
    """

    # Patterns that indicate skipped tests
    SKIP_PATTERNS = [
        r"(\d+) skipped",
        r"@pytest\.mark\.skip",
        r"xfail",
        r"SKIP",
    ]

    def run(self, cwd: Path) -> ProbeResult:
        cmd = self.config.get("cmd")
        if not cmd:
            return ProbeResult(
                passed=False, evidence="No test command specified", details={}
            )

        must_pass = self.config.get("must_pass", True)
        timeout = self.config.get("timeout", 120)
        work_dir = cwd
        if "working_dir" in self.config:
            work_dir = cwd / self.config["working_dir"]

        try:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=str(work_dir),
            )
        except subprocess.TimeoutExpired:
            return ProbeResult(
                passed=False,
                evidence=f"Test command '{cmd}' timed out after {timeout}s",
                details={"cmd": cmd, "timeout": timeout},
            )
        except Exception as e:
            return ProbeResult(
                passed=False,
                evidence=f"Test command '{cmd}' raised exception: {e}",
                details={"cmd": cmd, "error": str(e)},
            )

        output = result.stdout + "\n" + result.stderr
        details: dict[str, Any] = {
            "cmd": cmd,
            "exit_code": result.returncode,
            "output": output[:5000],
        }

        # Parse test results
        test_info = self._parse_output(output)
        details.update(test_info)

        passed = True
        reasons = []

        if must_pass and result.returncode != 0:
            passed = False
            reasons.append(f"exit code {result.returncode}")

        if test_info.get("failures", 0) > 0:
            passed = False
            reasons.append(f"{test_info['failures']} test(s) failed")

        if test_info.get("errors", 0) > 0:
            passed = False
            reasons.append(f"{test_info['errors']} error(s)")

        if test_info.get("skipped", 0) > 0:
            details["skipped_warning"] = True

        evidence = f"Tests ({cmd}): {test_info.get('passed', '?')} passed"
        if test_info.get("failures"):
            evidence += f", {test_info['failures']} failed"
        if test_info.get("skipped"):
            evidence += f", {test_info['skipped']} skipped"
        if reasons:
            evidence += " — " + "; ".join(reasons)

        return ProbeResult(passed=passed, evidence=evidence, details=details)

    def _parse_output(self, output: str) -> dict[str, Any]:
        """Parse pytest/unittest output for test counts."""
        info: dict[str, Any] = {}

        # pytest summary line: "X passed, Y failed, Z skipped"
        summary_match = re.search(
            r"(\d+) passed", output
        )
        if summary_match:
            info["passed"] = int(summary_match.group(1))

        fail_match = re.search(r"(\d+) failed", output)
        if fail_match:
            info["failures"] = int(fail_match.group(1))
        else:
            info["failures"] = 0

        skip_match = re.search(r"(\d+) skipped", output)
        if skip_match:
            info["skipped"] = int(skip_match.group(1))
        else:
            info["skipped"] = 0

        error_match = re.search(r"(\d+) error", output)
        if error_match:
            info["errors"] = int(error_match.group(1))
        else:
            info["errors"] = 0

        # unittest style: "Ran X tests ... OK" or "FAILED (failures=Y)"
        if not info.get("passed"):
            ran_match = re.search(r"Ran (\d+) test", output)
            if ran_match:
                total = int(ran_match.group(1))
                info["passed"] = total - info["failures"] - info["errors"]

        return info
