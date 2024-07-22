from flask import Flask, request, jsonify, render_template
import re
import ply.lex as lex
from flask_cors import CORS  # Importar CORS

app = Flask(__name__)
CORS(app)  # Configurar CORS para permitir solicitudes desde cualquier origen

# Lista de nombres de tokens
tokens = ['COLLECTION', 'DOCUMENT', 'ID', 'NUM', 'SYM', 'STR', 'ERR']

# Definiciones de los tokens
t_COLLECTION = r'\b(collection)\b'
t_DOCUMENT = r'\b(document)\b'
t_ID = r'\b[a-zA-Z_][a-zA-Z_0-9]*\b'
t_NUM = r'\b\d+\b'
t_SYM = r'[;,*=<>!+-/*]'
t_STR = r'\'[^\']*\''
t_ERR = r'.'

def t_error(t):
    print(f"Carácter ilegal '{t.value[0]}'")
    t.lexer.skip(1)

lexer = lex.lex()

def analyze_lexical(code):
    results = {'COLLECTION': 0, 'DOCUMENT': 0, 'ID': 0, 'NUM': 0, 'STR': 0, 'SYM': 0, 'ERR': 0}
    lexer.input(code)
    while True:
        tok = lexer.token()
        if not tok:
            break
        token_name = tok.type
        results[token_name] += 1
    return results

def analyze_syntactic(code):
    errors = []
    if re.match(r"^collection\('(\w+)'\).document\('(\w+)'\).set\(\{(.+)\}\);$", code, re.IGNORECASE):
        return "Sintaxis correcta"
    elif re.match(r"^collection\('(\w+)'\).add\(\{(.+)\}\);$", code, re.IGNORECASE):
        return "Sintaxis correcta"
    elif re.match(r"^collection\('(\w+)'\).document\('(\w+)'\).update\(\{(.+)\}\);$", code, re.IGNORECASE):
        return "Sintaxis correcta"
    elif re.match(r"^collection\('(\w+)'\).document\('(\w+)'\).delete\(\);$", code, re.IGNORECASE):
        return "Sintaxis correcta"
    else:
        errors.append("Estructura básica de consulta Firestore no válida.")
    if not errors:
        return "Sintaxis correcta"
    else:
        return " ".join(errors)

def analyze_semantic(code):
    errors = []
    declared_collections = set(['mi_coleccion'])

    collections = re.findall(r"collection\('(\w+)'\)", code, re.IGNORECASE)
    for collection in collections:
        if collection not in declared_collections:
            errors.append(f"Colección '{collection}' no existe.")
        declared_collections.add(collection)

    fields = re.findall(r"\{(.+?)\}", code, re.IGNORECASE)
    if fields:
        fields = fields[0].split(',')
        for field in fields:
            field_name = field.split(':')[0].strip().strip('"')
            if field_name not in ['id', 'nombre', 'edad']:
                errors.append(f"Campo '{field_name}' no existe en las colecciones declaradas.")

    if not errors:
        return "Uso correcto de las estructuras semánticas"
    else:
        return " ".join(errors)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/validate', methods=['POST'])
def validate():
    data = request.json
    queries = data.get('queries', [])
    results = []
    for query in queries:
        lexical_results = analyze_lexical(query)
        syntactic_result = analyze_syntactic(query)
        semantic_result = analyze_semantic(query)
        is_valid = syntactic_result == "Sintaxis correcta" and semantic_result == "Uso correcto de las estructuras semánticas"
        error_message = ''
        if not is_valid:
            error_message = syntactic_result if syntactic_result != "Sintaxis correcta" else semantic_result
        results.append({
            'lexical': lexical_results,
            'syntactic': syntactic_result,
            'semantic': semantic_result,
            'valid': is_valid,
            'error': error_message
        })
    return jsonify(results)

if __name__ == '__main__':
    app.run(debug=True)
