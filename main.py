# app.py
import os
from collections import deque
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

app = Flask(__name__,
            static_folder="static",
            static_url_path="")

CORS(app, resources={r"/generate": {"origins": "*"}, r"/health": {"origins": "*"}})

# ===========================
# Memoria mínima en proceso
# ===========================
# Guardamos por session_id una ventana de últimos N turnos (user+assistant)
HIST_WINDOW = 6  # ajusta si quieres más/menos contexto
MEM_STORE: dict[str, deque] = {}

def get_session_history(session_id: str) -> deque:
    """Devuelve el historial (deque) de la sesión; lo crea si no existe."""
    if session_id not in MEM_STORE:
        # maxlen = turnos_user_y_assistant * 2 mensajes (uno user, otro assistant)
        MEM_STORE[session_id] = deque(maxlen=HIST_WINDOW * 2)
    return MEM_STORE[session_id]

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
    Cuerpo JSON:
    {
      "prompt": "Escribe un guion de 1 página sobre viajes en el tiempo...",
      "session_id": "usuario_123"   # opcional; por defecto "demo"
    }
    """
    data = request.get_json(silent=True) or {}

    # Prompt del sistema (vendedor)
    system_prompt = (
        "Eres el mejor vendedor del mundo. "
        "Tu tarea: ante el primer mensaje de usuario le ofrecerás tu ayuda, le preguntarás el nombre al usuario y el producto que busca"
        "Identificarás el producto que menciona y recomendarás ese mismo producto con un argumento persuasivo y claro. "
        "Si no menciona ningún producto, preguntale nuevamente qué producto busca. "
        "Estructura tu respuesta al producto de interés con estas secciones "
        "- Encabezado breve y atractivo, "
        "- Un beneficio del producto. "
        "- Una prueba social, "
        "- Un llamado a la acción claro. "
        "jamás muestres los títulos de estas secciones, eso es conficencial, solo muestra el texto que generes. "
        "Sé conciso y amigable"
        "Luego, si el usuario muestra interés, ofrécele un descuento del 10% si realiza la compra hoy."
        "Inventa una URL de compra para el producto. y muéstrale al cliente para cerrar tu venta"
    )

    # 1) Lectura segura del input y la sesión
    user_msg = (data.get("prompt") or "").strip()
    session_id = (data.get("session_id") or "demo").strip()

    if not user_msg:
        return jsonify({"error": "Falta 'prompt' (string no vacío)."}), 400

    # 2) Recuperar historial de la sesión
    history = get_session_history(session_id)

    # 3) Construir mensajes de entrada:
    #    - system (comportamiento)
    #    - historial previo (user/assistant)
    #    - mensaje actual del usuario
    input_messages = [
        {
            "role": "system",
            "content": [{"type": "input_text", "text": system_prompt}]
        }
    ]
    # Añadir historial previo (ya en formato role/content)
    input_messages.extend(list(history))
    # Mensaje actual del usuario
    input_messages.append({
        "role": "user",
        "content": [{"type": "input_text", "text": user_msg}]
    })

    # 4) Llamar al modelo
    try:
        resp = client.responses.create(
            model=MODEL,
            input=input_messages,
            reasoning={"effort": "minimal"},
            max_output_tokens=800
        )
        text = (resp.output_text or "").strip()
    except Exception:
        return jsonify({"error": "Fallo al generar respuesta."}), 500

    # 5) Actualizar memoria: guardamos el turno del usuario y la respuesta del asistente
    history.append({
        "role": "user",
        "content": [{"type": "input_text", "text": user_msg}]
    })
    history.append({
        "role": "assistant",
        "content": [{"type": "output_text", "text": text}]
    })

    # 6) Respuesta JSON
    return jsonify({
        "model": MODEL,
        "session_id": session_id,
        "prompt_used": user_msg,
        "output": text
    })

if __name__ == "__main__":
    # Ejecución local
    app.run(host="0.0.0.0",
            port=8000)
