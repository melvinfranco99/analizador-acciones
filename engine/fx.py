"""Tipo de cambio USD/EUR para mostrar los precios tambien en euros."""
from __future__ import annotations

import logging

import yfinance as yf

logger = logging.getLogger(__name__)


def fetch_usd_to_eur_rate() -> float | None:
    """
    Devuelve cuantos dolares vale 1 euro (p.ej. 1.08). Para convertir un
    importe en USD a EUR: eur = usd / rate.
    """
    try:
        hist = yf.Ticker("EURUSD=X").history(period="5d")
        if hist.empty:
            return None
        return float(hist["Close"].iloc[-1])
    except Exception:
        logger.exception("No se pudo obtener el tipo de cambio EUR/USD")
        return None


def usd_to_eur(usd_value: float | None, rate: float | None) -> float | None:
    if usd_value is None or not rate:
        return None
    return round(usd_value / rate, 2)
