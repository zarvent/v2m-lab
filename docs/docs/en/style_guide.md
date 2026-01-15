# Style Guide and Governance

This guide defines the standards for Voice2Machine documentation, aligned with "State of the Art 2026".

## Fundamental Principles

1.  **Docs as Code**: Documentation lives in the repository, is versioned with Git, and validated in CI/CD.
2.  **Universal Accessibility**: Strict compliance with WCAG 2.1 Level AA.
3.  **Localization**: The source of truth (`docs/`) is in **Native Latin American Spanish** and **English**. Root files (`README.md`, `AGENTS.md`) are in English (USA) and Spanish.

## Accessibility (WCAG 2.1 AA)

- **Alternative Text**: All images must have descriptive `alt text`.
- **Heading Hierarchy**: Do not skip levels (H1 -> H2 -> H3).
- **Contrast**: Diagrams and screenshots must have high contrast.
- **Links**: Use descriptive text ("see installation guide" instead of "click here").

## Tone and Voice

- **Audience**: Developers and technical users.
- **Tone**: Professional, concise, direct ("Do this" instead of "You could do this").
- **Persona**: Second person ("Configure your environment") or impersonal ("The environment is configured").
- **Language**:
    - **English**: American English.
    - **Spanish**: Neutral/Latin American. Avoid excessive local idioms.

## Markdown Structure

### Admonitions (Notes)

Use admonition blocks to highlight information:

```markdown
!!! note "Note"
    Neutral information.

!!! tip "Tip"
    Help to optimize.

!!! warning "Warning"
    Watch out for this.

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

1.  **Changes**: Any code change affecting functionality requires doc updates in the same PR.
2.  **Review**: Documentation PRs require human review.
3.  **Maintenance**: Quarterly obsolescence review.
