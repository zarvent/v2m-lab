# 🛠️ Instalación y Configuración

> **Prerrequisito**: Este proyecto está optimizado para **Linux (Debian/Ubuntu)**.
> **Estado del Arte 2026**: Utilizamos aceleración por hardware (CUDA) y un enfoque modular para garantizar privacidad y rendimiento.

Esta guía te llevará desde cero hasta un sistema de dictado completamente funcional en tu máquina local.

---

## 🚀 Método 1: Instalación Automática (Recomendado)

Hemos creado un script que maneja todo el "trabajo sucio" por ti: verifica tu sistema, instala dependencias (apt), crea el entorno virtual (venv) y configura las credenciales.

```bash
# Ejecutar desde la raíz del proyecto
./scripts/install.sh
```

**Lo que hace este script:**
1.  📦 Instala librerías del sistema (`ffmpeg`, `xclip`, `pulseaudio-utils`).
2.  🐍 Crea un entorno Python aislado (`venv`).
3.  ⚙️ Instala las dependencias del proyecto (`faster-whisper`, `torch`).
4.  🔑 Te ayuda a configurar tu API Key de Gemini (opcional, para IA generativa).
5.  🖥️ Verifica si tienes una GPU NVIDIA compatible.

---

## 🛠️ Método 2: Instalación Manual

Si prefieres tener el control total o el script automático falla, sigue estos pasos.

### 1. Dependencias del Sistema (System Level)

Necesitamos herramientas para manipular audio y el portapapeles a nivel del SO.

```bash
sudo apt update
sudo apt install ffmpeg xclip pulseaudio-utils python3-venv build-essential python3-dev
```

### 2. Entorno Python

Aislamos las librerías para evitar conflictos.

```bash
# Crear entorno virtual
python3 -m venv venv

# Activar entorno (¡Haz esto cada vez que trabajes en el proyecto!)
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

### 3. Configuración de IA (Opcional)

Para usar las funciones de "Refinado de Texto" (reescritura con LLM), necesitas una API Key de Google Gemini.

1.  Consigue tu clave en [Google AI Studio](https://aistudio.google.com/).
2.  Crea un archivo `.env` en la raíz:

```bash
echo 'GEMINI_API_KEY="tu_clave_api_aqui"' > .env
```

---

## ✅ Verificación

Asegúrate de que todo funciona antes de continuar.

**1. Verificar Aceleración GPU**
Esto confirma que Whisper puede usar tu tarjeta gráfica (esencial para velocidad).
```bash
python scripts/test_whisper_gpu.py
```

**2. Diagnóstico del Sistema**
Verifica que el demonio y los servicios de audio estén listos.
```bash
python scripts/verify_daemon.py
```

---

## ⏭️ Siguientes Pasos

Una vez instalado, es hora de configurar cómo interactúas con la herramienta.

- [Configuración Detallada](configuracion.md) - Ajusta modelos y sensibilidad.
- [Atajos de Teclado](atajos_teclado.md) - Configura tus teclas mágicas.
