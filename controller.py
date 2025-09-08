# c:\Users\mseca\OneDrive\Documents\Proyecto_Logica\controller.py
from flask import Flask, render_template, request, flash, redirect, url_for
from flask_wtf import CSRFProtect, FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import re
import os
from model import LogicaModelo
from flask_wtf.csrf import generate_csrf

app = Flask(__name__)
# Configuración de seguridad para CSRF
app.config['SECRET_KEY'] = os.urandom(24)
csrf = CSRFProtect(app)

logica_modelo = LogicaModelo()

# Asegúrate de tener sympy instalado: pip install sympy

@app.route("/", methods=["GET", "POST"])
def index():
    proposicion_simbolica = ""
    leyenda = None
    error = None
    # Aunque el formulario es simple, usar Flask-WTF nos da protección CSRF
    # y una mejor estructura.
    class ProposicionForm(FlaskForm):
        proposicion = StringField('Proposición', validators=[DataRequired()])
        submit = SubmitField('Convertir')

    form = ProposicionForm()

    if form.validate_on_submit():
        proposicion_texto = form.proposicion.data
        if proposicion_texto:
            # Usamos el nuevo método basado en IA
            proposicion_simbolica, leyenda, error = logica_modelo.procesar_con_ia(proposicion_texto)
    
    # El controlador pasa el resultado a la vista para ser mostrado
    return render_template("view.html", form=form, resultado=proposicion_simbolica, leyenda=leyenda, error=error)

@app.route("/tabla-verdad", methods=["GET", "POST"])
def tabla_verdad():
    class FormulaForm(FlaskForm):
        formula = StringField('Fórmula', validators=[DataRequired(message="Por favor, introduce una fórmula.")])
        submit = SubmitField('Generar Tabla')

    form = FormulaForm()
    tabla_header = None
    tabla_rows = None
    clasificacion = None
    error = None
    formula_input = request.args.get('formula') # Para enlaces GET

    if form.validate_on_submit(): # Es un POST válido con CSRF
        formula_to_process = form.formula.data
        tabla_header, tabla_rows, clasificacion, error = logica_modelo.generar_tabla_verdad(formula_to_process)
        formula_input = formula_to_process # Para mostrarla de nuevo en el campo
    elif request.method == 'GET' and formula_input:
        # Es un GET con una fórmula en la URL
        form.formula.data = formula_input
        tabla_header, tabla_rows, clasificacion, error = logica_modelo.generar_tabla_verdad(formula_input)

    return render_template("tabla_verdad.html", form=form, tabla_header=tabla_header, tabla_rows=tabla_rows, clasificacion=clasificacion, error=error, formula_input=formula_input)

@app.route("/simplificar", methods=["GET", "POST"])
def simplificar():
    class FormulaForm(FlaskForm):
        formula = StringField('Fórmula', validators=[DataRequired(message="Por favor, introduce una fórmula.")])
        submit = SubmitField('Simplificar')

    form = FormulaForm()
    formula_input = request.args.get('formula') # Para enlaces GET
    pasos_simplificacion = None
    formula_simplificada = None
    error = None
    
    if form.validate_on_submit(): # Es un POST válido con CSRF
        formula_input = form.formula.data
        pasos_simplificacion, formula_simplificada, error = logica_modelo.simplificar_formula(formula_input)
    elif request.method == 'GET' and formula_input:
        # Es un GET con una fórmula en la URL
        form.formula.data = formula_input
        pasos_simplificacion, formula_simplificada, error = logica_modelo.simplificar_formula(formula_input)

    return render_template("simplificar.html", form=form, formula_input=formula_input, pasos=pasos_simplificacion, formula_simplificada=formula_simplificada, error=error)

@app.route("/equivalencia", methods=["GET", "POST"])
def equivalencia():
    """Verifica si dos fórmulas lógicas son equivalentes."""
    class EquivalenciaForm(FlaskForm):
        formula_a = StringField('Fórmula A', validators=[DataRequired(message="Introduce la primera fórmula.")])
        formula_b = StringField('Fórmula B', validators=[DataRequired(message="Introduce la segunda fórmula.")])
        submit = SubmitField('Verificar Equivalencia')

    form = EquivalenciaForm()
    resultado_equivalencia = None
    error = None
    
    if form.validate_on_submit():
        formula_a = form.formula_a.data
        formula_b = form.formula_b.data
        
        # Creamos la fórmula bicondicional para probar la equivalencia
        formula_bicondicional = f"({formula_a}) \u2194 ({formula_b})" # \u2194 es ↔
        
        _, _, clasificacion, err = logica_modelo.generar_tabla_verdad(formula_bicondicional)
        
        if err:
            error = err
        elif clasificacion == "Tautología":
            resultado_equivalencia = True
        else:
            resultado_equivalencia = False
            
    return render_template("equivalencia.html", form=form, resultado=resultado_equivalencia, error=error)

