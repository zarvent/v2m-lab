---
title: Contributing Guide
description: Instructions and standards for collaborating on Voice2Machine.
status: stable
last_update: 2026-01-23
language: US English
---

# ❤️ Contributing Guide

Thank you for your interest in contributing to **Voice2Machine**! This project is built on collaboration and quality code.

To maintain our "State of the Art 2026" standards, we follow strict but fair rules. Please read this before submitting your first Pull Request.

---

## 🚀 Workflow

1.  **Discussion First**: Before writing code, open an [Issue](https://github.com/v2m-lab/voice2machine/issues) to discuss the change. This avoids duplicate work or rejections due to architectural misalignment.
2.  **Fork & Branch**:
    - Fork the repository.
    - Create a descriptive branch: `feat/new-gpu-support` or `fix/transcription-error`.
3.  **Local Development**: Follow the [Installation](installation.md) guide to set up your development environment.

---

## 📏 Quality Standards

### Code

- **Backend (Python)**:
  - Strict static typing (100% Type Hints).
  - Linter: `ruff check src/ --fix`.
  - Formatter: `ruff format src/`.
  - Tests: `pytest` must pass at 100%.
- **Frontend (Tauri/React)**:
  - Strict TypeScript (no `any`).
  - Linter: `npm run lint`.
  - Functional components and Hooks.

### Commits

We use **Conventional Commits**. Your commit message must follow this format:

```text
<type>(<scope>): <short description>

[Optional detailed body]
```

**Allowed Types:**

- `feat`: New functionality.
- `fix`: Bug fix.
- `docs`: Documentation only.
- `refactor`: Code change that doesn't fix bugs or add features.
- `test`: Add or fix tests.
- `chore`: Maintenance, dependencies.

**Example:**

> `feat(whisper): upgrade to faster-whisper 1.0.0 for 20% speedup`

### Documentation (Docs as Code)

If you change functionality, you **must** update documentation in `docs/docs/`.

- Verify that `mkdocs serve` works locally.
- Follow the [Style Guide](style_guide.md).

---

## ✅ Pull Request Checklist

Before submitting your PR:

- [ ] I have run local tests and they pass.
- [ ] I have linted the code (`ruff`, `eslint`).
- [ ] I have updated relevant documentation.
- [ ] I have added an entry to `CHANGELOG.md` (if applicable).
- [ ] My code follows Hexagonal Architecture (no prohibited cross-imports).

!!! tip "Help"
If you have questions about architecture or design, check the documents in `docs/docs/adr/` or ask in the corresponding Issue.
