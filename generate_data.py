"""
Ejecuta el pipeline de analisis y escribe:
  - docs/data.json     -> ranking actual (lo consume la web estatica)
  - docs/changes.json  -> historial de cambios de opinion (ultimos 3 meses)
  - state/last_run.json -> estado interno para poder detectar cambios en la
    siguiente ejecucion (no lo consume la web, es uso interno del motor)

Uso:
    python generate_data.py
"""
from __future__ import annotations

import json
from pathlib import Path

from engine.analyze import run_analysis
from engine.changes import build_changes

BASE_DIR = Path(__file__).parent
DATA_PATH = BASE_DIR / "docs" / "data.json"
CHANGES_PATH = BASE_DIR / "docs" / "changes.json"
STATE_PATH = BASE_DIR / "state" / "last_run.json"


def main() -> None:
    payload = run_analysis()
    DATA_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Escritos {len(payload['results'])} resultados en {DATA_PATH}")

    changes = build_changes(payload["results"], STATE_PATH, CHANGES_PATH)
    print(f"Historial de cambios actualizado: {len(changes)} entradas en {CHANGES_PATH}")


if __name__ == "__main__":
    main()
