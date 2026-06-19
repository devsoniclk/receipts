"""Anti-gaming detection — catches agents that cheat on verification."""

from __future__ import annotations

import fnmatch
import re
import subprocess
from pathlib import Path
from typing import Any

from receipts.probes.base import ProbeResult


def run_anti_gaming(config: dict[str, Any], cwd: Path) -> list[ProbeResult]:
    """Run all anti-gaming checks based on config.

    Args:
        config: Anti-gaming configuration dict.
        cwd: Working directory (should be a git repo).

    Returns:
        List of ProbeResult for each check.
    """
    results: list[ProbeResult] = []

    if config.get("forbid_test_edits", False):
        results.append(check_test_file_edits(cwd))

    if config.get("forbid_skipped_tests", False):
        results.append(check_skipped_tests(cwd))

    if config.get("forbid_hardcoded_outputs", False):
        results.append(check_hardcoded_outputs(cwd))

    if not results:
        # No anti-gaming checks configured — pass by default
        results.append(
            ProbeResult(
                passed=True,
                evidence="No anti-gaming checks configured",
                details={"configured": False},
            )
        )

    return results


def _run_git(args: list[str], cwd: Path) -> tuple[int, str, str]:
    """Run a git command and return (returncode, stdout, stderr)."""
    try:
        result = subprocess.run(
            ["git"] + args,
            capture_output=True,
            text=True,
            timeout=30,
            cwd=str(cwd),
        )
        return result.returncode, result.stdout, result.stderr
    except FileNotFoundError:
        return -1, "", "git not found"
    except subprocess.TimeoutExpired:
        return -1, "", "git timed out"
    except Exception as e:
        return -1, "", str(e)


def check_test_file_edits(cwd: Path) -> ProbeResult:
    """Check if any test files were modified (git diff).

    Detects:
    - Modified test files (git diff --name-only on test paths)
    - Deleted test files (git diff --diff-filter=D)
    """
    test_patterns = ["test_*.py", "*_test.py", "tests/", "test/"]

    # Get modified files
    rc, stdout, stderr = _run_git(
        ["diff", "--name-only", "HEAD"], cwd
    )

    # Also check staged changes
    rc2, stdout2, _ = _run_git(
        ["diff", "--cached", "--name-only", "HEAD"], cwd
    )

    # Also check untracked files
    rc3, stdout3, _ = _run_git(
        ["ls-files", "--others", "--exclude-standard"], cwd
    )

    all_changed = set()
    for output in [stdout, stdout2, stdout3]:
        for line in output.strip().split("\n"):
            line = line.strip()
            if line:
                all_changed.add(line)

    # Check if any changed file matches test patterns
    modified_tests = set()
    for filepath in all_changed:
        for pattern in test_patterns:
            if _matches_test_pattern(filepath, pattern):
                modified_tests.add(filepath)
                break

    # Check for deleted test files specifically
    _, del_stdout, _ = _run_git(
        ["diff", "--diff-filter=D", "--name-only", "HEAD"], cwd
    )
    deleted_tests = set()
    for line in del_stdout.strip().split("\n"):
        line = line.strip()
        if line:
            for pattern in test_patterns:
                if _matches_test_pattern(line, pattern):
                    deleted_tests.add(line)
                    break

    passed = len(modified_tests) == 0
    details: dict[str, Any] = {
        "modified_tests": sorted(modified_tests),
        "deleted_tests": sorted(deleted_tests),
    }

    if deleted_tests:
        passed = False
        evidence = f"Test files deleted: {', '.join(sorted(deleted_tests))}"
    elif modified_tests:
        evidence = f"Test files modified: {', '.join(sorted(modified_tests))}"
    else:
        evidence = "No test files modified"

    return ProbeResult(passed=passed, evidence=evidence, details=details)


def check_skipped_tests(cwd: Path) -> ProbeResult:
    """Detect skipped tests in Python test files.

    Looks for:
    - @pytest.mark.skip / @pytest.mark.skipif decorators
    - pytest.skip() calls
    - @pytest.mark.xfail(strict=False)
    - unittest.skip decorators
    """
    skip_patterns = [
        (r"@pytest\.mark\.skip", "pytest.mark.skip decorator"),
        (r"@pytest\.mark\.skipif", "pytest.mark.skipif decorator"),
        (r"pytest\.skip\(", "pytest.skip() call"),
        (r"@pytest\.mark\.xfail", "pytest.mark.xfail decorator"),
        (r"@unittest\.skip", "unittest.skip decorator"),
        (r"unittest\.skip\(", "unittest.skip() call"),
    ]

    test_files = _find_test_files(cwd)
    findings: list[dict[str, Any]] = []

    for filepath in test_files:
        try:
            content = filepath.read_text(errors="replace")
        except Exception:
            continue

        for pattern, description in skip_patterns:
            matches = list(re.finditer(pattern, content))
            if matches:
                for match in matches:
                    line_num = content[: match.start()].count("\n") + 1
                    findings.append(
                        {
                            "file": str(filepath.relative_to(cwd)),
                            "line": line_num,
                            "pattern": description,
                            "match": match.group(),
                        }
                    )

    passed = len(findings) == 0
    details: dict[str, Any] = {"findings": findings}

    if findings:
        files = set(f["file"] for f in findings)
        evidence = (
            f"Found {len(findings)} skip marker(s) in {', '.join(sorted(files))}"
        )
    else:
        evidence = "No skip markers found in test files"

    return ProbeResult(passed=passed, evidence=evidence, details=details)


def check_hardcoded_outputs(cwd: Path) -> ProbeResult:
    """Detect hard-coded output assertions in test files.

    Looks for patterns like:
    - assert value == "literal_string"
    - assert result == "expected"
    - assert output == 'hardcoded'
    """
    # Pattern: assert <expr> == <string_literal>
    hardcoded_pattern = re.compile(
        r"""assert\s+.+?\s*==\s*(['"])(?P<value>.+?)\1"""
    )

    test_files = _find_test_files(cwd)
    findings: list[dict[str, Any]] = []

    for filepath in test_files:
        try:
            content = filepath.read_text(errors="replace")
        except Exception:
            continue

        for match in hardcoded_pattern.finditer(content):
            line_num = content[: match.start()].count("\n") + 1
            line_content = content.split("\n")[line_num - 1].strip()
            findings.append(
                {
                    "file": str(filepath.relative_to(cwd)),
                    "line": line_num,
                    "content": line_content,
                    "value": match.group("value"),
                }
            )

    passed = len(findings) == 0
    details: dict[str, Any] = {"findings": findings}

    if findings:
        files = set(f["file"] for f in findings)
        evidence = (
            f"Found {len(findings)} hard-coded assertion(s) in {', '.join(sorted(files))}"
        )
    else:
        evidence = "No hard-coded output assertions found"

    return ProbeResult(passed=passed, evidence=evidence, details=details)


def _find_test_files(cwd: Path) -> list[Path]:
    """Find all Python test files in the directory."""
    test_files = []
    for pattern in ["test_*.py", "*_test.py"]:
        test_files.extend(cwd.rglob(pattern))
    return test_files


def _matches_test_pattern(filepath: str, pattern: str) -> bool:
    """Check if a filepath matches a test file pattern."""
    if pattern.endswith("/"):
        return filepath.startswith(pattern) or f"/{pattern}" in filepath
    # Use basename matching for glob patterns like test_*.py
    basename = filepath.rsplit("/", 1)[-1] if "/" in filepath else filepath
    return fnmatch.fnmatch(basename, pattern)
