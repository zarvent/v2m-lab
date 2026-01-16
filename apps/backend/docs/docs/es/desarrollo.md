# Guía de Desarrollo Backend

Instrucciones para configurar el entorno de desarrollo y contribuir al daemon de Voice2Machine.

## 🛠️ Prerrequisitos del Sistema

Antes de instalar las dependencias de Python, asegúrate de tener las librerías del sistema necesarias.

### Ubuntu/Debian
```bash
sudo apt update
sudo apt install -y python3-dev build-essential portaudio19-dev ffmpeg git
```

### Fedora
```bash
sudo dnf install -y python3-devel gcc portaudio-devel ffmpeg git
```

### Arch Linux
```bash
sudo pacman -S python base-devel portaudio ffmpeg git
```

---

## 🐍 Configuración del Entorno Python

Recomendamos **Python 3.12** para aprovechar las mejoras de rendimiento en `asyncio`.

1.  **Crear Entorno Virtual**:
    ```bash
    cd apps/backend
    python3.12 -m venv .venv
    source .venv/bin/activate
    ```

2.  **Instalar Dependencias**:
    ```bash
    pip install --upgrade pip
    pip install -r requirements.txt
    ```

3.  **Instalar en modo Editable**:
    Esto permite reflejar cambios en el código sin reinstalar el paquete.
    ```bash
    pip install -e .
    ```

---

## ⚙️ Configuración Básica

El backend necesita un archivo `config.toml` en la raíz del repositorio (o variables de entorno).

1.  Copia el ejemplo:
    ```bash
    cp config.example.toml config.toml
    ```
2.  Edita `config.toml` según tus necesidades (ver [Referencia de Configuración](referencia_configuracion.md)).

---

## ⌨️ Comandos de Desarrollo

### Ejecución del Demonio
Para levantar el servidor IPC y ver logs en consola:

```bash
python -m v2m.main --daemon
```

### Comandos CLI
Puedes invocar funcionalidades directamente sin el socket:

```bash
# Transcribir un archivo WAV
python -m v2m.main transcribe grabacion.wav --model small

# Listar dispositivos de audio
python -m v2m.utils.audio_devices
```

### Calidad de Código (Linting)
Usamos **Ruff** como linter y formatter todo-en-uno.

```bash
# Verificar errores
ruff check .

# Corregir automáticamente
ruff check --fix .

# Formatear código
ruff format .
```

---

## 🧪 Testing

Tenemos una suite completa de pruebas unitarias e integración. Para detalles sobre cómo correrlas, mockear hardware y medir cobertura, consulta la **[Guía de Testing Detallada](testing.md)**.

Resumen rápido:
```bash
pytest tests/unit
```
