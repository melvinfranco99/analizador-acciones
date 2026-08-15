"""
Servidor web local para el analizador de acciones.

Uso:
    pip install -r requirements.txt
    python app.py

Abre automaticamente http://127.0.0.1:5000 en el navegador.
"""
from __future__ import annotations

import logging
import threading
import webbrowser
from pathlib import Path

from flask import Flask, jsonify, render_template

from engine.analyze import run_analysis
from engine.changes import build_changes

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

_analysis_lock = threading.Lock()

BASE_DIR = Path(__file__).parent
STATE_PATH = BASE_DIR / "state" / "last_run.json"
CHANGES_PATH = BASE_DIR / "docs" / "changes.json"


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/analyze", methods=["POST"])
def api_analyze():
    if not _analysis_lock.acquire(blocking=False):
        return jsonify({"error": "Ya hay un analisis en curso, espera a que termine."}), 429
    try:
        payload = run_analysis()
        payload["changes"] = build_changes(payload["results"], STATE_PATH, CHANGES_PATH)
        return jsonify(payload)
    except Exception as exc:  # pragma: no cover
        logging.exception("Error durante el analisis")
        return jsonify({"error": str(exc)}), 500
    finally:
        _analysis_lock.release()


def _open_browser():
    webbrowser.open("http://127.0.0.1:5000")


if __name__ == "__main__":
    threading.Timer(1.2, _open_browser).start()
    app.run(host="127.0.0.1", port=5000, debug=False, threaded=True)
