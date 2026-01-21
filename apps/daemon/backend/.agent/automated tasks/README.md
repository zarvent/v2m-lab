# Automated Tasks for Daemon Backend

This directory contains standardized task definitions for AI agents to execute repetitive maintenance and verification workflows. Each task is self-contained in its own directory with detailed instructions.

## 📂 Workflow Categories

### 🛠️ [01_code_quality](01_code_quality/task.md)

**Objective**: Enforce strict code quality standards.

- **Tools**: `ruff`
- **Actions**: Formatting, Import Sorting, Linting.
- **Frequency**: Daily / Pre-commit.

### 🧪 [02_test_verification](02_test_verification/task.md)

**Objective**: Ensure system stability and regression testing.

- **Tools**: `pytest`, `pytest-cov`
- **Actions**: Full suite execution, coverage analysis.
- **Frequency**: On Change / Daily.

### 🧹 [03_environment_maintenance](03_environment_maintenance/task.md)

**Objective**: Deep clean of development artifacts.

- **Tools**: Shell utilities (`find`, `rm`)
- **Actions**: Cache removal, build artifact cleanup.
- **Frequency**: Weekly / Debugging.

### 📦 [04_dependency_management](04_dependency_management/task.md)

**Objective**: Keep dependencies up-to-date and secure.

- **Tools**: `uv`
- **Actions**: Lockfile upgrade, environment sync.
- **Frequency**: Weekly.

## Usage for Agents

When instructed to perform a task (e.g., "Run quality checks"), navigate to the relevant directory and follow the steps in `task.md` **exactly**. These files serve as the immutable Source of Truth.
