## 🤖 AI & Automatización

Para instrucciones detalladas sobre cómo los agentes de IA deben manejar esta documentación, consulta [AGENTS.md](AGENTS.md).

Este proyecto utiliza:

- **Diátaxis**: Para la organización del contenido.
- **SOTA 2026**: Estándares modernos de accesibilidad y "Docs as Code".
- **i18n**: Flujo de sincronización mandatorio entre español e inglés.

## Principios

Esta documentación sigue tres principios fundamentales:

1. **Simple** - Solo lo esencial, sin sobre-ingeniería
2. **Sólida** - Estructura clara y mantenible
3. **Sostenible** - Fácil de escalar y mantener

## Estructura

```
docs/
├── docs/                   # Contenido fuente
│   ├── assets/             # Recursos estáticos
│   │   ├── stylesheets/    # CSS personalizado (mínimo)
│   │   ├── logo.svg        # Logo del proyecto
│   │   └── favicon.ico     # Favicon
│   ├── includes/           # Contenido reutilizable
│   ├── es/                 # Español (idioma por defecto)
│   └── en/                 # Inglés
├── overrides/              # Overrides del tema
├── requirements.txt        # Dependencias Python
└── README.md               # Este archivo
```

## Desarrollo Local

```bash
# Instalar dependencias
pip install -r docs/requirements.txt
pip install -e apps/daemon/backend

# Servidor de desarrollo
mkdocs serve

# Build de producción
mkdocs build
```

## Guía de Contenido

### Agregar una Página

1. Crear archivo `.md` en `docs/es/` y `docs/en/`
2. Agregar a `nav` en `mkdocs.yml`
3. Probar con `mkdocs serve`

### Navegación Multi-App

La estructura está preparada para múltiples apps:

```yaml
nav:
  - Referencia:
      - API Python:
          - Daemon: # ← App actual
              - api/backend/...
          # - Frontend:       # ← Futuras apps
          #     - api/frontend/...
          # - CLI:
          #     - api/cli/...
```

### Usar Markdown

```markdown
# Título Principal

## Sección

Texto normal con **negrita** y `código`.

!!! note "Nota"
Contenido de la nota.

!!! warning
Contenido de advertencia.

=== "Tab 1"
Contenido tab 1.

=== "Tab 2"
Contenido tab 2.
```

### Documentar Código Python

El plugin `mkdocstrings` extrae automáticamente docstrings:

```markdown
::: v2m.orchestrator.Orchestrator
```

Formato de docstrings (Google style):

```python
def transcribir(audio: bytes) -> str:
    """Transcribe audio a texto.

    Args:
        audio: Bytes de audio en formato WAV.

    Returns:
        Texto transcrito.

    Raises:
        TranscriptionError: Si falla la transcripción.
    """
```

## Internacionalización

- **Idioma por defecto**: Español (`es/`)
- **Traducciones**: Inglés (`en/`)
- **Navegación**: Traducciones en `mkdocs.yml` bajo `plugins.i18n`

Cada página debe existir en ambos idiomas con el mismo nombre de archivo.

## CI/CD

El workflow `.github/workflows/documentation.yml`:

- **Trigger**: Push a `main` que modifique `docs/`, `mkdocs.yml`, o código Python
- **Deploy**: Automático a GitHub Pages
- **URL**: https://zarvent.github.io/v2m-lab/

## Plugins Utilizados

| Plugin                        | Propósito                          |
| ----------------------------- | ---------------------------------- |
| `mkdocs-material`             | Tema principal                     |
| `mkdocs-static-i18n`          | Internacionalización               |
| `mkdocstrings`                | Documentación automática de Python |
| `git-revision-date-localized` | Fecha de última actualización      |

## Qué NO Hacer

- ❌ Agregar plugins innecesarios
- ❌ CSS excesivo que override el tema
- ❌ Páginas sin traducción
- ❌ Documentación duplicada

## Licencia

Esta documentación es parte de Voice2Machine, licenciada bajo GPL-3.0.
