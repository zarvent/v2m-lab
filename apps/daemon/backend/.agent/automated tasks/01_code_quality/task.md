---
name: Enforce Code Quality Standards
description: Comprehensive check and auto-fix for code formatting, style, and import sorting using Ruff.
frequency: Daily / Pre-commit
tags: [quality, lint, format, ruff, python]
---

# 🛡️ Enforce Code Quality Standards

This task ensures the codebase adheres to the strict quality vectors defined in `pyproject.toml` using `ruff`.

## 📋 Context

- **Tooling**: We use `ruff` for both linting and formatting. It replaces black, isort, and flake8.
- **Standards**: Google-style docstrings, 120 char line limit, sorted imports.
- **Goal**: Maintain a "clean code" state where no warnings exist.

## 🚀 Execution Steps

### 1. Format Code

Apply the auto-formatter to fix layout, spacing, and quotes.

```bash
uv run ruff format .
```

### 2. Sort and Organize Imports

Ensure imports are sorted and grouped standardly (Future -> Stdlib -> Third Party -> Local).

```bash
uv run ruff check --select I --fix .
```

### 3. Deep Linting & Auto-fix

Run the full linter suite configured in `pyproject.toml` (`E`, `W`, `F`, `B`, `UP`, `SIM`, `RUF`, `D`).
_Note: This cleans up unused variables, simplifies logic, and upgrades syntax._

```bash
uv run ruff check --fix .
```

### 4. Verification (Read-Only)

Run a final pass to ensure no unfixable errors remain. If this step fails, manual intervention is required.

```bash
uv run ruff check .
```

## 🔍 Validation Criteria

- Exit code must be `0`.
- output should contain "All checks passed!" or be empty.

## ⚠️ Troubleshooting

- **D100/D104 Errors**: These are currently ignored in config. If they appear, check `pyproject.toml`.
- **SyntaxError**: If `ruff` fails to parse, check for Python 3.12+ incompatible syntax.
