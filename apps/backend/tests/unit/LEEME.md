# UNIT TESTS

### ¿Qué es esta carpeta?

Esta carpeta contiene las **pruebas unitarias** del proyecto. Las pruebas unitarias se centran en verificar el comportamiento de componentes individuales (funciones, métodos, clases) de forma aislada.

### ¿Para qué sirve?

El objetivo es asegurar que cada pieza pequeña de lógica funcione correctamente por sí misma, sin depender de sistemas externos, bases de datos o red. Esto permite:

- Ejecución rápida de pruebas (milisegundos).
- Localización precisa de errores.
- Documentación ejecutable del comportamiento esperado de cada componente.

### ¿Qué puedo encontrar aquí?

- `test_audio_recorder.py`: Pruebas para la clase `AudioRecorder`.
- `test_config.py`: Pruebas para la carga y validación de configuración.
- `test_vad_service.py`: Pruebas para el servicio de detección de voz (VAD).
- Otros archivos `test_*.py` correspondientes a módulos específicos de `src/v2m`.

### Cómo ejecutar estas pruebas

Desde la raíz del proyecto:

```bash
# ejecutar todas las pruebas unitarias
pytest tests/unit

# ejecutar un archivo específico
pytest tests/unit/test_vad_service.py
```

### Principios de diseño

- **Aislamiento**: Usamos `unittest.mock` o `pytest-mock` para simular dependencias externas (como `sounddevice` o APIs).
- **Velocidad**: Estas pruebas no deben realizar I/O real (disco, red).
- **Cobertura**: Buscamos cubrir tanto el "happy path" como los casos de error y bordes.

### Referencias

- [Documentación de pytest](https://docs.pytest.org/)
- `tests/README.md` para la guía general de testing del proyecto.
