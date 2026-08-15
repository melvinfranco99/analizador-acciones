"""
Registro de "cambios de opinion" de los ultimos 3 meses, combinando dos
fuentes honestas y verificables (nada inventado):

  1. Cambios en nuestro propio modelo: comparamos el ranking/objetivo
     actual con el estado guardado de la ejecucion anterior (persistido
     en disco) para detectar entradas/salidas del Top 10 y revisiones de
     precio objetivo.
  2. Eventos reales de mercado via yfinance: cambios de recomendacion de
     analistas (subida/bajada de rating o de precio objetivo) y sorpresas
     de resultados (BPA real vs estimado), cada uno con su fecha real.

No se generan interpretaciones cualitativas sin fuente (p. ej. "el CEO dijo
X"): solo se reportan hechos con fecha y origen verificable.
"""
from __future__ import annotations

import concurrent.futures as cf
import datetime as dt
import hashlib
import json
import logging
from pathlib import Path

import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)

HISTORY_WINDOW_DAYS = 90
TARGET_CHANGE_THRESHOLD = 0.05  # 5% de variacion en el precio objetivo del modelo
EARNINGS_SURPRISE_THRESHOLD = 3.0  # puntos porcentuales
MARKET_EVENTS_WORKERS = 10


def _load_json(path: Path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        logger.exception("No se pudo leer %s", path)
        return default


def _save_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _make_entry(date_obj, ticker: str, name: str, category: str, type_: str, description: str) -> dict:
    date_str = date_obj.isoformat() if hasattr(date_obj, "isoformat") else str(date_obj)
    raw_id = f"{ticker}|{type_}|{date_str}|{description}"
    entry_id = hashlib.md5(raw_id.encode("utf-8")).hexdigest()[:16]
    return {
        "id": entry_id,
        "date": date_str,
        "ticker": ticker,
        "name": name,
        "category": category,  # "modelo" | "analista" | "resultados"
        "type": type_,
        "description": description,
    }


def _state_entry(result: dict) -> dict:
    return {
        "rank": result["rank"],
        "name": result["name"],
        "target_price": result["target_price"],
        "upside_pct": result["upside_pct"],
        "total_score": result["total_score"],
    }


def diff_model_state(previous_state: dict, current_top: list[dict], today: dt.date) -> list[dict]:
    """Detecta cambios de opinion de nuestro propio modelo frente a la ejecucion anterior."""
    entries = []
    current_map = {r["ticker"]: r for r in current_top}

    for ticker, prev in previous_state.items():
        if ticker not in current_map:
            name = prev.get("name", ticker)
            entries.append(
                _make_entry(
                    today, ticker, name, "modelo", "sale_top10",
                    f"{name} sale del Top 10 (antes en el puesto #{prev.get('rank', '?')}).",
                )
            )

    for ticker, cur in current_map.items():
        prev = previous_state.get(ticker)
        if prev is None:
            entries.append(
                _make_entry(
                    today, ticker, cur["name"], "modelo", "entra_top10",
                    f"{cur['name']} entra en el Top 10 (puesto #{cur['rank']}) con precio objetivo de "
                    f"{cur['target_price']:.2f} $ ({cur['upside_pct']:+.1f}% a 3 meses).",
                )
            )
            continue

        prev_target = prev.get("target_price")
        if prev_target:
            delta_pct = (cur["target_price"] - prev_target) / prev_target
            if abs(delta_pct) >= TARGET_CHANGE_THRESHOLD:
                up = delta_pct > 0
                entries.append(
                    _make_entry(
                        today, ticker, cur["name"], "modelo",
                        "objetivo_subido" if up else "objetivo_bajado",
                        f"Precio objetivo de nuestro modelo revisado de {prev_target:.2f} $ a "
                        f"{cur['target_price']:.2f} $ ({delta_pct*100:+.1f}%).",
                    )
                )

    return entries


def _fetch_analyst_events(ticker: str, name: str, cutoff_date: dt.date) -> list[dict]:
    entries = []
    try:
        df = yf.Ticker(ticker).upgrades_downgrades
    except Exception:
        return entries
    if df is None or df.empty:
        return entries

    df = df.reset_index()
    date_col = df.columns[0]

    for _, row in df.iterrows():
        ts = row[date_col]
        d = ts.date() if hasattr(ts, "date") else None
        if d is None or d < cutoff_date:
            continue

        action = str(row.get("Action", "")).lower()
        firm = row.get("Firm") or "Un analista"
        to_grade = row.get("ToGrade") or "N/D"
        from_grade = row.get("FromGrade") or "N/D"
        cur_pt = row.get("currentPriceTarget")
        prior_pt = row.get("priorPriceTarget")
        pt_action = row.get("priceTargetAction") or ""

        if action == "up":
            desc = f"{firm} sube la recomendacion de {from_grade} a {to_grade}."
            if cur_pt:
                desc += f" Precio objetivo: {cur_pt:.2f} $."
            entries.append(_make_entry(d, ticker, name, "analista", "upgrade_analista", desc))
        elif action == "down":
            desc = f"{firm} baja la recomendacion de {from_grade} a {to_grade}."
            if cur_pt:
                desc += f" Precio objetivo: {cur_pt:.2f} $."
            entries.append(_make_entry(d, ticker, name, "analista", "downgrade_analista", desc))
        elif pt_action in ("Raises", "Lowers") and prior_pt and cur_pt and prior_pt > 0 and cur_pt != prior_pt:
            up = pt_action == "Raises"
            desc = (
                f"{firm} {'sube' if up else 'baja'} su precio objetivo de {prior_pt:.2f} $ a "
                f"{cur_pt:.2f} $ (mantiene {to_grade})."
            )
            entries.append(
                _make_entry(
                    d, ticker, name, "analista",
                    "objetivo_analista_subido" if up else "objetivo_analista_bajado", desc,
                )
            )

    return entries


def _fetch_earnings_events(ticker: str, name: str, cutoff_date: dt.date) -> list[dict]:
    entries = []
    try:
        df = yf.Ticker(ticker).get_earnings_dates(limit=12)
    except Exception:
        return entries
    if df is None or df.empty:
        return entries

    df = df.reset_index()
    date_col = df.columns[0]
    today = dt.date.today()

    for _, row in df.iterrows():
        ts = row[date_col]
        d = ts.date() if hasattr(ts, "date") else None
        if d is None or d < cutoff_date or d > today:
            continue

        surprise = row.get("Surprise(%)")
        if surprise is None or pd.isna(surprise) or abs(surprise) < EARNINGS_SURPRISE_THRESHOLD:
            continue

        reported = row.get("Reported EPS")
        estimate = row.get("EPS Estimate")
        positive = surprise > 0
        desc = (
            f"Resultados del {d.isoformat()}: BPA real {reported:.2f} $ vs estimado {estimate:.2f} $ "
            f"(sorpresa {surprise:+.1f}%)."
        )
        entries.append(
            _make_entry(
                d, ticker, name, "resultados",
                "resultados_positivos" if positive else "resultados_negativos", desc,
            )
        )

    return entries


def _fetch_market_events(current_top: list[dict], cutoff_date: dt.date) -> list[dict]:
    entries = []
    with cf.ThreadPoolExecutor(max_workers=MARKET_EVENTS_WORKERS) as executor:
        futures = []
        for r in current_top:
            futures.append(executor.submit(_fetch_analyst_events, r["ticker"], r["name"], cutoff_date))
            futures.append(executor.submit(_fetch_earnings_events, r["ticker"], r["name"], cutoff_date))
        for future in cf.as_completed(futures):
            try:
                entries.extend(future.result())
            except Exception:
                logger.exception("Fallo al obtener eventos de mercado")
    return entries


def build_changes(current_top: list[dict], state_path: Path, changes_path: Path) -> list[dict]:
    """Actualiza el estado persistido y el historial de cambios (ultimos 3 meses)."""
    today = dt.date.today()
    cutoff = today - dt.timedelta(days=HISTORY_WINDOW_DAYS)

    previous_state = _load_json(state_path, default={})
    model_entries = diff_model_state(previous_state, current_top, today)

    new_state = {r["ticker"]: _state_entry(r) for r in current_top}
    _save_json(state_path, new_state)

    market_entries = _fetch_market_events(current_top, cutoff)

    existing_changes = _load_json(changes_path, default=[])
    merged_by_id = {e["id"]: e for e in existing_changes}
    for entry in model_entries + market_entries:
        merged_by_id[entry["id"]] = entry

    def _still_recent(entry: dict) -> bool:
        try:
            return dt.date.fromisoformat(entry["date"][:10]) >= cutoff
        except (ValueError, KeyError):
            return False

    pruned = [e for e in merged_by_id.values() if _still_recent(e)]
    pruned.sort(key=lambda e: e["date"], reverse=True)

    _save_json(changes_path, pruned)
    return pruned
