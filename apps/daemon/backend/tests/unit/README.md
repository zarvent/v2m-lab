# UNIT TESTS

### What is this folder?

This folder contains the project's **unit tests**. Unit tests focus on verifying the behavior of individual components (functions, methods, classes) in isolation.

### What is it for?

The goal is to ensure each small piece of logic works correctly on its own, without depending on external systems, databases, or network. This allows:

- Fast test execution (milliseconds).
- Precise error localization.
- Executable documentation of each component's expected behavior.

### What can I find here?

- `test_audio_recorder.py`: Tests for the `AudioRecorder` class.
- `test_config.py`: Tests for configuration loading and validation.
- `test_vad_service.py`: Tests for the voice activity detection service (VAD).
- Other `test_*.py` files corresponding to specific `src/v2m` modules.

### How to run these tests

From the project root:

```bash
# run all unit tests
pytest tests/unit

# run a specific file
pytest tests/unit/test_vad_service.py
```

### Design principles

- **Isolation**: We use `unittest.mock` or `pytest-mock` to simulate external dependencies (like `sounddevice` or APIs).
- **Speed**: These tests should not perform real I/O (disk, network).
- **Coverage**: We aim to cover both the "happy path" and error/edge cases.

### References

- [pytest documentation](https://docs.pytest.org/)
- `tests/README.md` for the project's general testing guide.
