# API Reference (IPC)

This section documents the internal communication protocol between the Frontend (Client) and the Daemon (Server).

!!! info "Architecture Note"
    Voice2Machine uses a Unix socket-based architecture for low-latency local communication. It is not a public REST API.

## Message Protocol

All messages (Requests and Responses) follow this binary format:

1.  **Header (4 bytes)**: Big-endian unsigned integer (`>I`) indicating payload size in bytes.
2.  **Payload (N bytes)**: JSON object encoded in UTF-8.

### Limits

- `MAX_REQUEST_SIZE`: 10 MB
- `MAX_RESPONSE_SIZE`: 10 MB

## Command Structure (Request)

The JSON payload must have the following structure:

```json
{
  "command": "command_name",
  "payload": {
    // command-specific arguments
  }
}
```

### Common Commands

#### `start_recording`
Starts audio recording.
- **Payload**: `{}`

#### `stop_recording`
Stops recording and triggers transcription.
- **Payload**: `{}`

#### `get_config`
Retrieves current configuration.
- **Payload**: `{}`

#### `update_config`
Updates configuration values.
- **Payload**: Partial configuration object (e.g., `{"transcription": {"model": "distil-large-v3"}}`).

## Response Structure (Response)

The response JSON payload always includes a `state` field for synchronization with the Frontend.

```json
{
  "status": "success" | "error",
  "data": {
    // requested data or null
  },
  "error": "optional error message",
  "state": {
    "is_recording": boolean,
    "is_transcribing": boolean,
    // ... other system states
  }
}
```
