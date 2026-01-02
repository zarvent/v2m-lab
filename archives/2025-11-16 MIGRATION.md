# Migración de Perplexity a Gemini

## Fecha: 16 de Noviembre, 2025

## Resumen de Cambios

Se ha migrado el sistema de procesamiento de texto desde **Perplexity Sonar API** a **Google Gemini API** debido a cambios en el funcionamiento de Perplexity Sonar.

## Cambios Principales

### 1. Archivo `.env`
- ✅ Reemplazado `PERPLEXITY_API_KEY` con `GEMINI_API_KEY`
- ✅ Actualizado `LLM_PROVIDER` de "perplexity" a "gemini"
- ✅ Cambiado `LLM_MODEL` a "models/gemini-2.5-flash"

### 2. Archivo `llm_processor.py`
- ✅ Reemplazada la librería `requests` con el SDK oficial `google-genai`
- ✅ Renombrada la clase `PerplexityProcessor` a `GeminiProcessor`
- ✅ Adaptado el método `refine()` para usar la API de Gemini
- ✅ Mantenida la misma interfaz pública y comportamiento

### 3. Archivo `requirements.txt`
- ✅ Agregado: `google-genai>=0.3.0`
- ✅ Confirmado: `python-dotenv>=1.0.0`
- ✅ Confirmado: `tenacity>=8.2.0`

### 4. Entorno Virtual
- ✅ Creado entorno virtual en `.venv/`
- ✅ Instaladas todas las dependencias necesarias

## Configuración Actual

```bash
GEMINI_API_KEY=".................."
LLM_PROVIDER="gemini"
LLM_MODEL="models/gemini-2.5-flash"
LLM_TEMPERATURE="0.3"
```

## Modelos Disponibles

Los siguientes modelos de Gemini están disponibles:
- `models/gemini-2.5-flash` (Recomendado - rápido y eficiente)
- `models/gemini-2.5-pro` (Más potente, más lento)
- `models/gemini-2.0-flash` (Versión anterior)
- `models/gemini-2.0-pro-exp` (Experimental)

## Uso

### Con el entorno virtual:
```bash
echo "Tu texto aquí" | .venv/bin/python3 llm_processor.py
```

### Desde otros scripts:
```bash
# Asegúrate de activar el entorno virtual primero
source .venv/bin/activate
python3 llm_processor.py "Tu texto aquí"
```

## Pruebas Realizadas

✅ Instalación de dependencias
✅ Conexión con la API de Gemini
✅ Procesamiento de texto simple
✅ Manejo de errores y reintentos

## Notas Importantes

1. **Entorno Virtual**: Se recomienda usar el entorno virtual `.venv/` para evitar conflictos con paquetes del sistema
2. **API Key**: La API key está configurada en el archivo `.env` (no la compartas públicamente)
3. **Límites de Cuota**: Gemini tiene límites de cuota gratuita. Si excedes, considera cambiar a un modelo con mejor cuota o esperar
4. **Compatibilidad**: La interfaz del script se mantiene igual, por lo que los scripts que lo usan no necesitan cambios

## Próximos Pasos

- [ ] Actualizar scripts shell (`process-clipboard.sh`, `whisper-toggle.sh`) para usar el entorno virtual
- [ ] Considerar agregar más configuraciones personalizables
- [ ] Documentar el prompt del sistema en `prompts/refine_system.txt`
