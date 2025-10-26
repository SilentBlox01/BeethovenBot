from flask import Flask
import threading
import asyncio

app = Flask(__name__)

@app.route("/")
def home():
    return "<h1>Beethoven Bot Online ✅</h1>"

def run_flask():
    app.run(host="0.0.0.0", port=8080)

def keep_alive():
    # Ejecuta Flask en un hilo separado para no bloquear el bot
    t = threading.Thread(target=run_flask)
    t.start()
