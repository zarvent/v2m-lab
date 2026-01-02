# UNIT TESTS

### qué es esta carpeta
esta carpeta contiene las **pruebas unitarias** del proyecto. las pruebas unitarias se centran en verificar el comportamiento de componentes individuales (funciones, métodos, clases) de forma aislada.

### para qué sirve
el objetivo es asegurar que cada pieza pequeña de lógica funcione correctamente por sí misma, sin depender de sistemas externos, bases de datos o red. esto permite:
*   ejecución rápida de pruebas (milisegundos).
*   localización precisa de errores.
*   documentación ejecutable del comportamiento esperado de cada componente.

### qué puedo encontrar aquí
*   `test_audio_recorder.py`: pruebas para la clase `AudioRecorder`.
*   `test_config.py`: pruebas para la carga y validación de configuración.
*   `test_vad_service.py`: pruebas para el servicio de detección de voz (VAD).
*   otros archivos `test_*.py` correspondientes a módulos específicos de `src/v2m`.

### cómo ejecutar estas pruebas
desde la raíz del proyecto:

```bash
# ejecutar todas las pruebas unitarias
pytest tests/unit

# ejecutar un archivo específico
pytest tests/unit/test_vad_service.py
```

### principios de diseño
*   **aislamiento**: usamos `unittest.mock` o `pytest-mock` para simular dependencias externas (como `sounddevice` o APIs).
*   **velocidad**: estas pruebas no deben realizar I/O real (disco, red).
*   **cobertura**: buscamos cubrir tanto el "happy path" como los casos de error y bordes.

### referencias
*   [documentación de pytest](https://docs.pytest.org/)
*   `tests/README.md` para la guía general de testing del proyecto.
