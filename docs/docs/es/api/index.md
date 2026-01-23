---
title: Referencia de API Python
description: Índice de documentación técnica del backend Voice2Machine.
status: stable
last_update: 2026-01-23
language: Native Latin American Spanish
---

# API Python - Índice

Esta sección proporciona documentación auto-generada de las clases y funciones Python del backend de Voice2Machine.

!!! info "Generado con mkdocstrings"
Esta documentación se extrae automáticamente de los docstrings del código fuente. Para la versión más actualizada, consulta siempre el código en `apps/daemon/backend/src/v2m/`.

---

## Módulos Principales

### [Interfaces](interfaces.md)

Protocolos y contratos que definen el comportamiento esperado de los adaptadores.

### [Dominio](domain.md)

Modelos de dominio, puertos y tipos de error.

### [Servicios](services.md)

Servicios de aplicación incluyendo el Orchestrator principal.

---

## Navegación Rápida

| Clase/Función          | Descripción                              |
| ---------------------- | ---------------------------------------- |
| `Orchestrator`         | Coordinador central del flujo de trabajo |
| `TranscriptionService` | Puerto para servicios de transcripción   |
| `AudioRecorder`        | Interfaz para captura de audio           |
| `LLMProvider`          | Interfaz base para proveedores de IA     |
