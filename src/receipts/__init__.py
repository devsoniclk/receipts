"""receipts — Task-completion verification for AI agents."""

from pathlib import Path
from typing import Optional

from receipts.verdict import Verdict


def verify(spec_path: str, workdir: Optional[str] = None) -> Verdict:
    """Verify a task spec and return a Verdict.

    Args:
        spec_path: Path to YAML task spec file.
        workdir: Working directory for probe execution (default: spec file's dir).

    Returns:
        Verdict with pass/fail, probe results, anti-gaming results, and reasons.
    """
    from receipts.spec import parse_spec
    from receipts.probes import run_probe
    from receipts.antigaming import run_anti_gaming

    spec = parse_spec(spec_path)
    cwd = Path(workdir) if workdir else Path(spec_path).parent

    # Run probes
    probe_results = []
    for probe_def in spec.get("probes", []):
        result = run_probe(probe_def, cwd=cwd)
        probe_results.append(result)

    # Run anti-gaming checks
    anti_gaming_config = spec.get("anti_gaming", {})
    anti_gaming_results = run_anti_gaming(anti_gaming_config, cwd=cwd)

    # Build verdict
    passed = all(r.passed for r in probe_results) and all(
        r.passed for r in anti_gaming_results
    )

    reasons = []
    for r in probe_results:
        if not r.passed:
            reasons.append(f"Probe failed: {r.evidence}")
    for r in anti_gaming_results:
        if not r.passed:
            reasons.append(f"Anti-gaming: {r.evidence}")

    evidence = {}
    for i, r in enumerate(probe_results):
        evidence[f"probe_{i}"] = r.details
    for i, r in enumerate(anti_gaming_results):
        evidence[f"antigaming_{i}"] = r.details

    return Verdict(
        passed=passed,
        probe_results=probe_results,
        anti_gaming_results=anti_gaming_results,
        reasons=reasons,
        evidence=evidence,
    )
