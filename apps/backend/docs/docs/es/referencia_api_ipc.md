# Referencia del Protocolo IPC (Inter-Process Communication)

El backend y el frontend de Voice2Machine se comunican exclusivamente a través de un **Socket Unix**, utilizando un protocolo binario/JSON personalizado optimizado para baja latencia y seguridad local.

## 📡 Visión General

- **Transporte**: Unix Domain Socket (UDS).
- **Ubicación del Socket**: `$XDG_RUNTIME_DIR/v2m/v2m.sock` (ej. `/run/user/1000/v2m/v2m.sock`).
- **Modelo**: Request-Response síncrono sobre conexión persistente (Keep-Alive).
- **Formato de Datos**: JSON (UTF-8).
- **Framing**: Cabecera de longitud de 4 bytes (Big Endian).

!!! info "Por qué no HTTP/REST?"
    HTTP introduce un overhead significativo de handshake y parsing de cabeceras en cada petición. Nuestro protocolo sobre UDS reduce la latencia a microsegundos, esencial para comandos de control en tiempo real (ej. "Detener grabación ahora").

---

## 📦 Estructura del Mensaje (Framing)

Cada mensaje enviado al socket (en ambas direcciones) debe seguir esta estructura binaria:

```
[ Longitud (4 bytes) ] [ Payload JSON (N bytes) ]
```

1.  **Longitud**: Entero de 4 bytes sin signo, Big Endian (`>I` en `struct` de Python). Indica el tamaño exacto del Payload en bytes.
2.  **Payload**: Cadena JSON codificada en UTF-8.

### Ejemplo Hexadecimal
Para enviar el JSON `{"cmd":"PING"}` (14 bytes):

```
00 00 00 0E 7B 22 63 6D 64 22 3A 22 50 49 4E 47 22 7D
| Length  | {  "  c  m  d  "  :  "  P  I  N  G  "  }
```

---

## 📨 Peticiones (Request)

El cliente envía un objeto JSON con la siguiente estructura:

```json
{
  "cmd": "NOMBRE_COMANDO",
  "data": {
    "parametro1": "valor",
    "parametro2": 123
  }
}
```

*   **cmd** (string, requerido): El comando a ejecutar (ver lista abajo).
*   **data** (object, opcional): Parámetros específicos del comando.

---

## 📩 Respuestas (Response)

El servidor responde siempre con un objeto JSON:

```json
{
  "status": "success",
  "data": { ... },
  "error": null
}
```

*   **status** (string): `"success"` o `"error"`.
*   **data** (object | null): Datos de respuesta si `status` es success.
*   **error** (string | null): Mensaje de error descriptivo si `status` es error.

---

## 🛠️ Comandos Disponibles

Lista completa de comandos definidos en `IPCCommand`.

### Control de Grabación

#### `START_RECORDING`
Inicia la captura de audio y el streaming de transcripción.
*   **Data**: N/A
*   **Respuesta**: `{ "status": "success" }` cuando la grabación ha iniciado efectivamente.

#### `STOP_RECORDING`
Detiene la grabación, finaliza el archivo de audio y retorna la transcripción final.
*   **Data**: N/A
*   **Respuesta**:
    ```json
    {
      "status": "success",
      "data": {
        "text": "Texto final transcrito.",
        "audio_path": "/path/to/recording.wav"
      }
    }
    ```

#### `TOGGLE_RECORDING`
Alterna entre iniciar y detener. Útil para atajos globales.

### Procesamiento de Texto (LLM)

#### `PROCESS_TEXT`
Envía texto al LLM configurado (Gemini/Local) para refinamiento o instrucción.
*   **Data**:
    *   `text` (string): Texto a procesar.
    *   `instruction` (string, opcional): Instrucción específica (ej. "Resumir").
*   **Respuesta**: `{ "data": { "text": "Texto procesado..." } }`

#### `TRANSLATE_TEXT`
Traduce el texto al idioma configurado.
*   **Data**: `{ "text": "Hola mundo" }`

### Gestión del Sistema

#### `PING`
Healthcheck. El servidor responde inmediatamente.
*   **Respuesta**: `{ "status": "success", "data": "PONG" }`

#### `GET_STATUS`
Obtiene telemetría del sistema.
*   **Respuesta**:
    ```json
    {
      "data": {
        "is_recording": false,
        "gpu_usage": 45,
        "vram_usage": 2048,
        "cpu_usage": 12
      }
    }
    ```

#### `UPDATE_CONFIG`
Actualiza la configuración en caliente (sin reiniciar).
*   **Data**: Objeto parcial de configuración (deep merge).
    ```json
    {
      "transcription": {
        "whisper": { "vad_filter": false }
      }
    }
    ```

#### `GET_CONFIG`
Devuelve la configuración actual completa.

#### `SHUTDOWN`
Solicita al demonio que se apague ordenadamente (liberando GPU y sockets).

---

## 🐍 Ejemplo de Cliente (Python)

```python
import socket
import json
import struct

SOCK_PATH = "/run/user/1000/v2m/v2m.sock"

def send_command(cmd, data=None):
    client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    client.connect(SOCK_PATH)

    # 1. Preparar Payload
    payload = json.dumps({"cmd": cmd, "data": data}).encode('utf-8')

    # 2. Enviar Header (Longitud) + Payload
    header = struct.pack(">I", len(payload))
    client.sendall(header + payload)

    # 3. Leer Header de Respuesta
    resp_header = client.recv(4)
    resp_len = struct.unpack(">I", resp_header)[0]

    # 4. Leer Payload de Respuesta
    resp_bytes = client.recv(resp_len)
    response = json.loads(resp_bytes)

    client.close()
    return response

# Uso
print(send_command("PING"))
# {'status': 'success', 'data': 'PONG', 'error': None}
```
