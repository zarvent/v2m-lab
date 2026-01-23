# Documentation Governance for Agents (SOTA 2026)

This guide defines the standards and workflows for maintaining the Voice2Machine documentation portal. Agents working on documentation must strictly adhere to these principles.

## 🏛️ Architecture: The Diátaxis Framework

We follow the **Diátaxis** documentation framework to ensure content serves specific user needs:

1.  **Tutorials (Learning-oriented)**: Step-by-step guides for newcomers to achieve a small, successful outcome (e.g., "Tu primer dictado").
2.  **How-to Guides (Task-oriented)**: Practical steps to solve specific problems for experienced users (e.g., "Configurar micrófono externo").
3.  **Reference (Information-oriented)**: Technical descriptions of the machinery (e.g., REST API endpoints, Python class signatures).
4.  **Explanation (Understanding-oriented)**: Deep dives into architecture and design decisions (e.g., ADRs, Why local-first?).

## 🤖 AI-Readability Standards

To ensure future AI agents can effectively process and maintain this documentation, the following standards are mandatory:

- **YAML Frontmatter**: Every `.md` file in `docs/docs/` must start with a metadata block:
  ```yaml
  ---
  title: Title of the page
  description: Brief description for search engines and AI context.
  ai_context: "Key concepts covered (e.g., FastAPI, Audio Streaming)"
  depends_on: [other/file.md, another/file.md]
  status: draft | review | stable
  ---
  ```
- **Semantic Hierarchy**: Use exactly ONE H1 tag. Follow with H2, then H3. Never skip levels.
- **Explicit Links**: Use relative paths for internal links: `[Guía de Instalación](../instalacion.md)`.
- **Code Annotations**: Use MkDocs Material annotations `(1)` to explain complex code blocks inline.

## 🌐 Internationalization (i18n) Workflow

We use the `i18n` plugin with a **folder-based** structure.

- **Primary Language (Source of Truth)**: `docs/docs/es/` (Native Latin American Spanish).
- **Secondary Language**: `docs/docs/en/` (English).
- **The Synchronization Rule**: Any PR that modifies a file in `es/` MUST include the corresponding update in `en/`. If a full translation is not immediately possible, create the file in `en/` with the original content and a `!!! warning` notice: "This page is currently being translated from Spanish."

## ♿ Accessibility & DX (WCAG 2.2+)

- **Headings**: Must be descriptive and unique.
- **Images**: Always include `alt` text: `![Arquitectura del Daemon](../../assets/diag-arch.svg)`.
- **Keyboard Shortcuts**: Use the `++ctrl+alt+delete++` syntax.
- **Target Size**: Instructions for UI interactions must assume a minimum target size of 24x24px for accessibility.

## 🛠️ Toolchain Mastery

### MkDocs Material Features

- **Admonitions**: Use `!!! note`, `!!! tip`, `!!! warning`, `!!! danger`. Avoid overusing "note".
- **Mermaid Diagrams**: Use for flowcharts and state machines. Ensure they are accessible (use high contrast).
- **Docstrings**: We use `mkdocstrings`. Python code must follow **Google Style docstrings**.
  - Agents must verify that `mkdocstrings` output in `docs/docs/es/api/` is up-to-date after changing function signatures.

### Validation Sequence

Before finishing a documentation task, verify:

1. `ruff check` passes on all modified Python files (for docstrings).
2. The page is correctly registered in the `nav` section of `mkdocs.yml`.
3. Relative links are correct and not broken.
4. Mermaid diagrams render correctly (can be tested locally with `mkdocs serve`).

## 🚫 Forbidden Practices

- **No Absolute Paths**: Never use `/home/...` or `C:\...`.
- **No Latinisms**: Use clear, modern Spanish (e.g., "Iniciar" instead of "Inicializar" where appropriate).
- **No God Pages**: If a page exceeds 1500 words, split it following Diátaxis.
- **No Inline Styles**: Use classes or `extra.css` if absolutely necessary.

---

## URLS

mkdocs:

- https://github.com/squidfunk/mkdocs-material
- https://squidfunk.github.io/mkdocs-material/
