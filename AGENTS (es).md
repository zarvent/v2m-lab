# Voice2Machine (V2M)

Herramienta local-first de dictado por voz que convierte speech-to-text usando GPU local (Whisper) con post-procesamiento opcional por LLM (Gemini).

---

## Comandos de Setup

```bash
# Backend (Python)
cd apps/backend && source venv/bin/activate
pip install -e .                       # instalar paquete

# Frontend (Tauri + React)
cd apps/frontend
npm install                            # instalar dependencias
npm run tauri dev                      # iniciar servidor de desarrollo
```

## Comandos de Build y Test

```bash
# Backend - seguros para auto-ejecutar
pytest -v                              # ejecutar todos los tests
pytest --cov=src/v2m tests/            # con coverage
ruff check src/ --fix                  # lint y auto-fix
ruff format src/                       # formatear código

# Frontend - seguros para auto-ejecutar
npm run build                          # build TypeScript + Vite
npm run tauri build                    # build de producción

# Scripts de sistema
scripts/v2m-daemon.sh start            # iniciar daemon
scripts/v2m-daemon.sh stop             # detener daemon
scripts/v2m-toggle.sh                  # toggle grabación
scripts/v2m-llm.sh                     # refinar con Gemini
```

---

## Tech Stack

### Backend (`apps/backend`)

- **Python 3.12+** con type hints estrictos
- **Librerías core**: `faster-whisper`, `sounddevice`, `pydantic`, `google-genai`
- **Linting**: `ruff` (estricto, 120 chars/línea)
- **Testing**: `pytest` con modo asyncio

### Frontend (`apps/frontend`)

- **Tauri v2** (core en Rust) + **React v19**
- **TypeScript** modo estricto
- **Vite v7** para bundling
- **CSS Modules** (estética minimalista)

### Infraestructura (`scripts`)

- **OS objetivo**: Linux (basado en Debian)
- **Herramientas de sistema**: `xclip` (portapapeles), `notify-send` (notificaciones)

---

## Estructura del Proyecto

```
v2m/
├── apps/
│   ├── backend/
│   │   ├── src/v2m/
│   │   │   ├── core/           # contenedor DI, Command Bus
│   │   │   ├── domain/         # interfaces, entidades, errores
│   │   │   ├── application/    # command handlers
│   │   │   └── infrastructure/ # implementaciones Whisper, Audio, Gemini
│   │   ├── tests/              # tests unitarios e integración
│   │   ├── prompts/            # prompts para LLM
│   │   └── config.toml         # configuración de la app
│   │
│   └── frontend/
│       ├── src/                # componentes React
│       └── src-tauri/          # backend en Rust
│
├── scripts/                    # scripts bash para orquestación
│   ├── v2m-daemon.sh           # servicio en background
│   ├── v2m-toggle.sh           # trigger de grabación
│   └── v2m-llm.sh              # trigger de refinamiento LLM
│
└── docs/                       # documentación técnica
    └── arquitectura.md         # decisiones de arquitectura y diagramas
```

---

## Estilo de Código

### Python

- siempre usar type hints estrictos para todos los argumentos y valores de retorno
- seguir configuración de `ruff` en `pyproject.toml`
- usar excepciones específicas del dominio (ej: `MicrophoneNotFoundError`)
- ejecutar `ruff check --fix` y `ruff format` antes de commitear

```python
# ✅ correcto - types estrictos, nombres descriptivos, manejo de errores
async def transcribir_audio(audio_path: Path, modelo: str = "large-v3") -> Transcripcion:
    if not audio_path.exists():
        raise ArchivoAudioNoEncontradoError(f"archivo no encontrado: {audio_path}")
    return await whisper_service.transcribir(audio_path, modelo)

# ❌ incorrecto - sin types, nombres vagos, sin manejo de errores
async def proc(p):
    return await ws.t(p)
```

### TypeScript/React

- modo estricto de TypeScript es obligatorio
- botones con solo icono DEBEN tener `aria-label`
- banners de error DEBEN usar `role="alert"` y `aria-live="assertive"`
- modales DEBEN cerrarse con tecla `Escape`
- usar `React.memo`, `useCallback`, `useMemo` para prevenir re-renders innecesarios

