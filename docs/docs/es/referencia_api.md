# Referencia de API (IPC)

Esta sección documenta el protocolo de comunicación interna entre el Frontend (Cliente) y el Daemon (Servidor).

!!! info "Nota de Arquitectura"
    Voice2Machine utiliza una arquitectura basada en sockets Unix para la comunicación local de baja latencia. No es una API REST pública.

## Protocolo de Mensajes

Todos los mensajes (Requests y Responses) siguen este formato binario:

1.  **Header (4 bytes)**: Entero big-endian sin signo (`>I`) que indica el tamaño del payload en bytes.
2.  **Payload (N bytes)**: Objeto JSON codificado en UTF-8.

### Límites

- `MAX_REQUEST_SIZE`: 10 MB
- `MAX_RESPONSE_SIZE`: 10 MB

## Estructura de Comandos (Request)

El payload JSON debe tener la siguiente estructura:

```json
{
  "command": "nombre_del_comando",
  "payload": {
    // argumentos específicos del comando
  }
}
```

### Comandos Comunes

#### `start_recording`
Inicia la grabación de audio.
- **Payload**: `{}`

#### `stop_recording`
Detiene la grabación y dispara la transcripción.
- **Payload**: `{}`

#### `get_config`
Obtiene la configuración actual.
- **Payload**: `{}`

#### `update_config`
Actualiza valores de configuración.
- **Payload**: Objeto parcial de configuración (ej. `{"transcription": {"model": "distil-large-v3"}}`).

## Estructura de Respuestas (Response)

El payload JSON de respuesta siempre incluye un campo `state` para sincronización con el Frontend.

```json
{
  "status": "success" | "error",
  "data": {
    // datos solicitados o null
  },
  "error": "mensaje de error opcional",
  "state": {
    "is_recording": boolean,
    "is_transcribing": boolean,
    // ... otros estados del sistema
  }
}
```
