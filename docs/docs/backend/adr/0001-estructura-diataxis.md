# 1. Adopción de Diátaxis y Docs-as-Code

* **Estado:** Aceptado
* **Fecha:** 2026-01-20

## Contexto
Necesitamos una documentación escalable que diferencie entre material de aprendizaje y referencia técnica pura.

## Decisión
Adoptar el framework **Diátaxis** y centralizar la documentación en el monorepo usando MkDocs.

## Consecuencias
La documentación del backend vivirá junto al código en `docs/docs/backend`, permitiendo actualizaciones atómicas en los PRs.