```typescript
// ✅ correcto - aria-label, memo, manejo de teclado
const BotonGrabar: React.FC<Props> = React.memo(({ onToggle, grabando }) => (
  <button
    onClick={onToggle}
    onKeyDown={(e) => e.key === "Escape" && onToggle()}
    aria-label={grabando ? "detener grabación" : "iniciar grabación"}
  >
    {grabando ? "⏹️" : "🎙️"}
  </button>
));

// ❌ incorrecto - sin aria-label, sin memo
const BotonMal = ({ onClick }) => <button onClick={onClick}>🎙️</button>;
```

---

## Reglas de Arquitectura

Este proyecto sigue **Arquitectura Hexagonal** (Puertos y Adaptadores):

- la lógica de negocio en `core/` y `domain/` NUNCA debe importar de `infrastructure/`
- las dependencias fluyen hacia adentro: Infrastructure → Application → Domain → Core
- usar inyección de dependencias para intercambiar implementaciones

---

## Instrucciones de Testing

1. ejecutar tests unitarios para el módulo específico que modificaste:
   - `pytest tests/unit/ -v`
2. ejecutar tests de integración si modificaste infraestructura:
   - `pytest tests/integration/ -v`
3. verificar que la aceleración GPU funciona:
   - `python scripts/test_whisper_gpu.py`
4. verificar salud del daemon:
   - `python scripts/verify_daemon.py`

siempre agregar o actualizar tests para el código que cambies, aunque no se solicite explícitamente.

---

## Consideraciones de Seguridad

- **NUNCA** commitear API keys o secrets (usar archivos `.env`, ya están en `.gitignore`)
- **NUNCA** hardcodear paths absolutos (usar archivos de config o variables de entorno)
- **NUNCA** modificar `venv/`, `node_modules/` o archivos generados
- los datos de audio se procesan solo localmente—nunca se transmiten externamente sin acción explícita del usuario
- el procesamiento LLM (Gemini) solo ocurre cuando el usuario activa explícitamente `v2m-llm.sh`

---

## Flujo de Git

```bash
# crear rama de feature
git checkout -b feature/nombre-descriptivo

# antes de commitear, siempre ejecutar
ruff check apps/backend/src/ --fix
ruff format apps/backend/src/
cd apps/frontend && npm run build     # verificar TypeScript

# formato de mensaje de commit
git commit -m "feat(backend): agregar soporte para modelo whisper-turbo"
# tipos: feat, fix, docs, style, refactor, test, chore
# scopes: backend, frontend, scripts, docs
```

---

## Boundaries

### ✅ siempre hacer

- seguir arquitectura hexagonal (core/domain nunca importan infrastructure)
- escribir tests para nueva funcionalidad
- usar type hints estrictos en Python y TypeScript
- validar con `ruff` y `tsc` antes de commit
- mantener documentación en `docs/` sincronizada

### ⚠️ preguntar primero

- cambios al schema de config (`config.toml`)
- agregar nuevas dependencias
- modificar scripts de sistema (`scripts/v2m-*.sh`)
- cambios que afecten pipeline de audio

### 🚫 nunca hacer

- commitear secrets o API keys
- modificar `venv/`, `node_modules/` o archivos generados
- hardcodear paths absolutos
- romper separación de capas de arquitectura hexagonal
- eliminar tests que fallan sin autorización

---

## Recursos de Verificación

- `scripts/test_whisper_gpu.py` — verificar aceleración GPU
- `scripts/verify_daemon.py` — verificar estado del daemon
- `scripts/health_check.py` — diagnóstico completo del sistema
- `scripts/diagnose_audio.py` — diagnóstico de dispositivos de audio
- `scripts/check_cuda.py` — verificar configuración CUDA

---

## Documentación

- `docs/arquitectura.md` — decisiones de arquitectura y diagramas de flujo
- `apps/backend/README.md` — setup y uso del backend
- `apps/frontend/README.md` — setup y uso del frontend
- `scripts/README.md` — documentación de scripts de sistema

---

## Nota sobre Monorepo

los archivos `AGENTS.md` anidados están soportados. coloca instrucciones específicas de paquete en subdirectorios, y el `AGENTS.md` más cercano tomará precedencia para ese contexto.
