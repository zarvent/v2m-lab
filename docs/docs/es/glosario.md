---
title: Glosario
description: Definiciones de términos técnicos y de dominio de Voice2Machine.
status: stable
last_update: 2026-01-23
language: Native Latin American Spanish
---

# Glosario

Este glosario define términos técnicos y de dominio utilizados en Voice2Machine.

## Términos Generales

### Local-First

Filosofía de diseño donde los datos (audio, texto) se procesan y almacenan exclusivamente en el dispositivo del usuario, sin depender de la nube.

### Daemon

Proceso en segundo plano (escrito en Python) que gestiona la grabación, transcripción y comunicación con el frontend.

### API REST

Mecanismo de comunicación entre el Daemon (Python) y los clientes (scripts, frontends). Utilizamos FastAPI con endpoints HTTP estándar y WebSocket para eventos en tiempo real.

## Componentes Técnicos

### Whisper

Modelo de reconocimiento de voz (ASR) desarrollado por OpenAI. Voice2Machine utiliza `faster-whisper`, una implementación optimizada con CTranslate2.

### Workflows (Flujos de Trabajo)

Componentes especializados de coordinación que gestionan el ciclo de vida completo de una tarea específica (ej: `RecordingWorkflow`, `LLMWorkflow`). Reemplazan al antiguo "Orchestrator" monolítico para una mejor trazabilidad y mantenibilidad.

### Features (Características)

Módulos autocontenidos que agrupan la lógica de dominio y sus adaptadores de infraestructura (audio, llm, transcripción). Representan las capacidades core del sistema.

### BackendProvider

Componente del frontend (React Context) que gestiona la conexión con el Daemon y distribuye el estado a la UI.

### TelemetryContext

Sub-contexto de React optimizado para actualizaciones de alta frecuencia (métricas de GPU, niveles de audio) para evitar re-renderizados innecesarios de la UI principal.

### Arquitectura Modular

Evolución de la Arquitectura Hexagonal que organiza el código en torno a módulos de negocio (Features) y flujos de ejecución (Workflows), minimizando el acoplamiento y maximizando la claridad.
