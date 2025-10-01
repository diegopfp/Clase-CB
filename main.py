# app.py
import os
from flask import Flask, request, jsonify
from openai import OpenAI
from dotenv import load_dotenv
from flask_cors import CORS

# ---------------------------
# Configuración básica
# ---------------------------
assert load_dotenv(".env", override=True)
API_KEY = os.getenv("OPENAI_API_KEY")
MODEL = os.getenv("OPENAI_MODEL", "gpt-5-nano")  # modelo por defecto

if not API_KEY:
    raise SystemExit("Falta OPENAI_API_KEY en el entorno (.env o variables del sistema).")

client = OpenAI(api_key=API_KEY)
app = Flask(__name__, static_folder="static", static_url_path="")
CORS(app, resources={r"/generate": {"origins": "*"}, r"/health": {"origins": "*"}})

@app.get("/")
def root():
    # Sirve ./static/index.html
    return app.send_static_file("index.html")

@app.get("/health")
def health():
    return jsonify({"ok": True, "model": MODEL})

@app.post("/generate")
def generate():
    """
    Cuerpo JSON (elige una de dos formas):
    1) Prompt directo:
       {
         "prompt": "Escribe un guion de 1 página sobre viajes en el tiempo..."
       }
    """
    data = request.get_json(silent=True) or {}
    print(data)
    prompt = data["prompt"]
    resp = client.responses.create(
        model=MODEL,
        input=[{"role": "user", "content": [{"type": "input_text", "text": prompt}]}],
        reasoning={"effort": "minimal"},
        max_output_tokens=800
    )
    # Extrae texto
    text = (resp.output_text or "").strip()
    return jsonify({
        "model": MODEL,
        "prompt_used": prompt,
        "output": text
    })


if __name__ == "__main__":
    # Ejecución local
    app.run(host="0.0.0.0", port=8000
            # TODO: escribe el puerto
            )
