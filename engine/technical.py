"""
Calculo de indicadores tecnicos clasicos a partir de un DataFrame OHLCV
(columnas Open, High, Low, Close, Volume) y construccion de un "snapshot"
resumido por accion.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

MIN_ROWS_REQUIRED = 60


def sma(series: pd.Series, window: int) -> pd.Series:
    return series.rolling(window=window, min_periods=window).mean()


def rsi(series: pd.Series, window: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / window, min_periods=window, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / window, min_periods=window, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    out = 100 - (100 / (1 + rs))
    return out.fillna(50)


def macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    ema_fast = series.ewm(span=fast, adjust=False).mean()
    ema_slow = series.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram


def atr(df: pd.DataFrame, window: int = 14) -> pd.Series:
    high, low, close = df["High"], df["Low"], df["Close"]
    prev_close = close.shift(1)
    tr = pd.concat(
        [
            (high - low).abs(),
            (high - prev_close).abs(),
            (low - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    return tr.ewm(alpha=1 / window, min_periods=window, adjust=False).mean()


def build_technical_snapshot(df: pd.DataFrame) -> dict | None:
    """
    Construye un resumen tecnico a partir del historico de precios.
    Devuelve None si no hay suficientes datos para calcular con fiabilidad.
    """
    if df is None or len(df) < MIN_ROWS_REQUIRED or "Close" not in df.columns:
        return None

    close = df["Close"].dropna()
    if len(close) < MIN_ROWS_REQUIRED:
        return None

    price = float(close.iloc[-1])
    sma50_series = sma(close, 50)
    sma200_series = sma(close, 200) if len(close) >= 200 else pd.Series(dtype=float)
    rsi_series = rsi(close, 14)
    macd_line, signal_line, hist = macd(close)
    atr_series = atr(df, 14)

    sma50 = float(sma50_series.iloc[-1]) if not sma50_series.dropna().empty else None
    sma200 = float(sma200_series.iloc[-1]) if not sma200_series.dropna().empty else None
    rsi14 = float(rsi_series.iloc[-1])
    macd_val = float(macd_line.iloc[-1])
    signal_val = float(signal_line.iloc[-1])
    hist_val = float(hist.iloc[-1])
    hist_prev = float(hist.iloc[-2]) if len(hist) > 1 else hist_val
    atr14 = float(atr_series.iloc[-1]) if not atr_series.dropna().empty else None

    lookback_3m = min(63, len(close) - 1)
    return_3m = float(close.iloc[-1] / close.iloc[-1 - lookback_3m] - 1) if lookback_3m > 0 else 0.0

    low_20d = float(df["Low"].iloc[-20:].min()) if len(df) >= 20 else float(df["Low"].min())
    high_52w = float(close.iloc[-252:].max()) if len(close) >= 5 else price
    low_52w = float(close.iloc[-252:].min()) if len(close) >= 5 else price

    return {
        "price": price,
        "sma50": sma50,
        "sma200": sma200,
        "rsi14": rsi14,
        "macd": macd_val,
        "macd_signal": signal_val,
        "macd_hist": hist_val,
        "macd_hist_prev": hist_prev,
        "atr14": atr14,
        "return_3m": return_3m,
        "low_20d": low_20d,
        "high_52w": high_52w,
        "low_52w": low_52w,
    }
