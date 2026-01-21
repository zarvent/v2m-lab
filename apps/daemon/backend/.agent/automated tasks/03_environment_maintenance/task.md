---
name: Deep Environment Maintenance
description: Perform a deep clean of the development environment to remove stale artifacts and caches.
frequency: Weekly / When encountering weird errors
tags: [maintenance, clean, cache, docker]
---

# 🧹 Deep Environment Maintenance

This task performs a "factory reset" of the temporary development artifacts. Use this when encountering inexplicable import errors, stale cache issues, or to reclaim disk space.

## 📋 Context

- **Targets**: Python bytecodes (`__pycache__`), pytest cache, ruff cache, coverage files, and build dists.
- **Safety**: Does **NOT** delete source code or configuration files.

## 🚀 Execution Steps

### 1. Clean Python Caches

Remove all bytecode and cache directories recursively.

```bash
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type d -name ".pytest_cache" -exec rm -rf {} +
find . -type d -name ".ruff_cache" -exec rm -rf {} +
find . -type d -name ".mypy_cache" -exec rm -rf {} +
```

### 2. Clean Build Artifacts

Remove directories created during package build or installation.

```bash
rm -rf build/
rm -rf dist/
rm -rf *.egg-info/
rm -rf htmlcov/
rm -f .coverage
```

### 3. Clean Temporary Files

Remove editor backups and temporary system files.

```bash
find . -type f -name "*~" -delete
find . -type f -name "*.bak" -delete
find . -type f -name "*.swp" -delete
find . -type f -name ".DS_Store" -delete
```

### 4. Re-sync Environment (Recommended)

After cleaning, it is good practice to ensure the environment is pristine.

```bash
uv sync
```

## 🔍 Validation Criteria

- `ls -a` should not show `.pytest_cache` or `.ruff_cache` immediately after running.
- Workspace should feel "fresh".
