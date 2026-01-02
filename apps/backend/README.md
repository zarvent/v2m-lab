# Backend Voice2Machine

## Instalación Rápida

```bash
# 1. Crear entorno virtual
python3 -m venv venv

# 2. Instalar dependencias
venv/bin/pip install -r requirements.txt

# 3. Configurar API key (opcional, para LLM cloud)
cp .env.example .env
# Editar .env con tu GEMINI_API_KEY

# 4. Ejecutar daemon
PYTHONPATH=src venv/bin/python3 -m v2m.main --daemon
```

## Notas de Portabilidad

- **El venv DEBE recrearse** si mueves el proyecto a otra ubicación o PC
- Las rutas se auto-detectan relativas al proyecto
- Requisitos: Python 3.12+, GPU NVIDIA con CUDA (opcional pero recomendado)

## Estructura

```
apps/backend/
├── src/v2m/          # Código fuente principal
├── tests/            # Tests
├── config.toml       # Configuración
├── requirements.txt  # Dependencias Python
└── venv/             # Entorno virtual (no versionado)
```

## Dependencias del Sistema (Linux)

```bash
sudo apt install ffmpeg xclip pulseaudio-utils python3-venv build-essential python3-dev
```
