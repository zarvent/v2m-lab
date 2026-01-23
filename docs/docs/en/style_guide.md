---
title: Style Guide
description: Documentation and governance standards "State of the Art 2026".
status: stable
last_update: 2026-01-23
language: US English
---

# Style Guide and Governance

This guide defines the standards for Voice2Machine documentation, aligned with "State of the Art 2026".

## Fundamental Principles

1.  **Docs as Code**: Documentation lives in the repository, is versioned with Git, and validated in CI/CD.
2.  **Universal Accessibility**: Strict WCAG 2.1 Level AA compliance.
3.  **Localization**: The source of truth (`docs/`) is in **Native Latin American Spanish**. Root files (`README.md`, `AGENTS.md`) are in English (USA) and Spanish.

## Accessibility (WCAG 2.1 AA)

- **Alt Text**: All images must have descriptive `alt text`.
- **Heading Hierarchy**: Don't skip levels (H1 -> H2 -> H3).
- **Contrast**: Diagrams and screenshots must have high contrast.
- **Links**: Use descriptive text ("see installation guide" instead of "click here").

## Tone and Voice

- **Audience**: Developers and technical users.
- **Tone**: Professional, concise, direct ("Do this" instead of "You could do this").
- **Person**: Second person ("Configure your environment") or impersonal ("The environment is configured").
- **English**: Standard American English. Avoid excessive local idioms.

## Markdown Structure

### Admonitions (Notes)

Use admonition blocks to highlight information:

```markdown
!!! note "Note"
Neutral information.

!!! tip "Tip"
Optimization help.

!!! warning "Warning"
Be careful with this.

!!! danger "Danger"
Risk of data loss.
```

### Code

Code blocks with specified language:

```python
def my_function():
    pass
```

## Governance Process

1.  **Changes**: Any code change affecting functionality requires documentation update in the same PR.
2.  **Review**: Documentation PRs require human review.
3.  **Maintenance**: Quarterly obsolescence review.
