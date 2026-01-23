---
title: Referencia de API REST
description: Documentación de los endpoints HTTP y el protocolo WebSocket de Voice2Machine.
ai_context: "FastAPI, REST API, WebSocket, Endpoints"
depends_on: []
status: stable
---

# Referencia de API REST

Esta sección documenta la API REST del Daemon Voice2Machine (v0.2.0+).

!!! info "Arquitectura Actualizada"
Voice2Machine utiliza **FastAPI** para la comunicación cliente-servidor, reemplazando el sistema anterior basado en Unix Sockets IPC. Esto permite probar endpoints directamente con `curl` o cualquier cliente HTTP.

## Información General

| Propiedad                     | Valor                                     |
| ----------------------------- | ----------------------------------------- |
| **Base URL**                  | `http://localhost:8765`                   |
| **Protocolo**                 | HTTP/1.1 + WebSocket                      |
| **Formato**                   | JSON (UTF-8)                              |
| **Documentación Interactiva** | `http://localhost:8765/docs` (Swagger UI) |

---

## Endpoints REST

### POST `/toggle`

Toggle de grabación (iniciar/detener). Este es el endpoint principal que usa el atajo de teclado.

=== "Request"
`bash
    curl -X POST http://localhost:8765/toggle | jq
    `

=== "Response (Iniciando)"
`json
    {
      "status": "recording",
      "message": "Grabación iniciada",
      "text": null
    }
    `

=== "Response (Deteniendo)"
`json
    {
      "status": "idle",
      "message": "Transcripción completada",
      "text": "El texto transcrito aparece aquí..."
    }
    `

---

### POST `/start`

Inicia grabación explícitamente. Útil cuando necesitas control separado de inicio/fin.

=== "Request"
`bash
    curl -X POST http://localhost:8765/start | jq
    `

=== "Response"
`json
    {
      "status": "recording",
      "message": "Grabación iniciada",
      "text": null
    }
    `

---

### POST `/stop`

Detiene grabación y transcribe el audio capturado.

=== "Request"
`bash
    curl -X POST http://localhost:8765/stop | jq
    `

=== "Response"
`json
    {
      "status": "idle",
      "message": "Transcripción completada",
      "text": "El texto transcrito aparece aquí..."
    }
    `

---

### POST `/llm/process`

Procesa texto con LLM (limpieza, puntuación, formato). El backend se selecciona según `config.toml`.

=== "Request"
`bash
    curl -X POST http://localhost:8765/llm/process \
      -H "Content-Type: application/json" \
      -d '{"text": "hola como estas espero que bien"}' | jq
    `

=== "Response"
`json
    {
      "text": "Hola, ¿cómo estás? Espero que bien.",
      "backend": "gemini"
    }
    `

---

### POST `/llm/translate`

Traduce texto a otro idioma usando LLM.

=== "Request"
`bash
    curl -X POST http://localhost:8765/llm/translate \
      -H "Content-Type: application/json" \
      -d '{"text": "Buenos días", "target_lang": "en"}' | jq
    `

=== "Response"
`json
    {
      "text": "Good morning",
      "backend": "gemini"
    }
    `

---

### GET `/status`

Retorna el estado actual del daemon.

=== "Request"
`bash
    curl http://localhost:8765/status | jq
    `

=== "Response"
`json
    {
      "state": "idle",
      "recording": false,
      "model_loaded": true
    }
    `

**Estados posibles:**

| Estado       | Descripción                         |
| ------------ | ----------------------------------- |
| `idle`       | Esperando comandos                  |
| `recording`  | Grabando audio                      |
| `processing` | Transcribiendo o procesando con LLM |

---

### GET `/health`

Health check para systemd/scripts de monitoreo.

=== "Request"
`bash
    curl http://localhost:8765/health | jq
    `

=== "Response"
`json
    {
      "status": "ok",
      "version": "0.2.0"
    }
    `

---

## WebSocket

### WS `/ws/events`

Stream de eventos en tiempo real. Útil para mostrar transcripción provisional mientras el usuario habla.

=== "Conexión (JavaScript)"

````javascript
const ws = new WebSocket('ws://localhost:8765/ws/events');

    ws.onmessage = (event) => {
      const { event: eventType, data } = JSON.parse(event.data);
      console.log(`Evento: ${eventType}`, data);
    };
    ```

=== "Conexión (Python)"
```python
import asyncio
import websockets

    async def listen():
        async with websockets.connect('ws://localhost:8765/ws/events') as ws:
            async for message in ws:
                print(message)

    asyncio.run(listen())
    ```

**Eventos emitidos:**

| Evento                 | Campos                           | Descripción                                          |
| ---------------------- | -------------------------------- | ---------------------------------------------------- |
| `transcription_update` | `text: str`, `final: bool`       | Actualización de transcripción (provisional o final) |
| `heartbeat`            | `timestamp: float`, `state: str` | Latido para mantener conexión viva                   |

---

## Modelos de Datos

### ToggleResponse

```python
class ToggleResponse(BaseModel):
    status: str      # 'recording' | 'idle'
    message: str     # Mensaje descriptivo
    text: str | None # Texto transcrito (solo en stop)
````

### StatusResponse

```python
class StatusResponse(BaseModel):
    state: str        # 'idle' | 'recording' | 'processing'
    recording: bool   # True si está grabando
    model_loaded: bool # True si Whisper está en VRAM
```

### LLMResponse

```python
class LLMResponse(BaseModel):
    text: str    # Texto procesado/traducido
    backend: str # 'gemini' | 'ollama' | 'local'
```

---

## Códigos de Error

| Código HTTP | Significado                            |
| ----------- | -------------------------------------- |
| `200`       | Operación exitosa                      |
| `422`       | Error de validación (payload inválido) |
| `500`       | Error interno del servidor             |

!!! tip "Depuración"
Usa la documentación interactiva en `http://localhost:8765/docs` para probar endpoints visualmente.
