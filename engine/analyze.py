"""
Orquestador del pipeline de analisis:

  1. Descarga precios de todo el universo (S&P500 + Nasdaq100).
  2. Calcula el snapshot e indicador tecnico de cada accion valida.
  3. Preselecciona los mejores candidatos por tecnico (evita pedir
     fundamentales de 500+ tickers, que seria muy lento).
  4. Descarga fundamentales solo de esos candidatos.
  5. Calcula score combinado, precio objetivo y stop loss.
  6. Devuelve el top 10 final ordenado.
"""
from __future__ import annotations

import datetime as dt
import logging

from . import data, fundamental, scoring, technical
from .tickers import UNIVERSE

logger = logging.getLogger(__name__)

CANDIDATE_POOL_SIZE = 45
TOP_N = 10


def run_analysis() -> dict:
    started_at = dt.datetime.now()

    price_data = data.download_price_history(UNIVERSE)
    benchmark_df = price_data.pop(data.BENCHMARK_TICKER, None)
    benchmark_snapshot = technical.build_technical_snapshot(benchmark_df) if benchmark_df is not None else None
    benchmark_return_3m = benchmark_snapshot["return_3m"] if benchmark_snapshot else 0.0

    tech_candidates = []
    for ticker, df in price_data.items():
        snap = technical.build_technical_snapshot(df)
        if snap is None:
            continue
        t_score, t_breakdown = scoring.technical_score(snap, benchmark_return_3m)
        tech_candidates.append((ticker, snap, t_score, t_breakdown))

    tech_candidates.sort(key=lambda item: item[2], reverse=True)
    pool = tech_candidates[:CANDIDATE_POOL_SIZE]

    fundamentals_map = data.fetch_fundamentals_bulk([c[0] for c in pool])

    results = []
    for ticker, tech_snap, t_score, t_breakdown in pool:
        info = fundamentals_map.get(ticker)
        if not info:
            continue
        fund_snap = fundamental.build_fundamental_snapshot(info, tech_snap["price"])
        f_score, f_breakdown = scoring.fundamental_score(fund_snap, tech_snap["price"])
        target_stop = scoring.compute_target_and_stop(tech_snap, fund_snap)
        total = scoring.combined_score(t_score, f_score)
        rationale = scoring.build_rationale(tech_snap, fund_snap, t_breakdown, f_breakdown)

        results.append(
            {
                "ticker": ticker,
                "name": fund_snap["name"] or ticker,
                "sector": fund_snap["sector"],
                "industry": fund_snap["industry"],
                "price": round(tech_snap["price"], 2),
                "target_price": target_stop["target_price"],
                "upside_pct": target_stop["upside_pct"],
                "stop_loss": target_stop["stop_loss"],
                "stop_loss_pct": target_stop["stop_loss_pct"],
                "technical_score": t_score,
                "fundamental_score": f_score,
                "total_score": total,
                "technical_breakdown": t_breakdown,
                "fundamental_breakdown": f_breakdown,
                "rationale": rationale,
                "pe": fund_snap.get("trailing_pe"),
                "num_analysts": fund_snap.get("num_analysts"),
            }
        )

    results.sort(key=lambda r: r["total_score"], reverse=True)
    top = results[:TOP_N]
    for i, r in enumerate(top, start=1):
        r["rank"] = i

    duration = (dt.datetime.now() - started_at).total_seconds()

    return {
        "generated_at": started_at.isoformat(timespec="seconds"),
        "duration_seconds": round(duration, 1),
        "universe_size": len(UNIVERSE),
        "tickers_with_data": len(tech_candidates),
        "candidates_analyzed": len(pool),
        "benchmark_return_3m": round(benchmark_return_3m * 100, 1),
        "results": top,
    }
