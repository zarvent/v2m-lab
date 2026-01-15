---
source:
 - docs/docs/en/architecture.md
---
# Arquitectura Hexagonal

Voice2Machine Backend implementa una **Arquitectura Hexagonal** pura para separar las decisiones técnicas de las reglas de negocio.

## 🧱 Capas del Sistema

### 1. Dominio (`domain/`)

Es el corazón del sistema. Define los modelos de datos (Entidades) y las reglas que no cambian, independientemente de si el audio viene de un micrófono físico o un archivo.

- **Entidades**: Clases Pydantic inmutables (`Transcription`, `AudioChunk`).
- **Puertos (Protocols)**: Definiciones estructurales usando `typing.Protocol` que el sistema necesita para funcionar (ej. `TranscriptionService`).

### 2. Aplicación (`application/`)

Coordina el flujo de datos entre el dominio y la infraestructura. Contiene los "Casos de Uso".

- **Handlers**: Orquestan la lógica. Por ejemplo, recibir audio, enviarlo al servicio de transcripción y luego guardarlo en el historial.

### 3. Infraestructura (`infrastructure/`)

Contiene los "Adaptadores" o implementaciones técnicas detalladas.

- **WhisperAdapter**: Implementa el protocolo de transcripción usando Faster-Whisper.
- **GeminiAdapter**: Implementa el protocolo de refinamiento usando la API de Google.
- **FileSystemAdapter**: Persistencia de datos local.

## 🧠 Inyección de Dependencias

El sistema utiliza un contenedor de dependencias centralizado en `core/container.py`. Esto permite intercambiar implementaciones (ej. usar un simulador de audio para tests) sin tocar la lógica de aplicación.

## 📡 Bus de Eventos

Las comunicaciones internas entre servicios se realizan mediante eventos asíncronos. Esto desacopla a los productores de datos (Captura de audio) de los consumidores (Interfaz de usuario/Logs).
