# receipts

Agents lie about task completion. Not maliciously — they just optimize for looking done. They'll skip a test, weaken an assertion, hard-code an expected value, or delete the failing test file entirely. Then they report success.

receipts is an independent verification layer that checks whether the work was actually done. It runs probes against the real system — HTTP endpoints, file contents, shell commands, test suites — and separately checks whether the agent gamed its own tests.

## Quickstart

```bash
pip install -e .
```

Write a spec describing what "done" looks like:

```yaml
# task.yaml
goal: "Add a /health endpoint returning 200 + {status: ok}"

probes:
  - http:
      url: "http://localhost:8000/health"
      expect_status: 200
      expect_json:
        status: "ok"
  - tests:
      cmd: "pytest tests/test_health.py"
      must_pass: true

anti_gaming:
  forbid_test_edits: true
  forbid_skipped_tests: true
```

Then run it:

```bash
receipts verify task.yaml
```

## What probes are available

- `shell` — command exits with expected code
- `http` — URL returns expected status and/or JSON values
- `file` — file exists, contains expected content
- `tests` — test suite passes with no skipped or deleted tests

## The anti-gaming checks

This is the part that matters most. receipts catches agents that game their own verification:

1. **Test file tampering** — diffs test paths against git HEAD. If the agent touched the tests, that's a flag.
2. **Skipped tests** — scans for `@pytest.mark.skip`, `xfail`, `skip()` calls that weren't there before.
3. **Hard-coded outputs** — looks for `assert value == "some_literal"` patterns where the expected value is a string constant rather than computed from the actual system state.
4. **Weakened assertions** — catches things like `assert status == 200` becoming `assert status < 500`.
5. **Deleted test files** — checks if test files were removed entirely.

## Python API

```python
from receipts import verify

verdict = verify("task.yaml")
if not verdict.passed:
    print(verdict.reasons)
    # ["SKIPPED_TEST: tests/test_health.py::test_response_schema"]
```

## Full spec format

```yaml
goal: "Human-readable description"

probes:
  - shell:
      cmd: "make build"
      exit_code: 0
      timeout: 120
  - http:
      url: "http://localhost:8000/api/data"
      expect_status: 200
      expect_json:
        count: 10
  - file:
      path: "config.json"
      exists: true
      contains: '"version": "2.0"'
  - tests:
      cmd: "pytest tests/"
      must_pass: true

anti_gaming:
  forbid_test_edits: true
  forbid_skipped_tests: true
  forbid_hardcoded_outputs: true
```

## License

MIT
