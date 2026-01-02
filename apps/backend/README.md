# Backend Voice2Machine (Python Core)

El "cerebro" del sistema. Encargado de la lógica de negocio, procesamiento de audio e inferencia de IA.

## 🚀 Quick Start (Dev Mode)

Si ya ejecutaste `install.sh` en la raíz, todo esto está listo. Para desarrollo manual:

```bash
# 1. Activar entorno virtual
cd apps/backend
source venv/bin/activate

# 2. Instalar dependencias en modo editable (útil para dev)
pip install -e .

# 3. Lanzar el Daemon (Servidor)
# Esto mantendrá el proceso vivo escuchando en /tmp/v2m.sock
python -m v2m.main --daemon
```

## 🏗️ Comandos de Desarrollo

Utilizamos herramientas modernas para garantizar calidad de código.

### Testing (Pytest)
```bash
# Tests unitarios rápidos
pytest tests/unit/

# Tests de integración (requiere GPU/Audio)
pytest tests/integration/
```

### Linting & Formatting (Ruff)
Usamos `ruff` (el linter más rápido del oeste) para reemplazar a flake8, isort y black.

```bash
# Check y autofix
ruff check src/ --fix

# Formateo
ruff format src/
```

## 📦 Estructura del Proyecto

```
apps/backend/
├── src/v2m/
│   ├── application/    # Casos de uso (Commands/Handlers)
│   ├── core/           # Bus de comandos y configuración global
│   ├── domain/         # Entidades puras y excepciones
│   ├── infrastructure/ # Implementaciones reales (Whisper, Gemini, Audio)
│   └── main.py         # Entrypoint
├── config.toml         # Configuración por defecto
└── pyproject.toml      # Configuración de build y herramientas
```

## 🔌 API de Sockets

El backend expone un Socket Unix en `/tmp/v2m.sock`.

**Protocolo:**
1.  **Header**: 4 bytes (Big Endian) indicando la longitud del mensaje.
2.  **Body**: JSON string codificado en UTF-8.

*Ejemplo de mensaje:* `{"type": "toggle_recording"}`
