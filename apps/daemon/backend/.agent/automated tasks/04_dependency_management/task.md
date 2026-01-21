---
name: Dependency Management & Security
description: Update project dependencies to latest versions and ensure lockfile integrity using uv.
frequency: Weekly
tags: [dependencies, uv, security, update]
---

# 📦 Dependency Management & Security

This task focuses on keeping the project's dependencies up-to-date and secure, leveraging the speed of `uv`.

## 📋 Context

- **Manager**: `uv` (Universal Package Manager replacement for pip/poetry).
- **Files**: `pyproject.toml` (Constraints) and `uv.lock` (Exact versions).

## 🚀 Execution Steps

### 1. Upgrade Lockfile

Check for newer versions of dependencies allowed by `pyproject.toml` and update the lockfile.

```bash
uv lock --upgrade
```

### 2. Sync Environment

Install the new versions defined in the updated lockfile into the virtual environment.

```bash
uv sync
```

### 3. Verify Updates

Run quick checks to ensure the updates didn't break basic functionality.

```bash
# Check if app can essentially start/import (dry run)
uv run python -c "import v2m; print('Import successful')"
```

### 4. Audit (Optional/Future)

If available, check for vulnerabilities.

```bash
# uv run pip-audit  # If installed
```

## 🔍 Validation Criteria

- `uv sync` completes without conflict resolution errors.
- Application imports successfully.

## ⚠️ Troubleshooting

- **Conflict Errors**: If `uv lock` fails, you may need to adjust version constraints in `pyproject.toml` manually.
