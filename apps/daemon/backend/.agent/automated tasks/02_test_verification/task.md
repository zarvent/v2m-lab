---
name: Verify Test Suite Integrity
description: Execute full regression testing with coverage analysis to ensure system stability.
frequency: On Change / Daily
tags: [test, pytest, coverage, regression]
---

# 🧪 Verify Test Suite Integrity

This task executes the automated test suite to validate logic correctness and ensure no regressions were introduced.

## 📋 Context

- **Framework**: `pytest`
- **Coverage**: `pytest-cov` targeting the `src` directory.
- **Async**: `pytest-asyncio` is configured for async tests.

## 🚀 Execution Steps

### 1. Run Complete Test Suite

Execute all tests with verbose output and coverage calculation.

```bash
uv run pytest -v --cov=src --cov-report=term-missing --cov-report=html
```

### 2. Analyze Coverage

Check the terminal output for the coverage percentage.

- **Target**: > 80% coverage.
- **Critical**: Ensure `src/v2m/orchestrator.py` and `src/v2m/transcription.py` are covered.

### 3. View HTML Report (Optional)

If running locally, you can view the detailed line-by-line coverage:

```bash
# Optional: Open in browser
# xdg-open htmlcov/index.html
```

## 🔍 Validation Criteria

- All tests must **PASS**.
- No "warnings" that indicate deprecated API usage (optional but recommended).

## ⚠️ Troubleshooting

- **"Module not found"**: Ensure you are running with `uv run` to use the virtualenv.
- **Asyncio Loop Error**: Common in async tests. Ensure `pytest-asyncio` is installed and `asyncio_mode = "auto"` is in `pyproject.toml`.
