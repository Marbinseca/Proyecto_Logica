import pytest
from unittest.mock import patch
from controller import app

@pytest.fixture
def client():
    """Configura la aplicación Flask para pruebas."""
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False  # Desactiva CSRF para pruebas de formularios
    with app.test_client() as client:
        yield client

def test_index_get(client):
    """Prueba que la página principal (Intérprete) se cargue correctamente."""
    response = client.get('/')
    assert response.status_code == 200
    # Usamos b'' para buscar bytes en la respuesta
    assert b'Int\xc3\xa9rprete de L\xc3\xb3gica Proposicional' in response.data

@patch('model.LogicaModelo.procesar_con_ia')
def test_index_post_success(mock_procesar, client):
    """Prueba el envío de una proposición al intérprete con una respuesta exitosa."""
    # Simulamos una respuesta exitosa del modelo
    mock_procesar.return_value = ('P ∧ Q', {'P': 'llueve', 'Q': 'hace frio'}, None)
    
    response = client.post('/', data={'proposicion': 'llueve y hace frio'})
    
    assert response.status_code == 200
    assert b'P \xe2\x88\xa7 Q' in response.data  # P ∧ Q
    assert b'<strong>P:</strong> Llueve' in response.data
    mock_procesar.assert_called_once_with('llueve y hace frio')

@patch('model.LogicaModelo.procesar_con_ia')
def test_index_post_error(mock_procesar, client):
    """Prueba el envío de una proposición al intérprete con un error del modelo."""
    # Simulamos una respuesta con error del modelo
    mock_procesar.return_value = (None, None, 'Error de la IA')
    
    response = client.post('/', data={'proposicion': 'texto invalido'})
    
    assert response.status_code == 200
    assert b'Error de la IA' in response.data
    mock_procesar.assert_called_once_with('texto invalido')

def test_tabla_verdad_get(client):
    """Prueba que la página de Tabla de Verdad se cargue correctamente."""
    response = client.get('/tabla-verdad')
    assert response.status_code == 200
    assert b'Generador de Tablas de Verdad' in response.data

@patch('model.LogicaModelo.generar_tabla_verdad')
def test_tabla_verdad_post(mock_generar, client):
    """Prueba la generación de una tabla de verdad."""
    mock_generar.return_value = (['P', 'Q'], [['V', 'V']], 'Contingencia', None)
    
    response = client.post('/tabla-verdad', data={'formula': 'P ∧ Q'})
    
    assert response.status_code == 200
    assert b'Contingencia' in response.data
    # Hacemos la aserción más flexible para ignorar espacios o atributos adicionales en la etiqueta.
    # Buscamos que el contenido 'P' esté dentro de una etiqueta <th>.
    assert b'<th scope="col">P</th>' in response.data
    mock_generar.assert_called_once_with('P ∧ Q')

def test_simplificar_get(client):
    """Prueba que la página de Simplificador se cargue correctamente."""
    response = client.get('/simplificar')
    assert response.status_code == 200
    assert b'Simplificador de F\xc3\xb3rmulas L\xc3\xb3gicas' in response.data

@patch('model.LogicaModelo.simplificar_formula')
def test_simplificar_post(mock_simplificar, client):
    """Prueba la simplificación de una fórmula."""
    pasos = [{'formula': 'P ∧ V', 'regla': 'Ley de negación'}]
    mock_simplificar.return_value = (pasos, 'P', None)
    
    response = client.post('/simplificar', data={'formula': 'P ∧ (Q ∨ ¬Q)'})
    
    assert response.status_code == 200
    assert b'F\xc3\xb3rmula Simplificada Final' in response.data
    assert b'Ley de negaci\xc3\xb3n' in response.data
    assert b'P' in response.data
    mock_simplificar.assert_called_once_with('P ∧ (Q ∨ ¬Q)')

def test_acerca_de_get(client):
    """Prueba que la página 'Acerca de' se cargue correctamente."""
    response = client.get('/acerca-de')
    assert response.status_code == 200
    assert b'Acerca del Analizador L\xc3\xb3gico' in response.data

def test_leyes_logicas_get(client):
    """Prueba que la página 'Leyes Lógicas' se cargue correctamente."""
    response = client.get('/leyes-logicas')
    assert response.status_code == 200
    assert b'Gu\xc3\xada de Leyes L\xc3\xb3gicas' in response.data