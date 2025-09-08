# test_api.py
import os
import google.generativeai as genai
from dotenv import load_dotenv

print("--- Iniciando prueba de API de Gemini ---")

# Cargar la clave de API desde el archivo .env
load_dotenv()
api_key = os.environ.get("GOOGLE_API_KEY")

if not api_key:
    print("ERROR: No se encontró la variable de entorno GOOGLE_API_KEY.")
else:
    try:
        # Configurar la API (igual que en tu model.py)
        genai.configure(
            api_key=api_key, transport='rest',
            client_options={'api_endpoint': 'generativelanguage.googleapis.com'}
        )

        # Crear el modelo
        model = genai.GenerativeModel('gemini-1.0-pro')

        # Hacer una pregunta simple
        print("Enviando solicitud a Gemini...")
        response = model.generate_content("Explica qué es una API en una oración.")

        print("\n--- ¡ÉXITO! ---")
        print("Respuesta de Gemini:")
        print(response.text)

    except Exception as e:
        print("\n--- ¡FALLO! ---")
        print("Se produjo un error al contactar con la API:")
        print(e)

print("\n--- Fin de la prueba ---")
