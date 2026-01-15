---
source:
  - docs/docs/en/development.md
---

# Guía de Desarrollo Backend

Instrucciones para configurar el entorno de desarrollo y contribuir al daemon de Voice2Machine.

## 🛠️ Configuración Inicial

### Entorno Virtual

Se recomienda el uso de `venv` con Python 3.12:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

### Configuración (config.toml)

El backend busca un archivo `config.toml` en la raíz del proyecto para definir el modelo de Whisper (ej. `large-v3-turbo`) y las claves de API para LLMs.

## ⌨️ Comandos de Desarrollo

### Ejecución

- **Daemon**: `python -m v2m.main --daemon`
- **CLI**: `python -m v2m.main transcribe file.wav`

### Calidad (Ruff)

Estamos comprometidos con el estándar SOTA 2026.

- **Chequeo**: `ruff check .`
- **Formateo**: `ruff format .`

### Pruebas (Pytest)

- **Todas**: `pytest`
- **Unitarias**: `pytest tests/unit`
- **Con cobertura**: `pytest --cov=v2m`

## 🧪 Estrategia de Testing

1.  **Mocks Rigurosos**: Nunca llamar a hardware real (Micrófono) o APIs externas en tests unitarios. Usar los protocolos de `domain/` para inyectar mocks.
2.  **Tests de Integración**: Prueban que los adaptadores reales funcionan con el daemon, idealmente en entornos controlados de CI/CD con soporte para GPU si es posible.
