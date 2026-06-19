"""Tests for verdict and report generation."""

from receipts.probes.base import ProbeResult
from receipts.verdict import Verdict


class TestVerdict:
    def test_pass_verdict(self):
        v = Verdict(
            passed=True,
            probe_results=[ProbeResult(passed=True, evidence="ok")],
            anti_gaming_results=[ProbeResult(passed=True, evidence="clean")],
        )
        assert v.passed
        assert "PASS" in v.to_report()

    def test_fail_verdict(self):
        v = Verdict(
            passed=False,
            probe_results=[ProbeResult(passed=False, evidence="broken")],
            reasons=["Probe failed: broken"],
        )
        assert not v.passed
        assert "FAIL" in v.to_report()
        assert "broken" in v.to_report()

    def test_to_dict(self):
        v = Verdict(
            passed=True,
            probe_results=[ProbeResult(passed=True, evidence="ok", details={"x": 1})],
        )
        d = v.to_dict()
        assert d["passed"] is True
        assert d["probe_results"][0]["evidence"] == "ok"
        assert d["probe_results"][0]["details"] == {"x": 1}

    def test_to_json(self):
        v = Verdict(passed=True)
        j = v.to_json()
        assert '"passed": true' in j
        assert isinstance(j, str)

    def test_empty_verdict(self):
        v = Verdict(passed=True)
        report = v.to_report()
        assert "PASS" in report

    def test_verdict_with_evidence(self):
        v = Verdict(
            passed=False,
            evidence={"probe_0": {"cmd": "test", "exit_code": 1}},
            reasons=["Command failed"],
        )
        d = v.to_dict()
        assert "probe_0" in d["evidence"]
