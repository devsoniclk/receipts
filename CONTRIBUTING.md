# Contributing to receipts

Thank you for your interest in contributing!

## Getting Started

1. Clone the repository
2. Create a virtual environment: `python -m venv .venv && source .venv/bin/activate`
3. Install in dev mode: `pip install -e ".[dev]"` or `pip install -e .`
4. Run tests: `pytest`

## Development Workflow

1. Fork the repo and create a feature branch
2. Write your code and add tests
3. Ensure all tests pass: `pytest`
4. Submit a pull request

## Adding a New Probe

1. Create `src/receipts/probes/yourprobe.py`
2. Subclass `Probe` from `probes/base.py`
3. Implement `run(context) -> ProbeResult`
4. Register it in `probes/__init__.py`
5. Add tests in `tests/test_probes.py`

## Code Style

- Type hints on all public functions
- Docstrings on classes and public methods
- Keep probes independent — no cross-probe state

## Reporting Issues

Open a GitHub issue with:
- What you expected
- What happened instead
- Steps to reproduce
