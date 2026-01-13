# Glosario

Este glosario define términos técnicos y de dominio utilizados en Voice2Machine.

## Términos Generales

### Local-First
Filosofía de diseño donde los datos (audio, texto) se procesan y almacenan exclusivamente en el dispositivo del usuario, sin depender de la nube.

### Daemon
Proceso en segundo plano (escrito en Python) que gestiona la grabación, transcripción y comunicación con el frontend.

### IPC (Inter-Process Communication)
Mecanismo utilizado para la comunicación entre el Daemon (Python) y el Frontend (Tauri/Rust). Utilizamos sockets Unix con un protocolo de mensajes enmarcado (header de tamaño + payload JSON).

## Componentes Técnicos

### Whisper
Modelo de reconocimiento de voz (ASR) desarrollado por OpenAI. Voice2Machine utiliza `faster-whisper`, una implementación optimizada con CTranslate2.

### BackendProvider
Componente del frontend (React Context) que gestiona la conexión con el Daemon y distribuye el estado a la UI.

### TelemetryContext
Sub-contexto de React optimizado para actualizaciones de alta frecuencia (métricas de GPU, niveles de audio) para evitar re-renderizados innecesarios de la UI principal.

### CommandBus
Patrón de diseño (CQRS) utilizado en el backend para desacoplar la intención del usuario (Command) de su ejecución (Handler).
