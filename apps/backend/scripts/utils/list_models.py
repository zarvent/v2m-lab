#!/usr/bin/env python3

"""
ver modelos de gemini disponibles

¿para qué sirve?
    te muestra todos los modelos de gemini ai que puedes usar
    con tu api key útil para
    - verificar que tu api key funciona
    - ver qué modelos tienes disponibles
    - elegir qué modelo usar en config.toml

¿cómo lo uso?
    $ python scripts/list_models.py

¿qué voy a ver?
    Available models:
    models/gemini-1.5-pro        <- El más potente
    models/gemini-1.5-flash      <- Rápido y económico (recomendado)
    models/gemini-pro            <- Versión anterior

¿qué modelo debería usar?
    para v2m recomendamos gemini-1.5-flash
    - es rápido (importa para dictado)
    - es económico (si pagas por uso)
    - calidad suficiente para corrección de texto

¿me sale error de api key?
    1 verifica que tengas un archivo .env en la raíz del proyecto
    2 que contenga gemini_api_key=tu-clave-aqui
    3 sin espacios alrededor del =
"""

import google.generativeai as genai
import os
from dotenv import load_dotenv


def list_available_models() -> None:
    """
    muestra los modelos de gemini que puedes usar

    lee tu api key del archivo .env y consulta a google qué modelos
    tienes disponibles solo muestra los que sirven para generar texto
    """
    load_dotenv()

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        api_key = os.getenv("GOOGLE_API_KEY")

    if not api_key:
        print("GEMINI_API_KEY or GOOGLE_API_KEY not found in environment variables.")
    else:
        genai.configure(api_key=api_key)
        print("Available models:")
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(m.name)


if __name__ == "__main__":
    list_available_models()
