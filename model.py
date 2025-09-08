# c:\Users\mseca\OneDrive\Documents\Proyecto_Logica\model.py
import os
import re
import json
import requests # Usaremos la librería requests para hacer la llamada a la API directamente
from dotenv import load_dotenv
from sympy.logic.boolalg import truth_table
from sympy import sympify, simplify_logic, symbols
import time
import hashlib
import logging
from threading import Lock
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

class SimpleCache:
    def __init__(self, maxsize=128, ttl=300):
        self.maxsize = maxsize
        self.ttl = ttl
        self.store = {}
        self.lock = Lock()

    def _prune(self):
        # remove expired entries, keep size under maxsize
        now = time.time()
        keys = list(self.store.keys())
        for k in keys:
            v, ts = self.store.get(k, (None, 0))
            if now - ts > self.ttl:
                self.store.pop(k, None)
        if len(self.store) > self.maxsize:
            # remove oldest
            items = sorted(self.store.items(), key=lambda x: x[1][1])
            for k, _ in items[: len(self.store) - self.maxsize]:
                self.store.pop(k, None)

    def get(self, key):
        with self.lock:
            self._prune()
            val = self.store.get(key)
            if val:
                return val[0]
            return None

    def set(self, key, value):
        with self.lock:
            self.store[key] = (value, time.time())
            self._prune()

# --- Carga de la Clave de API ---
# Carga las variables de entorno desde un archivo .env
load_dotenv()
API_KEY = os.environ.get("GOOGLE_API_KEY")
# Mantener compatibilidad: si existe variable con URL completa en env, usarla
ENV_API_URL = os.environ.get("GEMINI_API_URL")
DEFAULT_API_URL = ENV_API_URL or f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent"