@app.route("/acerca-de")
def acerca_de():
    """Muestra la página 'Acerca de'."""
    return render_template("acerca_de.html")

@app.route("/leyes-logicas")
def leyes_logicas():
    """Muestra una página con la explicación de las leyes lógicas."""
    return render_template("leyes_logicas.html")

# Añadir esta ruta para la nueva página "Símbolos -> Texto"
@app.route('/simbolo_a_texto', methods=['GET', 'POST'])
def simbolo_a_texto():
    resultado = None
    leyenda = None
    error = None

    if request.method == 'POST':
        formula = request.form.get('formula', '').strip()
        leyenda_text = request.form.get('legend', '').strip()

        if not formula:
            error = "Introduce una fórmula en símbolos."
        else:
            # Parsear leyenda si el usuario la proporcionó (formato: "P: Juan come...")
            leyenda = {}
            if leyenda_text:
                for line in leyenda_text.splitlines():
                    if ':' in line:
                        k, v = line.split(':', 1)
                        leyenda[k.strip()] = v.strip()

            # Si no hay leyenda, generamos frases de ejemplo para las variables encontradas
            import re
            vars_found = sorted(set(re.findall(r'\b[A-Z]\b', formula)))
            ejemplo_frases = [
                "Juan come en el restaurante",
                "María viste una camisa roja",
                "Pedro estudia en la universidad",
                "El equipo ganó el partido",
                "La habitación está iluminada",
                "El motor funciona correctamente",
                "La puerta está cerrada",
                "El correo fue enviado"
            ]
            for i, v in enumerate(vars_found):
                if v not in leyenda:
                    leyenda[v] = ejemplo_frases[i % len(ejemplo_frases)]

            # Función simple para convertir fórmula simbólica a oración en español
            def expr_to_text(expr):
                expr = expr.strip()
                # Negación: ¬X or ~X
                expr = re.sub(r'¬\s*([A-Z])', lambda m: f"no {leyenda.get(m.group(1), m.group(1))}", expr)
                expr = re.sub(r'~\s*([A-Z])', lambda m: f"no {leyenda.get(m.group(1), m.group(1))}", expr)
                # Paréntesis: procesar recursivamente es complejo; se hace reemplazo simple
                # Implicación: A → B  -> "Si A, entonces B"
                if '→' in expr or '->' in expr:
                    parts = re.split(r'\s*(?:→|->)\s*', expr, maxsplit=1)
                    left = parts[0]
                    right = parts[1] if len(parts) > 1 else ''
                    left_text = expr_to_text(left)
                    right_text = expr_to_text(right)
                    return f"Si {left_text}, entonces {right_text}"
                # Bicondicional
                if '↔' in expr or '<->' in expr:
                    parts = re.split(r'\s*(?:↔|<->)\s*', expr, maxsplit=1)
                    a = expr_to_text(parts[0])
                    b = expr_to_text(parts[1] if len(parts) > 1 else '')
                    return f"{a} si y solo si {b}"
                # Conjunción y Disyunción: manejar operadores binarios de forma lineal
                # Reemplazar variables sueltas por su frase
                # Primero reemplazar conjunción y disyunción por conectores en español
                # Manejar conjunción
                if '∧' in expr or '&' in expr:
                    parts = re.split(r'\s*(?:∧|&)\s*', expr)
                    parts_text = [expr_to_text(p) for p in parts]
                    return ' y '.join(parts_text)
                # Manejar disyunción
                if '∨' in expr or 'v' in expr or '\\/' in expr:
                    parts = re.split(r'\s*(?:∨|v|\\\/)\s*', expr)
                    parts_text = [expr_to_text(p) for p in parts]
                    return ' o '.join(parts_text)
                # Si es solo una variable, devolver la frase de la leyenda
                m = re.match(r'^\s*([A-Z])\s*$', expr)
                if m:
                    return leyenda.get(m.group(1), m.group(1))
                # Si queda algo más complejo, intentar reemplazar variables dentro del texto
                def replace_var(match):
                    sym = match.group(0)
                    return leyenda.get(sym, sym)
                return re.sub(r'\b[A-Z]\b', replace_var, expr)

            try:
                resultado = expr_to_text(formula)
            except Exception as e:
                error = "No se pudo convertir la fórmula. Revisa la sintaxis."
    # generar token CSRF y pasarlo a la plantilla
    csrf_token = generate_csrf()
    return render_template('simbolo_a_texto.html', resultado=resultado, leyenda=leyenda, error=error, csrf_token=csrf_token)

if __name__ == "__main__":
    app.run(debug=True)