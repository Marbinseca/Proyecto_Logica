# Proyecto_Logica

[![Python Application CI](https://github.com/Marbinseca/Proyecto_Logica/actions/workflows/ci.yml/badge.svg)](https://github.com/Marbinseca/Proyecto_Logica/actions/workflows/ci.yml)


Proyecto_Logica es una herramienta educativa para trabajar con lógica proposicional. Permite:
- Convertir enunciados en lenguaje natural a notación simbólica.
- Insertar símbolos lógicos desde la interfaz en páginas editables.
- Generar tablas de verdad, simplificar fórmulas y verificar equivalencias.
- Consultar leyes y reglas de inferencia (página de solo lectura).

Principales páginas (rutas)
- /                → Intérprete (texto → símbolos)
- /simbolo_a_texto  → Símbolos → Texto (símbolos → oración en español)
- /tabla-verdad     → Generar tabla de verdad
- /simplificar      → Simplificar fórmula
- /equivalencia     → Verificar equivalencia
- /leyes-logicas    → Referencia (solo lectura)
- /acerca-de        → Información del proyecto

Instalación rápida (entorno Windows)
1. Crear y activar virtualenv:
   python -m venv .venv
   .venv\Scripts\activate

2. Instalar dependencias:
   pip install -r requirements.txt

3. Copiar variables de entorno:
   ren .env.example .env
   (editar .env y añadir la clave si aplica)

4. Ejecutar la aplicación en desarrollo:
   set FLASK_APP=controller.py
   flask run

Notas importantes
- CSRF: la aplicación usa Flask-WTF/CSRFProtect. Asegúrate de que los formularios POST incluyan el token CSRF ({{ csrf_token }} o {{ form.hidden_tag() }}).
- Scripts front-end: static/js/symbol_inserter.js debe estar presente y cargarse en las plantillas que permiten edición. Si los botones de símbolo no funcionan, revisa la consola del navegador por errores JS y que el input objetivo tenga data-default-target="true" o tenga foco.
- API/IA: si usas integración con una API externa, añade la clave en .env (GOOGLE_API_KEY o GEMINI_API_URL) según configuración.

Estructura relevante
- controller.py        — Rutas y controladores Flask
- model.py             — Lógica y wrappers para llamadas a IA / sympy
- templates/           — Plantillas Jinja2 (view.html, simbolo_a_texto.html, leyes_logicas.html, etc.)
- static/js/           — symbol_inserter.js, app.js
- requirements.txt     — Dependencias Python

Contribuciones y mejoras
- Abrir issues o crear pull requests en el repositorio local.
- Mantener tests (si se añaden) y revisar compatibilidad de sympy al actualizar versión.

Contacto
- Proyecto local: revisa los archivos en la carpeta del proyecto para ajustes internos.