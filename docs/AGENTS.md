# Voice2Machine - Documentación

Instrucciones para agentes de IA que trabajan con la documentación del proyecto.

**Stack**: MkDocs Material + i18n + mkdocstrings
**Framework**: Diátaxis (Tutoriales, Guías, Referencia, Explicación)
**Idioma principal**: Español latinoamericano nativo

---

## Inicio Rápido

```bash
# Instalar dependencias
pip install -r docs/requirements.txt
pip install -e apps/daemon/backend  # Requerido para mkdocstrings

# Servir localmente (hot reload)
mkdocs serve

# Construir para producción
mkdocs build
```

---

## Estructura de Carpetas

```
docs/
├── docs/                    # Fuente de contenido (mkdocs lee desde aquí)
│   ├── es/                  # Español (IDIOMA POR DEFECTO)
│   │   ├── index.md         # Página principal
│   │   ├── guia_rapida.md   # Getting started
│   │   ├── adr/             # Architecture Decision Records
│   │   └── api/             # Referencia API (auto-generada)
│   ├── en/                  # Inglés (traducciones)
│   └── assets/              # Recursos compartidos
│       ├── images/
│       ├── stylesheets/
│       └── javascripts/
├── ideas/                   # Borradores y propuestas futuras
├── llm/                     # Logs y prompts de LLM
├── requirements.txt         # Dependencias de MkDocs
└── AGENTS.md                # Este archivo
```

**Regla clave**: Todo contenido nuevo va primero en `docs/es/`, luego se traduce a `docs/en/`.

---

## Comandos por Archivo

```bash
# Verificar sintaxis de un archivo Markdown
markdownlint docs/docs/es/archivo.md

# Previsualizar cambios (abre http://127.0.0.1:8000)
mkdocs serve

# Validar enlaces rotos
mkdocs build --strict
```

---

## Convenciones de Escritura

### Frontmatter Obligatorio

Todas las páginas deben incluir este encabezado YAML:

```yaml
---
title: "Título de la Página"
description: "Descripción breve para SEO (máx 160 caracteres)"
status: stable # stable | draft | deprecated
last_update: 2026-01-23
language: es # es | en
---
```

### Jerarquía de Encabezados

```markdown
# H1 - Solo uno por página (coincide con `title`)

## H2 - Secciones principales

### H3 - Subsecciones

#### H4 - Detalles específicos (evitar si es posible)
```

**Prohibido**: Saltar niveles (H1 → H3 directamente).

### Admonitions Permitidos

```markdown
!!! note "Nota"
Información adicional relevante.

!!! tip "Consejo"
Mejores prácticas o atajos útiles.

!!! warning "Advertencia"
Precauciones importantes.

!!! danger "Peligro"
Acciones que pueden causar pérdida de datos o errores graves.
```

### Enlaces

```markdown
# ✅ Correcto: texto descriptivo

Consulta la [guía de instalación](instalacion.md) para más detalles.

# ❌ Incorrecto: "click aquí"

Para más detalles, [haz clic aquí](instalacion.md).
```

### Bloques de Código

````markdown
# ✅ Siempre especificar el lenguaje

```python
def ejemplo():
    return "hola"
```
````

# ❌ Sin lenguaje

```
def ejemplo():
    return "hola"
```

````

---

## Accesibilidad (WCAG 2.1 AA)

| Requisito | Implementación |
|-----------|----------------|
| **Alt text** | Todas las imágenes: `![Descripción clara](imagen.png)` |
| **Contraste** | Usar colores del tema Material (ya cumple) |
| **Navegación** | Headings jerárquicos para screen readers |
| **Targets** | Links/botones mínimo 24x24px |

---

## Framework Diátaxis

Organiza el contenido según su propósito:

| Tipo | Propósito | Ubicación | Ejemplo |
|------|-----------|-----------|---------|
| **Tutoriales** | Aprender haciendo | `guia_rapida.md` | "Tu primera transcripción" |
| **Guías** | Resolver tareas específicas | `configuracion.md`, `atajos_teclado.md` | "Cómo cambiar el idioma del modelo" |
| **Referencia** | Información técnica precisa | `api/`, `referencia_api.md` | Documentación de endpoints |
| **Explicación** | Entender conceptos | `arquitectura.md`, `adr/` | "Por qué usamos Hexagonal Architecture" |

---

## Sincronización Código ↔ Docs

### Regla de Oro

> **Todo PR que modifica funcionalidad DEBE actualizar la documentación correspondiente.**

### API Auto-documentada

Los docstrings de Python se extraen automáticamente con `mkdocstrings`:

```python
# En src/v2m/api/routes/recording.py
async def toggle() -> RecordingResponse:
    """Alterna el estado de grabación.

    Returns:
        RecordingResponse: Estado actual y texto transcrito (si aplica).

    Raises:
        ServiceUnavailableError: Si el servicio de audio no responde.
    """
````

En la documentación:

```markdown
::: v2m.api.routes.recording.toggle
options:
show_source: false
```

### Checklist para PRs

- [ ] ¿Agregaste nueva funcionalidad? → Actualiza `referencia_api.md` o `api/`
- [ ] ¿Cambiaste configuración? → Actualiza `configuracion.md`
- [ ] ¿Modificaste arquitectura? → Crea/actualiza ADR en `adr/`
- [ ] ¿El cambio afecta al usuario? → Actualiza `changelog.md`

---

## ADRs (Architecture Decision Records)

### Cuándo Crear un ADR

- Decisiones que afectan múltiples componentes
- Cambios de dependencias mayores
- Trade-offs significativos de diseño

### Plantilla

```markdown
---
title: "ADR-XXX: Título de la Decisión"
status: proposed # proposed | accepted | deprecated | superseded
date: 2026-01-23
---

# ADR-XXX: Título

## Contexto

[Problema o necesidad que motiva la decisión]

## Decisión

[La decisión tomada]

## Consecuencias

[Impactos positivos y negativos]

## Alternativas Consideradas

[Otras opciones evaluadas y por qué se descartaron]
```

---

## Errores Comunes

### ❌ Prohibido

| Error                            | Por qué                               | Solución                                  |
| -------------------------------- | ------------------------------------- | ----------------------------------------- |
| Agregar plugins sin autorización | Aumenta complejidad y tiempo de build | Consultar antes de modificar `mkdocs.yml` |
| CSS excesivo sobre el tema       | Dificulta mantenimiento               | Usar variables de Material Theme          |
| Páginas sin traducción           | Rompe navegación i18n                 | Crear al menos un stub en ambos idiomas   |
| Documentación duplicada          | Desincronización inevitable           | Una fuente de verdad, enlaces al resto    |
| Enlaces "click aquí"             | Mala accesibilidad                    | Texto descriptivo del destino             |
| Saltar niveles de heading        | Confunde screen readers               | Respetar H1 → H2 → H3                     |

### ✅ Buenas Prácticas

- Ejecutar `mkdocs serve` antes de commitear
- Usar `mkdocs build --strict` para detectar enlaces rotos
- Mantener páginas cortas y enfocadas (máx ~1500 palabras)
- Preferir listas y tablas sobre párrafos largos

---

## CI/CD

El workflow `.github/workflows/documentation.yml` despliega automáticamente a GitHub Pages en cada push a `main`.

**URL de producción**: https://zarvent.github.io/v2m-lab/

---

## Idiomas

| Contexto                    | Idioma                               |
| --------------------------- | ------------------------------------ |
| Contenido de docs (`docs/`) | Español latinoamericano nativo       |
| Comentarios en código       | Español latinoamericano nativo       |
| Commits                     | Inglés (Conventional Commits)        |
| README raíz                 | Inglés + versión española (LEEME.md) |
