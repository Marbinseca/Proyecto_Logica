# Analizador de Lógica Proposicional con IA

[![Python Application CI](https://github.com/Marbinseca/Proyecto_Logica/actions/workflows/ci.yml/badge.svg)](https://github.com/Marbinseca/Proyecto_Logica/actions/workflows/ci.yml)

Una aplicación web interactiva construida con Flask y Google Gemini para interpretar, analizar y simplificar proposiciones lógicas.

 <!-- Reemplaza con una captura de pantalla real -->

## Descripción

Esta herramienta educativa está diseñada para ayudar a estudiantes y entusiastas de la lógica a trabajar con lógica proposicional. La aplicación aprovecha el poder de los modelos de lenguaje avanzados (Google Gemini) para realizar tareas complejas que van desde la interpretación del lenguaje natural hasta la simplificación de fórmulas.

## Características Principales

1.  **Intérprete Proposicional**:
    -   Convierte oraciones en lenguaje natural (español) a su forma simbólica en lógica proposicional.
    -   Identifica automáticamente las proposiciones atómicas y los conectores lógicos.
    -   Muestra una leyenda clara que asocia cada variable con su proposición.

2.  **Generador de Tablas de Verdad**:
    -   Crea tablas de verdad detalladas para cualquier fórmula simbólica.
    -   Muestra los valores de verdad para todas las sub-expresiones, facilitando el seguimiento paso a paso.
    -   Clasifica la fórmula final como **Tautología**, **Contradicción** o **Contingencia**.

3.  **Simplificador de Fórmulas**:
    -   Reduce expresiones lógicas complejas a su forma más simple.
    -   Muestra cada paso del proceso de simplificación, indicando la ley lógica aplicada (ej. Ley de De Morgan, Ley distributiva, etc.).

## Tecnologías Utilizadas

-   **Backend**: Python 3, Flask
-   **Inteligencia Artificial**: Google Gemini API (a través de peticiones REST)
-   **Frontend**: HTML5, CSS3, JavaScript
-   **Framework CSS**: Bootstrap 5
-   **Librerías Python**:
    -   `requests`: Para realizar llamadas a la API de Gemini.
    -   `python-dotenv`: Para gestionar las claves de API de forma segura.

## Instalación y Puesta en Marcha

Sigue estos pasos para ejecutar el proyecto en tu máquina local.

### Prerrequisitos

-   Python 3.8 o superior
-   Una clave de API de Google para Gemini. Puedes obtenerla en Google AI Studio.

### Pasos

1.  **Clona el repositorio:**
    ```bash
    git clone https://github.com/Marbinseca/Proyecto_Logica.git
    cd Proyecto_Logica
    ```

2.  **Crea y activa un entorno virtual:**
    -   En Windows:
        ```bash
        python -m venv venv
        .\venv\Scripts\activate
        ```
    -   En macOS/Linux:
        ```bash
        python3 -m venv venv
        source venv/bin/activate
        ```

3.  **Instala las dependencias:**
    Crea un archivo `requirements.txt` con el siguiente contenido:
    ```
    Flask
    requests
    python-dotenv
    google-generativeai
    sympy
    ```
    Luego, instálalo usando pip:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configura tu clave de API:**
    Crea un archivo llamado `.env` en la raíz del proyecto y añade tu clave de API de Google:
    ```
    GOOGLE_API_KEY="TU_CLAVE_DE_API_AQUI"
    ```

5.  **Ejecuta la aplicación Flask:**
    ```bash
    flask run
    ```

6.  **Abre la aplicación en tu navegador:**
    Visita http://127.0.0.1:5000 en tu navegador web.

## Uso

La interfaz web está dividida en tres secciones principales accesibles desde la barra lateral:

-   **Intérprete Proposicional**: Escribe una oración en el campo de texto y haz clic en "Convertir". La aplicación mostrará la fórmula simbólica y la leyenda correspondiente. Desde el resultado, puedes navegar directamente para generar su tabla de verdad o simplificar la fórmula.
-   **Tabla de Verdad**: Introduce una fórmula simbólica (ej. `(P ∧ Q) → P`) y haz clic en "Generar". Se mostrará la tabla completa y la clasificación de la fórmula.
-   **Simplificador**: Introduce una fórmula simbólica y haz clic en "Simplificar". Verás la fórmula simplificada y todos los pasos intermedios con las reglas lógicas aplicadas.

## Cómo Funciona la IA

A diferencia de los métodos tradicionales que dependen de un análisis sintáctico estricto, este proyecto delega las tareas lógicas a la API de Google Gemini.

Para cada funcionalidad (interpretar, tabular, simplificar), se construye un *prompt* detallado que instruye al modelo de IA sobre las reglas de la lógica proposicional y el formato de salida JSON esperado. La aplicación luego realiza una llamada a la API, recibe la respuesta estructurada en JSON y la presenta de manera amigable en la interfaz de usuario.

Este enfoque permite una gran flexibilidad en la interpretación del lenguaje natural y proporciona explicaciones detalladas en los procesos de simplificación.

## Ejecución de Pruebas

Este proyecto utiliza `pytest` para las pruebas unitarias. Para ejecutar las pruebas, asegúrate de haber instalado las dependencias y luego ejecuta el siguiente comando en la raíz del proyecto:

```bash
pytest
```

Las pruebas verificarán que todas las rutas de la aplicación respondan correctamente y que la lógica del controlador funcione como se espera, simulando las llamadas a la API de Gemini para no incurrir en costos ni depender de una conexión de red.


---