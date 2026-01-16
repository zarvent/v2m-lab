---
source:
  - docs/docs/es/index.md
---
# Backend de Voice2Machine

El backend de Voice2Machine es el "cerebro" del sistema, encargado de la captura de audio, transcripción mediante modelos locales y procesamiento de lenguaje natural. Está diseñado bajo principios de **arquitectura hexagonal** (puertos y adaptadores) para garantizar la modularidad y flexibilidad.

## 🚀 Filosofía

1.  **Privacidad por Diseño (Local-First)**: El procesamiento de audio nunca sale de la máquina del usuario. No hay telemetría ni envío de datos a nubes externas sin consentimiento explícito.
2.  **Desempeño Asíncrono (AsyncIO)**: Diseñado para ser no bloqueante, permitiendo que la interfaz de usuario permanezca fluida mientras se realizan tareas pesadas de inferencia.
3.  **Modularidad Extrema**: Los motores de IA (Whisper, Gemini, LLMs locales) son adaptadores intercambiables que implementan protocolos definidos en el dominio.

## 🛠️ Stack Tecnológico

- **Lenguaje**: [Python 3.12+](https://www.python.org/)
- **Validación de Datos**: [Pydantic V2](https://docs.pydantic.dev/latest/)
- **Inferencia de Audio**: [Faster-Whisper](https://github.com/SYSTRAN/faster-whisper)
- **Procesamiento LLM**: Google GenAI (Gemini) y adaptadores para modelos locales.
- **Manejo de Audio**: [SoundDevice](https://python-sounddevice.readthedocs.io/) y NumPy.
- **Calidad de Código**: [Ruff](https://docs.astral.sh/ruff/) y [Pytest](https://docs.pytest.org/).

## 🏛️ Estructura del Proyecto

```
apps/backend/src/v2m/
├── domain/         # Entidades, errores y protocolos (Interfaces)
├── application/    # Casos de uso y lógica de negocio
├── infrastructure/ # Implementaciones concretas (Adapters)
├── core/           # Bus de eventos, Inyección de dependencias y Logs
└── main.py         # Punto de entrada CLI/Daemon
```

## 📚 Documentación Técnica Detallada

*   [**Arquitectura**](arquitectura.md): Visión general de las capas y flujo de datos.
*   [**Referencia API IPC**](referencia_api_ipc.md): Protocolo de comunicación socket con el Frontend.
*   [**Referencia de Configuración**](referencia_configuracion.md): Detalles de `config.toml` y variables de entorno.
*   [**Componentes Internos**](componentes_internos.md): Deep dive en servicios (Whisper, VAD, Rust).
*   [**Guía de Testing**](testing.md): Estrategias de prueba y mocking.
*   [**Guía de Desarrollo**](desarrollo.md): Setup y comandos básicos.
*   [**Gestión del Demonio**](gestion_demonio.md): Ciclo de vida y troubleshooting del proceso principal.
*   [**Estándares de Código**](estandares.md): Convenciones de estilo y calidad.
