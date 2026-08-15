"""
Extraccion y normalizacion de datos fundamentales a partir del diccionario
`.info` que devuelve yfinance para cada ticker.
"""
from __future__ import annotations


def _num(info: dict, *keys, default=None):
    for key in keys:
        val = info.get(key)
        if val is not None:
            try:
                return float(val)
            except (TypeError, ValueError):
                continue
    return default


def build_fundamental_snapshot(info: dict, price: float) -> dict:
    name = info.get("longName") or info.get("shortName") or info.get("symbol", "")
    sector = info.get("sector") or "N/D"
    industry = info.get("industry") or "N/D"

    trailing_pe = _num(info, "trailingPE")
    forward_pe = _num(info, "forwardPE")
    peg_ratio = _num(info, "trailingPegRatio", "pegRatio")

    revenue_growth = _num(info, "revenueGrowth")
    earnings_growth = _num(info, "earningsGrowth", "earningsQuarterlyGrowth")

    profit_margin = _num(info, "profitMargins")
    roe = _num(info, "returnOnEquity")
    debt_to_equity = _num(info, "debtToEquity")

    target_mean = _num(info, "targetMeanPrice")
    target_high = _num(info, "targetHighPrice")
    target_low = _num(info, "targetLowPrice")
    recommendation_mean = _num(info, "recommendationMean")
    num_analysts = info.get("numberOfAnalystOpinions")

    # Filtramos objetivos de analista poco fiables (outliers extremos)
    if target_mean is not None and price:
        implied = (target_mean - price) / price
        if implied > 1.2 or implied < -0.6:
            target_mean = None

    return {
        "name": name,
        "sector": sector,
        "industry": industry,
        "trailing_pe": trailing_pe,
        "forward_pe": forward_pe,
        "peg_ratio": peg_ratio,
        "revenue_growth": revenue_growth,
        "earnings_growth": earnings_growth,
        "profit_margin": profit_margin,
        "roe": roe,
        "debt_to_equity": debt_to_equity,
        "target_mean_price": target_mean,
        "target_high_price": target_high,
        "target_low_price": target_low,
        "recommendation_mean": recommendation_mean,
        "num_analysts": num_analysts,
    }
