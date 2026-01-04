"""Pruebas unitarias del sistema de configuración.

Propósito
---------
Verificar que el módulo de configuración cargue correctamente los valores
desde config.toml y los exponga de manera consistente a través de Settings.

Contexto técnico
----------------
La configuración en v2m sigue el patrón de "configuración externa":
los parámetros de la aplicación (modelo de ML, idioma, timeouts, etc.)
se definen en un archivo separado (config.toml), no en el código fuente.

Ventajas de este enfoque:
    * Separación de concerns: El código no conoce valores específicos.
    * Flexibilidad: Cambiar comportamiento sin recompilar/redesplegar.
    * Ambientes múltiples: Diferentes configs para dev/staging/prod.

Este archivo verifica
---------------------
    * Que config.toml se parsee correctamente.
    * Que los valores críticos tengan los defaults esperados.
    * Que la estructura jerárquica (whisper.model, gemini.retry_attempts)
      se mapee correctamente al objeto Settings.

Estrategia de testing
---------------------
Usamos assertions directas contra valores conocidos del config.toml
actual. Si estos valores cambian, las pruebas fallarán intencionalmente
para alertar sobre el cambio de configuración.

Nota importante:
    Estas pruebas son "contract tests" - verifican el contrato entre
    config.toml y el código que lo consume. Si necesitas cambiar un
    valor en config.toml, actualiza también estas pruebas.

Ejecución
---------
    >>> pytest tests/unit/test_config.py -v
"""

import pytest
from v2m.config import Settings


def test_config_loading() -> None:
    """Verifica la carga correcta de parámetros desde config.toml.

    Caso de prueba
    --------------
    Instanciar Settings y validar que los valores críticos coincidan
    con los definidos en config.toml.

    Valores verificados
    -------------------
    whisper.model = "large-v3-turbo"
        Modelo de transcripción. "large-v3-turbo" ofrece balance óptimo
        entre precisión y velocidad para uso en producción.

    whisper.language = "auto"
        Modo de detección automática de idioma. Whisper analizará el
        audio para determinar el idioma hablado.

    gemini.retry_attempts = 3
        Número de reintentos ante fallos de la API de Gemini. El valor 3
        sigue la práctica común de "three strikes" antes de fallar
        definitivamente.

    Metodología
    -----------
    Este test sigue el patrón de "smoke test" o "sanity check":
    verifica que los componentes básicos funcionen antes de ejecutar
    pruebas más complejas.

    Returns:
        None. Los tests en pytest no retornan valores; comunican
        resultados mediante assertions y excepciones.

    Raises:
        AssertionError: Si algún valor de configuración no coincide
            con el esperado. Esto indica que config.toml fue modificado
            o hay un problema en el parser de configuración.

    Example:
        >>> config = Settings()
        >>> config.whisper.model
        'large-v3-turbo'
    """
    config = Settings()

    # Validación del modelo de Whisper
    # large-v3-turbo: 6x más rápido que large-v3 con calidad comparable
    # NOTE: Access via transcription.whisper since whisper field is deprecated/default only
    assert config.transcription.whisper.model == "large-v3-turbo", (
        f"Modelo inesperado: {config.transcription.whisper.model}. "
        "¿Se modificó config.toml sin actualizar este test?"
    )

    # Validación del idioma
    # "auto" = detección automática mediante análisis espectral
    assert config.transcription.whisper.language == "auto", (
        f"Idioma inesperado: {config.transcription.whisper.language}. "
        "El valor debe ser 'auto' para detección automática."
    )

    # Validación de política de reintentos
    # 3 reintentos: práctica estándar en sistemas distribuidos
    assert config.gemini.retry_attempts == 3, (
        f"Reintentos inesperados: {config.gemini.retry_attempts}. "
        "El valor recomendado es 3 para balancear resiliencia y latencia."
    )


def test_ollama_config_defaults() -> None:
    """Verifica defaults de OllamaConfig para structured outputs.

    Valores verificados
    -------------------
    ollama.model = "gemma2:2b"
        Modelo optimizado para grammar correction, cabe en 4GB VRAM.

    ollama.keep_alive = "5m"
        Balance entre consumo de VRAM y latencia. Mantiene modelo
        cargado 5 minutos después del último uso.

    ollama.temperature = 0.0
        Determinístico para structured outputs con JSON schema.
    """
    config = Settings()

    assert config.llm.ollama.model == "gemma2:2b", (
        f"Modelo Ollama inesperado: {config.llm.ollama.model}. "
        "El default debe ser 'gemma2:2b' para grammar correction."
    )

    assert config.llm.ollama.keep_alive == "5m", (
        f"keep_alive inesperado: {config.llm.ollama.keep_alive}. "
        "El default debe ser '5m' para balance VRAM/latencia."
    )

    assert config.llm.ollama.temperature == 0.0, (
        f"Temperatura inesperada: {config.llm.ollama.temperature}. "
        "Debe ser 0.0 para structured outputs determinísticos."
    )
