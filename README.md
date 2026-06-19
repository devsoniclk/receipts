# receipts

> Your agent said ✅. It lied. **receipts** checks.

AI agents frequently claim tasks are complete when they aren't. A [2025 UC Berkeley study](https://arxiv.org/abs/2406.04802) found that LLM agents game benchmarks by optimizing for surface-level metrics rather than genuine task completion — skipping tests, weakening assertions, and hard-coding expected outputs.

**receipts** is an independent verification layer that checks whether an agent *actually* did what it claims. It catches agents that lie about completion or game their own tests.

## Quickstart

### Install

```bash
pip install -e .
```

### Write a task spec

Create `task.yaml`:

```yaml
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

### Verify

```bash
receipts verify task.yaml
```

Machine-readable output:

```bash
receipts verify task.yaml --json
```

### Python API

```python
from receipts import verify

verdict = verify("task.yaml")
if not verdict.passed:
    print(verdict.reasons)
```

## Probe Types

| Probe | What it checks |
|-------|---------------|
| `shell` | Command exits with expected code |
| `http` | URL returns expected status / JSON values |
| `file` | File exists, contains expected content |
| `tests` | Test suite passes, no skips detected |

## Anti-Gaming Checks

**receipts** catches agents that game their own verification:

1. **Test file tampering** — detects if the agent modified test files (`git diff` on test paths)
2. **Skipped tests** — detects `@pytest.mark.skip`, `xfail`, `skip()` calls
3. **Hard-coded outputs** — detects `assert value == "literal"` patterns where the expected value is a string literal (not computed)
4. **Weakened assertions** — detects assertions that were relaxed (e.g., `assert status == 200` → `assert status < 400`)
5. **Deleted tests** — detects if test files were removed entirely

## YAML Task Spec Format

```yaml
goal: "Human-readable description of what should be done"

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
