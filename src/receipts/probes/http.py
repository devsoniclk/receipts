"""HTTP probe — makes an HTTP request and validates the response."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from receipts.probes.base import Probe, ProbeResult

try:
    import httpx
except ImportError:
    httpx = None  # type: ignore[assignment]


class HttpProbe(Probe):
    """Makes an HTTP request and validates status code and JSON response.

    Config keys:
        url: URL to request.
        method: HTTP method (default: GET).
        expect_status: Expected HTTP status code.
        expect_json: Dict of expected key-value pairs in JSON response.
        json_path: JSONPath-like dot-notation path to check in response.
        json_path_value: Expected value at json_path.
        timeout: Request timeout in seconds (default: 10).
    """

    def run(self, cwd: Path) -> ProbeResult:
        if httpx is None:
            return ProbeResult(
                passed=False,
                evidence="httpx is not installed",
                details={"error": "missing httpx dependency"},
            )

        url = self.config.get("url")
        if not url:
            return ProbeResult(passed=False, evidence="No URL specified", details={})

        method = self.config.get("method", "GET").upper()
        expect_status = self.config.get("expect_status")
        expect_json = self.config.get("expect_json", {})
        timeout = self.config.get("timeout", 10)

        try:
            response = httpx.request(method, url, timeout=timeout)
        except httpx.TimeoutException:
            return ProbeResult(
                passed=False,
                evidence=f"{method} {url} timed out after {timeout}s",
                details={"url": url, "timeout": timeout},
            )
        except httpx.RequestError as e:
            return ProbeResult(
                passed=False,
                evidence=f"{method} {url} request failed: {e}",
                details={"url": url, "error": str(e)},
            )

        passed = True
        reasons = []
        details: dict[str, Any] = {
            "url": url,
            "status_code": response.status_code,
        }

        # Check status code
        if expect_status is not None:
            if response.status_code != expect_status:
                passed = False
                reasons.append(
                    f"status {response.status_code} != expected {expect_status}"
                )
            details["expected_status"] = expect_status

        # Check JSON response
        if expect_json or "json_path" in self.config:
            try:
                body = response.json()
                details["body"] = body
            except (json.JSONDecodeError, ValueError):
                passed = False
                reasons.append("Response is not valid JSON")
                body = None

            if body is not None and expect_json:
                for key, expected_val in expect_json.items():
                    actual_val = _dig(body, key)
                    if actual_val != expected_val:
                        passed = False
                        reasons.append(
                            f"json.{key}: {actual_val!r} != expected {expected_val!r}"
                        )

            # JSONPath-style check
            json_path = self.config.get("json_path")
            json_path_value = self.config.get("json_path_value")
            if body is not None and json_path is not None:
                actual = _dig(body, json_path)
                if json_path_value is not None and actual != json_path_value:
                    passed = False
                    reasons.append(
                        f"json_path '{json_path}': {actual!r} != expected {json_path_value!r}"
                    )

        evidence = f"{method} {url} → {response.status_code}"
        if reasons:
            evidence += " — " + "; ".join(reasons)

        return ProbeResult(passed=passed, evidence=evidence, details=details)


def _dig(obj: Any, path: str) -> Any:
    """Traverse a nested dict/list by dot-separated path."""
    current = obj
    for part in path.split("."):
        if isinstance(current, dict):
            current = current.get(part)
        elif isinstance(current, list):
            try:
                current = current[int(part)]
            except (ValueError, IndexError):
                return None
        else:
            return None
    return current
