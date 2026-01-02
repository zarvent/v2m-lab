# 🛠️ Instalación y Configuración

Esta guía detalla los pasos necesarios para desplegar **Voice2Machine** en un entorno Linux. El proceso abarca dependencias del sistema, configuración del entorno Python y credenciales de IA.

---

## 1. Requisitos del Sistema

Antes de comenzar, asegúrate de tener instaladas las siguientes herramientas a nivel de sistema operativo. Estas son esenciales para la captura de audio y la gestión del portapapeles.

```bash
sudo apt update
sudo apt install ffmpeg xclip pactl python3-venv build-essential python3-dev
```

### Soporte para GPU (NVIDIA)
Para un rendimiento óptimo con Whisper, es **crítico** utilizar aceleración por GPU.
*   **Drivers NVIDIA**: Asegúrate de tener los últimos drivers instalados.
*   **CUDA Toolkit**: Necesario para `faster-whisper` y `torch`.

> **nota**: si no tienes GPU NVIDIA, funcionará en cpu pero será mucho más lento.

---

## 2. entorno python

Se recomienda encarecidamente utilizar un entorno virtual para aislar las dependencias del proyecto.

### Creación y Activación

```bash
# 1. Crear el entorno virtual en la raíz del proyecto
python3 -m venv venv

# 2. Activar el entorno
source venv/bin/activate
```

### Instalación de Dependencias

```bash
# 3. Instalar paquetes requeridos
pip install -r requirements.txt
```

---

## 3. Credenciales de IA (Google Gemini)

Para la funcionalidad de refinado de texto (`process-clipboard`), se requiere una API Key de Google Gemini.

1.  Obtén tu clave en [Google AI Studio](https://aistudio.google.com/).
2.  Crea un archivo `.env` en la raíz del proyecto.
3.  Añade tu clave siguiendo este formato:

```bash
echo 'GEMINI_API_KEY="tu_clave_api_aqui"' > .env
```

---

## 4. Verificación de la Instalación

Para confirmar que todos los componentes están correctamente configurados, ejecuta los scripts de diagnóstico incluidos.

### Verificar Dependencias y Audio
```bash
./scripts/verify-setup.sh
```

### Verificar Aceleración GPU
Este script cargará un modelo pequeño de Whisper para confirmar que `cuda` está disponible y funcional.
```bash
python scripts/test_whisper_gpu.py
```
