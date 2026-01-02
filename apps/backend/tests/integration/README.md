# INTEGRATION TESTS

### What is this folder?

This folder is for **integration tests**. Unlike unit tests, these verify how multiple components interact with each other or with simulated external systems.

### What is it for?

Its purpose is to detect errors in the "seams" between modules, such as:

- Communication issues between layers (e.g., application -> infrastructure).
- Data flow errors between services.
- Contract validation with external dependencies (using fakes or containers).

### Current state

This folder may currently be empty or in early development, as the main focus has been on unit coverage and manual system testing (see `scripts/verify_daemon.py`).

### How to contribute

When adding integration tests:

1.  **Scope**: Test the interaction of 2 or more real components.
2.  **Speed**: Keep in mind they will be slower than unit tests. Use pytest markers (e.g., `@pytest.mark.integration`) to filter them.
3.  **Resources**: If you need databases or external services, consider using `testcontainers` or high-level mocks.

### References

- `tests/README.md` for the general testing strategy.
- `scripts/verify_daemon.py` for end-to-end system tests.
