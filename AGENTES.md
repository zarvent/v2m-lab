# Voice2Machine (V2M) - Instrucciones para Agentes

> **Contexto**: Estás trabajando en un proyecto de Arquitectura Hexagonal (Backend Python + Frontend Tauri).
> **Objetivo**: Mantener estándares de calidad de código "State of the Art 2026". Alta cohesión, bajo acoplamiento, deuda técnica cero.

---

## 📚 Gobernanza de Documentación (SOTA 2026)

### Docs as Code
*   **Fuente de Verdad**: La documentación técnica vive en `docs/docs/es/`. `mkdocs.yml` define la estructura del sitio.
*   **Sincronización**: Todo PR que cambie funcionalidad (código) **DEBE** incluir la actualización correspondiente en la documentación.
*   **README**: `README.md` (Inglés) y `LEEME.md` (Español) deben mantenerse sincronizados y apuntar a la documentación detallada.

### Estándares de Calidad
1.  **Accesibilidad (WCAG 2.1 AA)**:
    *   Usa `alt text` descriptivo en todas las imágenes.
    *   Mantén jerarquía estricta de encabezados (H1 > H2 > H3).
    *   Usa bloques de código con especificación de lenguaje.
2.  **Estructura**:
    *   **Exploración**: Qué es y por qué usarlo.
    *   **Procedimientos**: Guías paso a paso (How-to).
    *   **Referencia**: APIs, Configuración, Comandos.
    *   **Conceptos**: Arquitectura, decisiones de diseño (ADRs).
3.  **Idioma**:
    *   Documentación detallada (`docs/`): **Español Latinoamericano Nativo**.
    *   Comentarios de código: **Español Latinoamericano Nativo**.
    *   Commits: Inglés (Conventional Commits).

---

## 🧠 Filosofía Core

1.  **Local-First**: La privacidad es suprema. El audio nunca sale de la máquina.
2.  **Modular**: El Demonio es el núcleo. La GUI y los Scripts son solo clientes.
3.  **Hexagonal**: Las dependencias apuntan hacia adentro. El `Dominio` no sabe nada de la `Infraestructura`.

---

## 🛠️ Herramientas y Comandos

### Documentación
*   **Servir localmente**: `mkdocs serve`

### Backend (Python 3.12+)
*   **Ejecutar**: `python -m v2m.main --daemon`
*   **Test**: `pytest tests/` (Unitarios: `tests/unit`, Integración: `tests/integration`)
*   **Lint**: `ruff check src/ --fix` (Reglas estrictas habilitadas)
*   **Format**: `ruff format src/`

### Frontend (Tauri 2 + React 19)
*   **Dev**: `npm run tauri dev`
*   **Build**: `npm run tauri build`
*   **Check**: `tsc --noEmit`

### Scripts
*   **Instalar**: `./scripts/install.sh` (Idempotente)
*   **Verificar**: `python scripts/verify_daemon.py`

---

## 🏗️ Guías de Arquitectura

### Estructura de Directorios
```
apps/backend/src/v2m/
├── core/           # Contenedor DI, Event Bus (CQRS)
├── domain/         # Entidades, Puertos (Protocolos), Errores
├── application/    # Command Handlers (Casos de Uso)
└── infrastructure/ # Implementaciones Concretas (Whisper, SoundDevice)
```

### Reglas
1.  **Interfaces en Dominio/Aplicación**: Usa `typing.Protocol` con `@runtime_checkable` en lugar de `abc.ABC` para desacoplamiento estructural.
2.  **Sin "God Classes"**: Divide responsabilidades (ej. `AudioRecorder` vs `TranscriptionService`).
3.  **Type Hints**: Cobertura 100% requerida.
4.  **AsyncIO**: El núcleo es asíncrono. No bloquees el event loop (usa `asyncio.to_thread` o ejecutores dedicados para tareas de CPU/GPU intensivas).

---

## 🧪 Estrategia de Testing

1.  **Unit Tests**: Mockea toda la infraestructura. Testea la lógica en `application/`.
2.  **Integration Tests**: Testea infraestructura real (GPU, Audio) en scripts aislados o `tests/integration/`.
3.  **Golden Rule**: Si arreglas un bug, añade un test que lo reproduzca.

---

## 🚨 Errores Comunes

- **Rutas Hardcodeadas**: NUNCA uses rutas absolutas como `/home/user`. Usa `v2m.utils.paths.get_secure_runtime_dir`.
- **Bloquear el Loop**: No uses `time.sleep()`. Usa `await asyncio.sleep()`.
- **Git Commits**: Use Conventional Commits (`feat:`, `fix:`, `refactor:`).

---

## 🤖 Contexto IA
Al generar código:
- Prefiere **Pydantic V2** para validación de datos.
- Usa manejo de errores robusto (Jerarquía `ApplicationError`).
- Asume un contexto de **CUDA 12** para operaciones GPU.
- **Idioma**: Toda la documentación y comentarios deben estar en Español Latinoamericano Nativo.
