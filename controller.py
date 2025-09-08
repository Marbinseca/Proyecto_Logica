# c:\Users\mseca\OneDrive\Documents\Proyecto_Logica\controller.py
from flask import Flask, render_template, request, flash
from flask_wtf import CSRFProtect, FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import re
import os
from model import LogicaModelo

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

if __name__ == "__main__":
    app.run(debug=True)