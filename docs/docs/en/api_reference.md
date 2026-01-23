---
title: REST API Reference
description: Documentation of HTTP endpoints and WebSocket protocol for Voice2Machine.
ai_context: "FastAPI, REST API, WebSocket, Endpoints"
depends_on: []
status: stable
---

# REST API Reference

This section documents the Voice2Machine Daemon REST API (v0.2.0+).

!!! info "Updated Architecture"
Voice2Machine uses **FastAPI** for client-server communication, replacing the previous Unix Sockets IPC system. This allows testing endpoints directly with `curl` or any HTTP client.

## General Information

| Property             | Value                                     |
| -------------------- | ----------------------------------------- |
| **Base URL**         | `http://localhost:8765`                   |
| **Protocol**         | HTTP/1.1 + WebSocket                      |
| **Format**           | JSON (UTF-8)                              |
| **Interactive Docs** | `http://localhost:8765/docs` (Swagger UI) |

---

## REST Endpoints

### POST `/toggle`

Recording toggle (start/stop). This is the main endpoint used by keyboard shortcuts.

=== "Request"
`bash
    curl -X POST http://localhost:8765/toggle | jq
    `

=== "Response (Starting)"
`json
    {
      "status": "recording",
      "message": "Recording started",
      "text": null
    }
    `

=== "Response (Stopping)"
`json
    {
      "status": "idle",
      "message": "Transcription complete",
      "text": "The transcribed text appears here..."
    }
    `

---

### POST `/start`

Explicitly start recording. Useful when you need separate start/stop control.

=== "Request"
`bash
    curl -X POST http://localhost:8765/start | jq
    `

=== "Response"
`json
    {
      "status": "recording",
      "message": "Recording started",
      "text": null
    }
    `

---

### POST `/stop`

Stop recording and transcribe captured audio.

=== "Request"
`bash
    curl -X POST http://localhost:8765/stop | jq
    `

=== "Response"
`json
    {
      "status": "idle",
      "message": "Transcription complete",
      "text": "The transcribed text appears here..."
    }
    `

---

### POST `/llm/process`

Process text with LLM (cleanup, punctuation, formatting). Backend is selected based on `config.toml`.

=== "Request"
`bash
    curl -X POST http://localhost:8765/llm/process \
      -H "Content-Type: application/json" \
      -d '{"text": "hello how are you hope youre well"}' | jq
    `

=== "Response"
`json
    {
      "text": "Hello, how are you? Hope you're well.",
      "backend": "gemini"
    }
    `

---

### POST `/llm/translate`

Translate text to another language using LLM.

=== "Request"
`bash
    curl -X POST http://localhost:8765/llm/translate \
      -H "Content-Type: application/json" \
      -d '{"text": "Good morning", "target_lang": "es"}' | jq
    `

=== "Response"
`json
    {
      "text": "Buenos días",
      "backend": "gemini"
    }
    `

---

### GET `/status`

Returns current daemon state.

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

**Possible States:**

| State        | Description                         |
| ------------ | ----------------------------------- |
| `idle`       | Waiting for commands                |
| `recording`  | Recording audio                     |
| `processing` | Transcribing or processing with LLM |

---

### GET `/health`

Health check for systemd/monitoring scripts.

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

Real-time event stream. Useful for showing provisional transcription while user speaks.

=== "Connection (JavaScript)"

````javascript
const ws = new WebSocket('ws://localhost:8765/ws/events');

    ws.onmessage = (event) => {
      const { event: eventType, data } = JSON.parse(event.data);
      console.log(`Event: ${eventType}`, data);
    };
    ```

=== "Connection (Python)"
```python
import asyncio
import websockets

    async def listen():
        async with websockets.connect('ws://localhost:8765/ws/events') as ws:
            async for message in ws:
                print(message)

    asyncio.run(listen())
    ```

**Emitted Events:**

| Event                  | Fields                           | Description                                 |
| ---------------------- | -------------------------------- | ------------------------------------------- |
| `transcription_update` | `text: str`, `final: bool`       | Transcription update (provisional or final) |
| `heartbeat`            | `timestamp: float`, `state: str` | Heartbeat to keep connection alive          |

---

## Data Models

### ToggleResponse

```python
class ToggleResponse(BaseModel):
    status: str      # 'recording' | 'idle'
    message: str     # Descriptive message
    text: str | None # Transcribed text (only on stop)
````

### StatusResponse

```python
class StatusResponse(BaseModel):
    state: str        # 'idle' | 'recording' | 'processing'
    recording: bool   # True if recording
    model_loaded: bool # True if Whisper is in VRAM
```

### LLMResponse

```python
class LLMResponse(BaseModel):
    text: str    # Processed/translated text
    backend: str # 'gemini' | 'ollama' | 'local'
```

---

## Error Codes

| HTTP Code | Meaning                            |
| --------- | ---------------------------------- |
| `200`     | Successful operation               |
| `422`     | Validation error (invalid payload) |
| `500`     | Internal server error              |

!!! tip "Debugging"
Use the interactive documentation at `http://localhost:8765/docs` to test endpoints visually.
