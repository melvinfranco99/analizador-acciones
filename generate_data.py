"""
Ejecuta el pipeline de analisis y escribe el resultado en docs/data.json,
que es lo que consume la version estatica de la web (GitHub Pages).

Uso:
    python generate_data.py
"""
from __future__ import annotations

import json
from pathlib import Path

from engine.analyze import run_analysis

OUTPUT_PATH = Path(__file__).parent / "docs" / "data.json"


def main() -> None:
    payload = run_analysis()
    OUTPUT_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Escritos {len(payload['results'])} resultados en {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
