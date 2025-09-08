# c:\Users\mseca\OneDrive\Documents\Proyecto_Logica\model.py
import os
import re
import json
import requests # Usaremos la librería requests para hacer la llamada a la API directamente
from dotenv import load_dotenv
from sympy.logic.boolalg import truth_table
from sympy import sympify, simplify_logic, symbols

# --- Carga de la Clave de API ---
# Carga las variables de entorno desde un archivo .env
load_dotenv()
API_KEY = os.environ.get("GOOGLE_API_KEY")
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={API_KEY}"

class LogicaModelo:
    def __init__(self):
        """El constructor ahora está vacío. No necesitamos inicializar ningún modelo complejo."""
        if not API_KEY and not os.environ.get("FLASK_RUN_FROM_CLI"): # Evita el mensaje durante los comandos de Flask
            print("ADVERTENCIA: La clave de API de Google no se encontró en las variables de entorno.")

    def _get_system_prompt(self):
        """Define las instrucciones para el modelo de IA."""
        return """
        Eres un experto en lógica proposicional. Tu tarea es convertir una oración en lenguaje natural a su forma simbólica.
        Sigue estas reglas estrictamente:
        1.  Identifica las proposiciones atómicas en la oración.
        2.  Asigna una variable proposicional (P, Q, R, etc.) a cada proposición atómica única.
        3.  Si una proposición está negada (ej. "no vi la película"), la proposición atómica es la forma afirmativa ("vi la película").
        4.  Reconoce los conectores lógicos y sus sinónimos:
            - 'y', 'pero', 'aunque' se traducen a '∧'.
            - 'o' se traduce a '∨'.
            - 'si...entonces' o 'si..., ...' se traducen a '→'.
            - 'si y solo si' se traduce a '↔'.
            - 'no' se traduce a '¬'.
        5.  Construye la fórmula simbólica final.
        6.  Devuelve el resultado en un formato JSON VÁLIDO, sin ningún texto adicional antes o después. El JSON debe tener dos claves: "formula" y "leyenda".
            - "formula": Un string con la expresión simbólica.
            - "leyenda": Un objeto donde cada clave es una variable (P, Q, ...) y su valor es la proposición atómica correspondiente en su forma afirmativa.

        Ejemplo 1:
        Oración: "si no estuvieras loca, no habrías venido aquí"
        Respuesta JSON:
        {
          "formula": "¬ P → ¬ Q",
          "leyenda": {
            "P": "estuvieras loca",
            "Q": "habrías venido aquí"
          }
        }

        Ejemplo 2:
        Oración: "vi la pelicula aunque no lei la novela"
        Respuesta JSON:
        {
          "formula": "P ∧ ¬ Q",
          "leyenda": {
            "P": "vi la pelicula",
            "Q": "lei la novela"
          }
        }
        """

    def _get_truth_table_prompt(self):
        """Define las instrucciones para que la IA genere una tabla de verdad."""
        return """
        Eres un experto en lógica proposicional. Tu tarea es generar una tabla de verdad detallada para una fórmula simbólica dada, mostrando todos los pasos intermedios.
        Sigue estas reglas estrictamente:
        1.  Identifica las variables proposicionales (P, Q, R, etc.) en la fórmula.
        2.  Identifica todas las sub-fórmulas de la expresión, desde las más simples hasta la más compleja (la fórmula completa).
        3.  Calcula todas las combinaciones de valores de verdad (Usa 'V' para verdadero y 'F' para falso).
        4.  Evalúa el valor de verdad para cada sub-fórmula y para la fórmula completa en cada combinación.
        5.  Clasifica la fórmula final como "Tautología", "Contradicción" o "Contingencia".
        6.  Devuelve el resultado en un formato JSON VÁLIDO, sin ningún texto adicional antes o después. El JSON debe tener tres claves: "header", "rows" y "clasificacion".
            - "header": Una lista de strings con los nombres de las columnas. Debe incluir primero las variables, luego todas las sub-fórmulas en orden de complejidad, y finalmente la fórmula completa.
            - "rows": Una lista de listas, donde cada sublista representa una fila de la tabla con los valores 'V' o 'F'.
            - "clasificacion": Un string que puede ser "Tautología", "Contradicción" o "Contingencia".

        Ejemplo 1:
        Fórmula: "(P ∧ Q) → P"
        Respuesta JSON:
        {
          "header": ["P", "Q", "P ∧ Q", "(P ∧ Q) → P"],
          "rows": [
            ["V", "V", "V", "V"],
            ["V", "F", "F", "V"],
            ["F", "V", "F", "V"],
            ["F", "F", "F", "V"]
          ],
          "clasificacion": "Tautología"
        }

        Usa los siguientes símbolos en la fórmula del header:
        - Conjunción: ∧
        - Disyunción: ∨
        - Negación: ¬
        - Condicional: →
        - Bicondicional: ↔
        """

    def _get_simplification_prompt(self):
        """Define las instrucciones para que la IA simplifique una fórmula lógica."""
        return """
        Eres un experto en lógica proposicional y álgebra booleana. Tu tarea es simplificar una fórmula lógica dada, mostrando cada paso del proceso.

        Sigue estas reglas estrictamente:
        1.  Analiza la fórmula de entrada.
        2.  Aplica las leyes de equivalencia lógica (De Morgan, distributiva, asociativa, negación, identidad, etc.) una por una para reducir la fórmula.
        3.  El objetivo es obtener la fórmula lógicamente equivalente más corta.
        4.  Devuelve el resultado en un formato JSON VÁLIDO, sin ningún texto adicional antes o después. El JSON debe tener dos claves: "pasos" y "formula_simplificada".
            - "formula_simplificada": Un string con la expresión simbólica final.
            - "pasos": Una lista de objetos, donde cada objeto representa un paso de la simplificación y tiene dos claves: "formula" y "regla".

        Ejemplo 1:
        Fórmula: "(P ∧ Q) ∨ (P ∧ ¬Q)"
        Respuesta JSON:
        {
          "pasos": [
            {
              "formula": "(P ∧ Q) ∨ (P ∧ ¬Q)",
              "regla": "Fórmula original"
            },
            {
              "formula": "P ∧ (Q ∨ ¬Q)",
              "regla": "Ley distributiva"
            },
            {
              "formula": "P ∧ V",
              "regla": "Ley de negación (Q ∨ ¬Q ≡ V)"
            },
            {
              "formula": "P",
              "regla": "Ley de identidad (P ∧ V ≡ P)"
            }
          ],
          "formula_simplificada": "P"
        }

        Usa los siguientes símbolos en la fórmula de salida:
        - Conjunción: ∧
        - Disyunción: ∨
        - Negación: ¬
        - Condicional: →
        - Bicondicional: ↔
        """

    def _call_gemini_api(self, full_prompt, expect_json_response=False):
        """
        Método auxiliar centralizado para realizar llamadas a la API de Gemini.
        Maneja la construcción de la petición, la llamada HTTP y la gestión de errores comunes.

        Args:
            full_prompt (str): El prompt completo a enviar al modelo.
            expect_json_response (bool): Si es True, configura la API para que devuelva JSON.

        Returns:
            tuple: Una tupla (datos_dict, error_str).
                   - datos_dict (dict): Los datos decodificados de JSON si la llamada es exitosa.
                   - error_str (str): Un mensaje de error si ocurre algún problema.
        """
        try:
            payload = {"contents": [{"parts": [{"text": full_prompt}]}]}
            if expect_json_response:
                payload["generationConfig"] = {"responseMimeType": "application/json"}

            headers = {"Content-Type": "application/json"}

            response = requests.post(API_URL, headers=headers, json=payload)
            response.raise_for_status()

            response_data = response.json()

            if 'candidates' not in response_data or not response_data['candidates']:
                error_info = response_data.get('promptFeedback', 'Sin detalles adicionales.')
                return None, f"La API devolvió una respuesta vacía o bloqueada. Causa: {error_info}"

            json_text = response_data['candidates'][0]['content']['parts'][0]['text']
            
            # Limpieza adicional para el caso en que la IA no respete el mime-type y envuelva en markdown
            if json_text.strip().startswith("```json"):
                json_text = json_text.strip()[7:-3].strip()

            data = json.loads(json_text)
            return data, None

        except requests.exceptions.HTTPError as http_err:
            # Manejo de errores específico para sobrecarga de la API
            if http_err.response.status_code in [429, 503]:
                user_friendly_message = "La IA está recibiendo muchas solicitudes en este momento. Por favor, espera un momento y vuelve a intentarlo."
                print(f"Error de sobrecarga de la API (código {http_err.response.status_code}): {user_friendly_message}")
                return None, user_friendly_message

            error_details = http_err.response.json()
            api_message = error_details.get('error', {}).get('message', 'Error desconocido de la API.')
            print(f"Error HTTP al llamar a la API: {http_err}\nDetalles: {api_message}")
            return None, f"Error de la API de Gemini: {api_message}" # Mantenemos el mensaje original para otros errores HTTP
        except (json.JSONDecodeError, ValueError) as json_err:
            print(f"Error al decodificar JSON de la API: {json_err}")
            return None, "La IA devolvió una respuesta en un formato inesperado. Inténtalo de nuevo."
        except Exception as e:
            print(f"Error inesperado al llamar a la API: {e}")
            return None, f"No se pudo procesar la petición con la IA. Error: {e}"

    def procesar_con_ia(self, texto):
        """
        Usa un modelo de IA para procesar el texto.
        Devuelve: (formula_visual, leyenda, error)
        """
        if not API_KEY:
            return None, None, "Error de configuración: La clave de API de Google no está definida."

        full_prompt = self._get_system_prompt() + "\nOración: \"" + texto + "\"\nRespuesta JSON:"
        data, error = self._call_gemini_api(full_prompt, expect_json_response=False)

        if error:
            return None, None, error

        formula = data.get("formula")
        leyenda = data.get("leyenda")

        if not formula or not leyenda:
            return None, None, "La respuesta de la IA no tuvo el formato esperado."

        return formula, leyenda, None

    def generar_tabla_verdad(self, formula_str):
        """
        Genera una tabla de verdad para una fórmula simbólica dada usando IA.
        Devuelve: (header, rows, clasificacion, error)
        """
        if not API_KEY:
            return None, None, None, "Error de configuración: La clave de API de Google no está definida."

        full_prompt = self._get_truth_table_prompt() + "\nFórmula: \"" + formula_str + "\"\nRespuesta JSON:"
        data, error = self._call_gemini_api(full_prompt, expect_json_response=True)

        if error:
            return None, None, None, error

        header = data.get("header")
        rows = data.get("rows")
        clasificacion = data.get("clasificacion")

        if not all([header, rows, clasificacion is not None]):
            return None, None, None, "La respuesta de la IA no tuvo el formato esperado para la tabla de verdad."

        return header, rows, clasificacion, None

    def simplificar_formula(self, formula_str):
        """
        Simplifica una fórmula lógica usando IA.
        Devuelve: (pasos, formula_simplificada, error)
        """
        if not API_KEY:
            return None, None, "Error de configuración: La clave de API de Google no está definida."

        full_prompt = self._get_simplification_prompt() + "\nFórmula: \"" + formula_str + "\"\nRespuesta JSON:"
        data, error = self._call_gemini_api(full_prompt, expect_json_response=True)

        if error:
            return None, None, error

        pasos = data.get("pasos")
        formula_simplificada = data.get("formula_simplificada")

        if not formula_simplificada or not pasos:
            return None, None, "La respuesta de la IA no tuvo el formato esperado para la simplificación."

        return pasos, formula_simplificada, None