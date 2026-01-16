# Guía de Testing del Backend

En Voice2Machine, el testing automatizado es fundamental para asegurar la estabilidad del sistema, especialmente dado que interactuamos con hardware (Micrófono, GPU) y modelos de IA pesados.

## 🧪 Estrategia de Pruebas

Seguimos la pirámide de testing clásica:

1.  **Unitarias (`tests/unit`)**: Rápidas (<1s), aisladas, mocks para todo I/O.
2.  **Integración (`tests/integration`)**: Validan la interacción entre componentes reales (ej. IPC -> Handler -> Service).
3.  **E2E (End-to-End)**: Prueban el sistema completo (usualmente desde el frontend o scripts de QA).

---

## 🛠️ Herramientas

*   **Runner**: `pytest`
*   **Plugins**:
    *   `pytest-asyncio`: Para probar corrutinas `async def`.
    *   `pytest-mock`: Wrapper sobre `unittest.mock`.
    *   `pytest-cov`: Reportes de cobertura.

---

## 🏃 Ejecutando Tests

### Todo el conjunto
Desde `apps/backend`:
```bash
pytest
```

### Solo Unitarios (Rápidos)
```bash
pytest tests/unit
```

### Con Reporte de Cobertura
```bash
pytest --cov=v2m --cov-report=term-missing
```

---

## 🎭 Mocking de Hardware y Servicios

Dado que no podemos depender de que el entorno de CI tenga una GPU NVIDIA o un micrófono conectado, **debemos** mockear estas dependencias en los tests unitarios.

### Ejemplo: Mockear Whisper

No queremos cargar el modelo de 3GB en un test unitario.

```python
from unittest.mock import AsyncMock
from v2m.domain.interfaces import TranscriptionService

async def test_transcription_flow(mocker):
    # 1. Crear Mock que cumpla la interfaz
    mock_service = AsyncMock(spec=TranscriptionService)
    mock_service.stop_and_transcribe.return_value = "Hola Mundo"

    # 2. Inyectar Mock en el handler/caso de uso
    handler = TranscribeAudioHandler(service=mock_service)

    # 3. Ejecutar
    result = await handler.handle()

    # 4. Verificar
    assert result == "Hola Mundo"
    mock_service.stop_and_transcribe.assert_called_once()
```

### Mockear Audio (PyAudio/SoundDevice)

El código de infraestructura de audio debe ser probado simulando streams de datos binarios, no intentando abrir un dispositivo real.

---

## 🚧 Tests de Integración

Estos tests pueden requerir configuración especial. En CI, se saltan automáticamente si no se detectan las credenciales o el hardware necesario.

Marcadores comunes en `pytest.ini`:
*   `@pytest.mark.gpu`: Requiere GPU NVIDIA.
*   `@pytest.mark.slow`: Tarda más de 5 segundos.
*   `@pytest.mark.requires_api_key`: Requiere claves externas (Gemini/OpenAI).

Para correrlos localmente:
```bash
pytest -m "gpu"
```
