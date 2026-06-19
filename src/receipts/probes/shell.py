"""Shell command probe — runs a command and checks exit code."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from receipts.probes.base import Probe, ProbeResult


class ShellProbe(Probe):
    """Runs a shell command and checks the exit code.

    Config keys:
        cmd: Shell command string to execute.
        exit_code: Expected exit code (default: 0).
        timeout: Timeout in seconds (default: 60).
        working_dir: Override working directory (relative to cwd).
    """

    def run(self, cwd: Path) -> ProbeResult:
        cmd = self.config.get("cmd")
        if not cmd:
            return ProbeResult(passed=False, evidence="No command specified", details={})

        expected_code = self.config.get("exit_code", 0)
        timeout = self.config.get("timeout", 60)
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

            passed = result.returncode == expected_code
            evidence = (
                f"Command '{cmd}' exited with {result.returncode} "
                f"(expected {expected_code})"
            )
            if not passed and result.stderr:
                evidence += f"\nstderr: {result.stderr[:500]}"

            return ProbeResult(
                passed=passed,
                evidence=evidence,
                details={
                    "cmd": cmd,
                    "exit_code": result.returncode,
                    "expected_exit_code": expected_code,
                    "stdout": result.stdout[:2000],
                    "stderr": result.stderr[:2000],
                },
            )

        except subprocess.TimeoutExpired:
            return ProbeResult(
                passed=False,
                evidence=f"Command '{cmd}' timed out after {timeout}s",
                details={"cmd": cmd, "timeout": timeout},
            )
        except Exception as e:
            return ProbeResult(
                passed=False,
                evidence=f"Command '{cmd}' raised exception: {e}",
                details={"cmd": cmd, "error": str(e)},
            )
