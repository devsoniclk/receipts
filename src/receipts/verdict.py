"""Verdict dataclass and report generation."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from receipts.probes.base import ProbeResult


@dataclass
class Verdict:
    """Final verdict on whether a task was actually completed."""

    passed: bool
    probe_results: list[ProbeResult] = field(default_factory=list)
    anti_gaming_results: list[ProbeResult] = field(default_factory=list)
    reasons: list[str] = field(default_factory=list)
    evidence: dict[str, Any] = field(default_factory=dict)

    def to_report(self) -> str:
        """Generate a human-readable report.

        Returns:
            Multi-line string with full verification report.
        """
        lines: list[str] = []

        status = "✅ PASS" if self.passed else "❌ FAIL"
        lines.append(f"Verification: {status}")
        lines.append("")

        # Probe results
        if self.probe_results:
            lines.append("Probes:")
            for i, r in enumerate(self.probe_results):
                mark = "✓" if r.passed else "✗"
                lines.append(f"  [{mark}] {r.evidence}")
            lines.append("")

        # Anti-gaming results
        if self.anti_gaming_results:
            lines.append("Anti-Gaming:")
            for i, r in enumerate(self.anti_gaming_results):
                mark = "✓" if r.passed else "✗"
                lines.append(f"  [{mark}] {r.evidence}")
            lines.append("")

        # Reasons for failure
        if self.reasons:
            lines.append("Failure Reasons:")
            for reason in self.reasons:
                lines.append(f"  - {reason}")

        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        """Convert to a JSON-serializable dict.

        Returns:
            Dict representation of the verdict.
        """
        return {
            "passed": self.passed,
            "reasons": self.reasons,
            "probe_results": [
                {
                    "passed": r.passed,
                    "evidence": r.evidence,
                    "details": r.details,
                }
                for r in self.probe_results
            ],
            "anti_gaming_results": [
                {
                    "passed": r.passed,
                    "evidence": r.evidence,
                    "details": r.details,
                }
                for r in self.anti_gaming_results
            ],
            "evidence": self.evidence,
        }

    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string.

        Args:
            indent: JSON indentation level.

        Returns:
            JSON string representation.
        """
        return json.dumps(self.to_dict(), indent=indent, default=str)
