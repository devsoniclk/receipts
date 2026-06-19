"""File probe — checks file/directory existence and content."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from receipts.probes.base import Probe, ProbeResult


class FileProbe(Probe):
    """Checks file or directory existence and content.

    Config keys:
        path: File or directory path (relative to cwd).
        exists: Whether the path must exist (default: true).
        contains: Substring that must appear in file content.
        matches_regex: Regex pattern that must match file content.
        is_dir: Whether path must be a directory (default: false).
    """

    def run(self, cwd: Path) -> ProbeResult:
        rel_path = self.config.get("path")
        if not rel_path:
            return ProbeResult(
                passed=False, evidence="No path specified", details={}
            )

        target = cwd / rel_path
        must_exist = self.config.get("exists", True)
        contains = self.config.get("contains")
        matches_regex = self.config.get("matches_regex")
        is_dir = self.config.get("is_dir", False)

        details: dict[str, Any] = {"path": str(target), "rel_path": rel_path}

        # Existence check
        if must_exist and not target.exists():
            return ProbeResult(
                passed=False,
                evidence=f"Path does not exist: {rel_path}",
                details=details,
            )

        if not must_exist and target.exists():
            return ProbeResult(
                passed=False,
                evidence=f"Path should not exist but does: {rel_path}",
                details=details,
            )

        if not must_exist:
            return ProbeResult(
                passed=True,
                evidence=f"Path correctly absent: {rel_path}",
                details=details,
            )

        details["exists"] = True

        # Directory check
        if is_dir:
            if not target.is_dir():
                return ProbeResult(
                    passed=False,
                    evidence=f"Path exists but is not a directory: {rel_path}",
                    details=details,
                )
            return ProbeResult(
                passed=True,
                evidence=f"Directory exists: {rel_path}",
                details=details,
            )

        # Content checks (only for files)
        if target.is_file():
            content = target.read_text(errors="replace")
            details["content_length"] = len(content)

            if contains is not None:
                if contains not in content:
                    return ProbeResult(
                        passed=False,
                        evidence=f"File {rel_path} does not contain '{contains}'",
                        details=details,
                    )

            if matches_regex is not None:
                if not re.search(matches_regex, content):
                    return ProbeResult(
                        passed=False,
                        evidence=f"File {rel_path} does not match regex '{matches_regex}'",
                        details=details,
                    )

        return ProbeResult(
            passed=True,
            evidence=f"File checks passed: {rel_path}",
            details=details,
        )
