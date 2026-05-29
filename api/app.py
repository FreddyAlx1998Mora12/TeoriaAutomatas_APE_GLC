from flask import Flask, request, jsonify
from flask_cors import CORS
from core.lexer import Lexer
from core.parser import Parser
from core.derivation import DerivationBuilder

app = Flask(__name__)
CORS(app)

@app.route("/api/analizar", methods=["POST"])
def analizar():
    data = request.get_json() or {}
    expr = data.get("expresion", "").strip()
    if not expr:
        return jsonify({"error": "Expresión vacía"}), 400
    
    try:
        tokens = Lexer().tokenizar(expr)
        ast = Parser(tokens).parse()
        result = DerivationBuilder().build(ast, tokens)
        return jsonify({
            "expresion": expr,
            "valida": True,
            **result
        })
    except Exception as e:
        return jsonify({"error": str(e), "valida": False}), 400

@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    app.run(debug=True, port=5000)