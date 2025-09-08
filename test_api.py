# test_api.py
import os
import google.generativeai as genai
import pytest
from dotenv import load_dotenv

def test_gemini_api_connection():
    """
    Esta prueba verifica que podemos conectarnos a la API de Gemini y obtener una respuesta.
    Utiliza la clave de API de las variables de entorno.
    """
    print("--- Iniciando prueba de conexión a la API de Gemini ---")

    # Cargar la clave de API desde el archivo .env o variables de entorno del CI
    load_dotenv()
    api_key = os.environ.get("GOOGLE_API_KEY")

    # pytest.fail detendrá la prueba si la clave no está presente.
    if not api_key:
        pytest.fail("ERROR: No se encontró la variable de entorno GOOGLE_API_KEY.")

    # La prueba fallará si hay una excepción durante la configuración o la llamada.
    # No es necesario un bloque try/except, pytest lo maneja.
    genai.configure(
        api_key=api_key, transport='rest',
        client_options={'api_endpoint': 'generativelanguage.googleapis.com'}
    )
    model = genai.GenerativeModel('gemini-1.0-pro')

    print("Enviando solicitud a Gemini...")
    response = model.generate_content("Explica qué es una API en una oración.")

    assert response.text, "La API de Gemini devolvió una respuesta vacía."
    print(f"Respuesta de Gemini recibida: {response.text}")
