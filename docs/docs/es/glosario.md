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

### Orchestrator

Componente central de coordinación que gestiona el ciclo de vida completo del flujo de trabajo: grabación → transcripción → post-procesamiento. Reemplaza el patrón anterior CQRS/CommandBus con un enfoque más directo y simple.

### BackendProvider

Componente del frontend (React Context) que gestiona la conexión con el Daemon y distribuye el estado a la UI.

### TelemetryContext

Sub-contexto de React optimizado para actualizaciones de alta frecuencia (métricas de GPU, niveles de audio) para evitar re-renderizados innecesarios de la UI principal.

### Arquitectura Hexagonal

También conocida como "Puertos y Adaptadores". Patrón de diseño donde la lógica de negocio central (el hexágono) está aislada de las preocupaciones externas (bases de datos, APIs, UI) a través de interfaces bien definidas (puertos) e implementaciones (adaptadores).
