---
title: Guía de Estilo
description: Estándares de documentación y gobernanza "State of the Art 2026".
status: stable
last_update: 2026-01-23
language: Native Latin American Spanish
---

# Guía de Estilo y Gobernanza

Esta guía define los estándares para la documentación de Voice2Machine, alineados con el "Estado del Arte 2026".

## Principios Fundamentales

1.  **Docs as Code**: La documentación vive en el repositorio, se versiona con Git y se valida en CI/CD.
2.  **Accesibilidad Universal**: Cumplimiento estricto de WCAG 2.1 Level AA.
3.  **Localización**: La fuente de la verdad (`docs/`) está en **Español Latinoamericano Nativo**. Los archivos raíz (`README.md`, `AGENTS.md`) están en Inglés (USA) y Español.

## Accesibilidad (WCAG 2.1 AA)

- **Texto Alternativo**: Todas las imágenes deben tener `alt text` descriptivo.
- **Jerarquía de Encabezados**: No saltar niveles (H1 -> H2 -> H3).
- **Contraste**: Diagramas y capturas deben tener alto contraste.
- **Enlaces**: Usar texto descriptivo ("ver guía de instalación" en lugar de "clic aquí").

## Tono y Voz

- **Audiencia**: Desarrolladores y usuarios técnicos.
- **Tono**: Profesional, conciso, directo ("Haga esto" en lugar de "Podría hacer esto").
- **Persona**: Segunda persona ("Configura tu entorno") o impersonal ("Se configura el entorno").
- **Español**: Neutro/Latinoamericano. Evitar modismos locales excesivos.

## Estructura de Markdown

### Admonitions (Notas)

Usa bloques de admonition para resaltar información:

```markdown
!!! note "Nota"
Información neutral.

!!! tip "Consejo"
Ayuda para optimizar.

!!! warning "Advertencia"
Cuidado con esto.

!!! danger "Peligro"
Riesgo de pérdida de datos.
```

### Código

Bloques de código con lenguaje especificado:

```python
def mi_funcion():
    pass
```

## Proceso de Gobernanza

1.  **Cambios**: Todo cambio de código que afecte funcionalidad requiere actualización de docs en el mismo PR.
2.  **Revisión**: Los PRs de documentación requieren revisión humana.
3.  **Mantenimiento**: Revisión trimestral de obsolescencia.
