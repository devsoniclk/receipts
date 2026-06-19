"""Abstract base probe and ProbeResult dataclass."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ProbeResult:
    """Result from running a probe."""

    passed: bool
    evidence: str
    details: dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        status = "PASS" if self.passed else "FAIL"
        return f"[{status}] {self.evidence}"


class Probe(ABC):
    """Abstract base class for probes."""

    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config

    @abstractmethod
    def run(self, cwd: Path) -> ProbeResult:
        """Execute the probe and return a result.

        Args:
            cwd: Working directory for execution.

        Returns:
            ProbeResult with pass/fail status and evidence.
        """
        ...
