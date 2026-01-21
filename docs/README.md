# Voice2Machine Documentation

> 📚 This directory contains the documentation source files for Voice2Machine.

## Directory Structure

```
docs/
├── docs/               # Documentation source files
│   ├── assets/         # Static assets (CSS, JS, images)
│   │   ├── stylesheets/
│   │   │   └── extra.css       # Custom styling
│   │   ├── javascripts/        # Custom JS (if needed)
│   │   ├── images/             # Documentation images
│   │   ├── logo.svg            # Site logo
│   │   └── favicon.ico         # Browser favicon
│   ├── includes/       # Reusable content
│   │   └── abbreviations.md    # Automatic tooltips
│   ├── en/             # English translations
│   └── es/             # Spanish (default)
├── overrides/          # Theme overrides
│   └── partials/       # Custom template partials
├── requirements.txt    # Python dependencies
└── README.md          # This file
```

## Quick Start

### Prerequisites

- Python 3.10+
- pip

### Local Development

```bash
# Install dependencies
pip install -r docs/requirements.txt

# Install backend (for API docs)
pip install -e apps/daemon/backend

# Start development server
mkdocs serve

# Build static site
mkdocs build
```

The documentation will be available at `http://localhost:8000`

## Writing Documentation

### Adding a New Page

1. Create a new `.md` file in the appropriate language folder (`es/` or `en/`)
2. Add the page to `nav` in `mkdocs.yml`
3. Ensure translations exist in both languages

### Using Features

#### Admonitions (Callouts)

```markdown
!!! note "Title"
Content here.

!!! warning
Warning content.

??? tip "Collapsible"
Click to expand.
```

#### Code Blocks

````markdown
````python title="example.py" hl_lines="2 3"
def hello():
    print("Hello")
    return True
```​
````
````

#### Tabs

````markdown
=== "Python"
`python
    print("Hello")
    `

=== "Bash"
`bash
    echo "Hello"
    `
````

#### Keyboard Shortcuts

```markdown
Press ++ctrl+shift+p++ to open the command palette.
```

### Internationalization (i18n)

- Default language: Spanish (`es/`)
- English translations in `en/`
- Navigation translations in `mkdocs.yml` under `plugins.i18n.languages`

## Deployment

Documentation is automatically deployed to GitHub Pages when changes are pushed to `main`.

- **Trigger paths**: `docs/**`, `mkdocs.yml`, `apps/daemon/backend/src/**/*.py`
- **Output**: https://zarvent.github.io/v2m-lab/

## Contributing

1. Follow the [Style Guide](docs/es/style_guide.md)
2. Ensure all pages have both Spanish and English versions
3. Test locally with `mkdocs serve`
4. Submit a PR with your changes

## License

This documentation is part of Voice2Machine, licensed under GPL-3.0.
