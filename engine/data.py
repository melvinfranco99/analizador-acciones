"""
Capa de acceso a datos: descarga precios historicos y datos fundamentales
usando yfinance (Yahoo Finance), sin necesidad de API key.
"""
from __future__ import annotations

import concurrent.futures as cf
import logging

import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)

BENCHMARK_TICKER = "^GSPC"
PRICE_PERIOD = "1y"
PRICE_INTERVAL = "1d"
CHUNK_SIZE = 80
FUNDAMENTALS_WORKERS = 20


def download_price_history(tickers: list[str]) -> dict[str, pd.DataFrame]:
    """
    Descarga precios OHLCV para una lista de tickers en bloques (yfinance
    permite descarga masiva, pero en listas muy grandes es mas fiable
    trocearlas). Devuelve un dict ticker -> DataFrame (vacio si fallo).
    """
    all_tickers = list(tickers) + [BENCHMARK_TICKER]
    result: dict[str, pd.DataFrame] = {}

    for i in range(0, len(all_tickers), CHUNK_SIZE):
        chunk = all_tickers[i : i + CHUNK_SIZE]
        try:
            data = yf.download(
                chunk,
                period=PRICE_PERIOD,
                interval=PRICE_INTERVAL,
                group_by="ticker",
                auto_adjust=True,
                threads=True,
                progress=False,
            )
        except Exception:
            logger.exception("Fallo al descargar bloque de precios: %s", chunk)
            continue

        if len(chunk) == 1:
            ticker = chunk[0]
            if not data.empty:
                result[ticker] = data.dropna(how="all")
            continue

        for ticker in chunk:
            try:
                df = data[ticker].dropna(how="all")
            except (KeyError, IndexError):
                continue
            if not df.empty and "Close" in df.columns:
                result[ticker] = df

    return result


def fetch_fundamentals(ticker: str) -> dict:
    """Devuelve el diccionario .info de yfinance para un ticker (o {})."""
    try:
        t = yf.Ticker(ticker)
        info = t.get_info()
        return info or {}
    except Exception:
        return {}


def fetch_fundamentals_bulk(tickers: list[str]) -> dict[str, dict]:
    """Descarga fundamentales para varios tickers en paralelo (I/O bound)."""
    results: dict[str, dict] = {}
    with cf.ThreadPoolExecutor(max_workers=FUNDAMENTALS_WORKERS) as executor:
        future_to_ticker = {
            executor.submit(fetch_fundamentals, ticker): ticker for ticker in tickers
        }
        for future in cf.as_completed(future_to_ticker):
            ticker = future_to_ticker[future]
            try:
                info = future.result()
            except Exception:
                info = {}
            if info:
                results[ticker] = info
    return results
