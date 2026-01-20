# Test Suite

This directory contains all automated project tests organized by type.

## Structure

- `unit/` - Unit tests that verify isolated components (mocking dependencies)
- `integration/` - Integration tests that verify interaction between real components

## Execution

To run all tests, use `pytest` from the project root:

```bash
# run all tests
pytest

# run only unit tests
pytest tests/unit

# run with coverage
pytest --cov=src/v2m
```

## Technologies

We use `pytest` as the main framework, `pytest-asyncio` for async tests, and `pytest-mock` for creating test doubles.