class LogicaModelo:
    def __init__(self, api_base=None, api_key=None, *, max_workers=4, cache_ttl=300, cache_size=256, default_timeout=(5,20)):
        """Constructor optimizado: session con retries, pool de hilos y caché en memoria."""
        self.api_key = api_key or API_KEY
        self.api_base = api_base or DEFAULT_API_URL

        if not self.api_key and not os.environ.get("FLASK_RUN_FROM_CLI"):
            logger.warning("ADVERTENCIA: La clave de API de Google no se encontró en las variables de entorno.")

        # HTTP session with retries & connection pooling
        self._session = requests.Session()
        retries = Retry(
            total=3,
            backoff_factor=0.6,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=frozenset(['GET', 'POST', 'PUT', 'DELETE', 'HEAD', 'OPTIONS']),
            respect_retry_after_header=True
        )
        adapter = HTTPAdapter(pool_connections=10, pool_maxsize=20, max_retries=retries)
        self._session.mount("https://", adapter)
        self._session.mount("http://", adapter)

        # Thread pool to avoid blocking main thread on slow API calls
        self._executor = ThreadPoolExecutor(max_workers=max_workers)

        # Simple in-memory cache for repeated prompts
        self._cache = SimpleCache(maxsize=cache_size, ttl=cache_ttl)

        # Default request timeout (connect, read)
        self._timeout = default_timeout  # tuple (connect, read)

        # Default generation config to reduce latency (ajustable)
        self._default_generation_config = {
            "maxOutputTokens": 512,
            "temperature": 0.0,
            "topP": 0.95
        }

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

    def _cache_key(self, prompt, params):
        key_raw = json.dumps({"p": prompt, "params": params}, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(key_raw.encode("utf-8")).hexdigest()

    def _extract_json_substring(self, text):
        """
        Busca y extrae el primer bloque JSON válido dentro de text.
        Retorna el string JSON o lanza JSONDecodeError.
        """
        # Intento rápido: búsqueda de bloque que empieza en { y termina en matching }
        start = text.find('{')
        if start == -1:
            raise json.JSONDecodeError("No JSON start", text, 0)
        # Intentar encontrar el final buscando el cierre balanceado
        depth = 0
        for i in range(start, len(text)):
            ch = text[i]
            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    candidate = text[start:i+1]
                    # validar parseo
                    json.loads(candidate)
                    return candidate
        # última posibilidad: buscar con regex un bloque grande de JSON
        m = re.search(r'(\{[\s\S]*\})', text)
        if m:
            candidate = m.group(1)
            json.loads(candidate)
            return candidate
        raise json.JSONDecodeError("No se pudo extraer JSON válido", text, 0)

    def _send_gemini_request(self, payload, timeout=None):
        """
        Envia la petición a Gemini usando la session configurada.
        Devuelve el diccionario (parsed JSON response_data) o lanza Exception.
        """
        timeout = timeout or self._timeout
        headers = {"Content-Type": "application/json"}
        params = {}
        if self.api_key:
            # La API soporta key en query param; usarlo por compatibilidad
            params["key"] = self.api_key

        resp = self._session.post(self.api_base, headers=headers, json=payload, params=params, timeout=timeout)
        resp.raise_for_status()
        return resp.json()

    def _call_gemini_api(self, full_prompt, expect_json_response=False, generation_config_override=None, timeout_seconds=None):
        """
        Llama a Gemini de forma segura y devuelve (data_dict, error_str).
        Esta versión usa la session con retries, extrae JSON dentro del texto si es necesario y aplica generación config.
        """
        try:
            gen_cfg = dict(self._default_generation_config)
            if generation_config_override:
                gen_cfg.update(generation_config_override)

            payload = {
                "contents": [{"parts": [{"text": full_prompt}]}],
                "generationConfig": gen_cfg
            }
            if expect_json_response:
                # el mime-type ayuda al modelo a devolver JSON cuando está soportado
                payload["generationConfig"]["responseMimeType"] = "application/json"

            response_data = self._send_gemini_request(payload, timeout=(self._timeout[0], timeout_seconds or self._timeout[1]))

            # structure: response_data['candidates'][0]['content']['parts'][0]['text']
            candidates = response_data.get('candidates') or []
            if not candidates:
                error_info = response_data.get('promptFeedback') or response_data.get('validation') or 'Sin detalles adicionales.'
                logger.warning("Respuesta vacía de Gemini: %s", error_info)
                return None, "La IA devolvió una respuesta vacía o bloqueada."

            raw_text = candidates[0].get('content', {}).get('parts', [])[0].get('text', '')
            if not raw_text:
                logger.warning("Texto vacío en candidato de Gemini.")
                return None, "La IA devolvió una respuesta sin contenido."

            # Si el texto parece JSON limpio, parsear directo; si no, intentar extraer bloque JSON dentro del texto
            try:
                result = json.loads(raw_text)
                return result, None
            except (json.JSONDecodeError, ValueError):
                try:
                    json_sub = self._extract_json_substring(raw_text)
                    result = json.loads(json_sub)
                    return result, None
                except (json.JSONDecodeError, ValueError) as jerr:
                    logger.exception("Error al parsear JSON devuelto por Gemini: %s", jerr)
                    return None, "La IA devolvió una respuesta en un formato inesperado. Inténtalo de nuevo."

        except requests.exceptions.HTTPError as http_err:
            status = getattr(http_err.response, "status_code", None)
            logger.exception("HTTP error calling Gemini: %s", http_err)
            if status in (429, 503):
                msg = "La IA está recibiendo muchas solicitudes en este momento. Por favor, espera y vuelve a intentarlo."
                return None, msg
            try:
                error_details = http_err.response.json()
                api_message = error_details.get('error', {}).get('message', str(http_err))
            except Exception:
                api_message = str(http_err)
            return None, f"Error de la API de Gemini: {api_message}"
        except Exception as e:
            logger.exception("Error inesperado al llamar a Gemini: %s", e)
            return None, f"No se pudo procesar la petición con la IA. Error: {e}"

    def _request_with_cache_and_timeout(self, prompt, expect_json_response=False, timeout_seconds=20, use_cache=True, generation_config_override=None):
        """
        Coordinador: verifica caché, ejecuta la llamada en un hilo y aplica timeout.
        Retorna (data, error)
        """
        cache_key = self._cache_key(prompt, {"json": expect_json_response, "gen_cfg": generation_config_override or {}})
        if use_cache:
            cached = self._cache.get(cache_key)
            if cached is not None:
                logger.debug("Cache hit para prompt")
                return cached, None

        future = self._executor.submit(self._call_gemini_api, prompt, expect_json_response, generation_config_override, timeout_seconds)
        try:
            data, error = future.result(timeout=timeout_seconds + 2)  # pequeño margen
        except FutureTimeoutError:
            future.cancel()
            logger.warning("Llamada a IA excedió timeout de %s s", timeout_seconds)
            return None, f"Tiempo de espera agotado ({timeout_seconds}s) al consultar la IA."
        except Exception as e:
            logger.exception("Error en ejecución de hilo para llamada IA: %s", e)
            return None, f"Error interno al consultar la IA: {e}"

        if data is not None and use_cache:
            try:
                self._cache.set(cache_key, data)
            except Exception:
                logger.exception("Fallo al escribir en cache")

        return data, error

    def procesar_con_ia(self, texto, timeout_seconds=18, use_cache=True):
        """
        Usa un modelo de IA para procesar el texto.
        Devuelve: (formula_visual, leyenda, error)
        """
        if not self.api_key:
            return None, None, "Error de configuración: La clave de API de Google no está definida."

        full_prompt = self._get_system_prompt() + "\nOración: \"" + texto + "\"\nRespuesta JSON:"
        data, error = self._request_with_cache_and_timeout(full_prompt, expect_json_response=True, timeout_seconds=timeout_seconds, use_cache=use_cache)

        if error:
            return None, None, error

        formula = data.get("formula")
        leyenda = data.get("leyenda")

        if not formula or not leyenda:
            return None, None, "La respuesta de la IA no tuvo el formato esperado."

        return formula, leyenda, None

    def generar_tabla_verdad(self, formula_str, timeout_seconds=22, use_cache=True):
        """
        Genera una tabla de verdad para una fórmula simbólica dada usando IA.
        Devuelve: (header, rows, clasificacion, error)
        """
        if not self.api_key:
            return None, None, None, "Error de configuración: La clave de API de Google no está definida."

        full_prompt = self._get_truth_table_prompt() + "\nFórmula: \"" + formula_str + "\"\nRespuesta JSON:"
        data, error = self._request_with_cache_and_timeout(full_prompt, expect_json_response=True, timeout_seconds=timeout_seconds, use_cache=use_cache)

        if error:
            return None, None, None, error

        header = data.get("header")
        rows = data.get("rows")
        clasificacion = data.get("clasificacion")

        if header is None or rows is None or clasificacion is None:
            return None, None, None, "La respuesta de la IA no tuvo el formato esperado para la tabla de verdad."

        return header, rows, clasificacion, None

    def simplificar_formula(self, formula_str, timeout_seconds=20, use_cache=True):
        """
        Simplifica una fórmula lógica usando IA.
        Devuelve: (pasos, formula_simplificada, error)
        """
        if not self.api_key:
            return None, None, "Error de configuración: La clave de API de Google no está definida."

        full_prompt = self._get_simplification_prompt() + "\nFórmula: \"" + formula_str + "\"\nRespuesta JSON:"
        data, error = self._request_with_cache_and_timeout(full_prompt, expect_json_response=True, timeout_seconds=timeout_seconds, use_cache=use_cache)

        if error:
            return None, None, error

        pasos = data.get("pasos")
        formula_simplificada = data.get("formula_simplificada")

        if not formula_simplificada or not pasos:
            return None, None, "La respuesta de la IA no tuvo el formato esperado para la simplificación."

        return pasos, formula_simplificada, None

    def get_response(self, prompt, params=None, *, timeout_seconds=25, use_cache=True):
        """
        Método genérico público compatible con el anterior: mantiene compatibilidad.
        """
        params = params or {}
        cache_key = self._cache_key(prompt, params)

        if use_cache:
            cached = self._cache.get(cache_key)
            if cached is not None:
                logger.debug("Cache hit for prompt")
                return cached

        future = self._executor.submit(self._call_gemini_api, prompt, False, None, timeout_seconds)
        try:
            result, error = future.result(timeout=timeout_seconds + 2)
        except FutureTimeoutError:
            future.cancel()
            logger.warning("AI call timed out after %s seconds", timeout_seconds)
            raise TimeoutError(f"AI call timed out after {timeout_seconds}s")
        except Exception as e:
            logger.exception("AI call raised an exception")
            raise

        if error:
            logger.warning("AI returned error: %s", error)
            raise RuntimeError(error)

        if use_cache and result is not None:
            try:
                self._cache.set(cache_key, result)
            except Exception:
                logger.exception("Failed to set cache")

        return result

    # Optionally add a graceful shutdown helper
    def shutdown(self):
        try:
            self._executor.shutdown(wait=False)
            self._session.close()
        except Exception:
            pass