"""
Logica de puntuacion: combina el snapshot tecnico y el fundamental en un
score unico, y calcula un precio objetivo a 3 meses y un stop loss
razonable. Todas las formulas son explicitas e intencionadamente
conservadoras: el objetivo es ser honesto, no vender expectativas.
"""
from __future__ import annotations

TECH_WEIGHT = 0.55
FUND_WEIGHT = 0.45


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def technical_score(tech: dict, benchmark_return_3m: float) -> tuple[float, dict]:
    price = tech["price"]
    sma50 = tech["sma50"]
    sma200 = tech["sma200"]
    rsi14 = tech["rsi14"]

    # 1. Tendencia (precio vs medias moviles)
    if sma50 is not None and sma200 is not None:
        if price > sma50 > sma200:
            trend = 100
        elif price > sma50 and sma50 < sma200:
            trend = 60
        elif price < sma50 and sma50 > sma200:
            trend = 40
        elif price < sma50 < sma200:
            trend = 10
        else:
            trend = 50
    elif sma50 is not None:
        trend = 70 if price > sma50 else 30
    else:
        trend = 50

    # 2. Momentum (RSI)
    if 45 <= rsi14 <= 65:
        momentum = 100
    elif 65 < rsi14 <= 75:
        momentum = 70
    elif rsi14 > 75:
        momentum = 30
    elif 35 <= rsi14 < 45:
        momentum = 60
    elif 25 <= rsi14 < 35:
        momentum = 40
    else:
        momentum = 20

    # 3. MACD (cruce e impulso)
    macd_bullish = tech["macd"] > tech["macd_signal"]
    hist_rising = tech["macd_hist"] > tech["macd_hist_prev"]
    if macd_bullish and hist_rising:
        macd_score = 100
    elif macd_bullish and not hist_rising:
        macd_score = 65
    elif not macd_bullish and hist_rising:
        macd_score = 55
    else:
        macd_score = 20

    # 4. Fuerza relativa vs S&P 500 (3 meses)
    relative = tech["return_3m"] - benchmark_return_3m
    if relative > 0.10:
        rel_score = 100
    elif relative > 0:
        rel_score = 70
    elif relative > -0.10:
        rel_score = 40
    else:
        rel_score = 15

    total = trend * 0.30 + momentum * 0.25 + macd_score * 0.25 + rel_score * 0.20
    breakdown = {
        "trend": trend,
        "momentum": momentum,
        "macd": macd_score,
        "relative_strength": rel_score,
    }
    return round(total, 1), breakdown


def fundamental_score(fund: dict, price: float) -> tuple[float, dict]:
    # 1. Valoracion (PER)
    pe = fund.get("trailing_pe") or fund.get("forward_pe")
    if pe is None or pe <= 0:
        valuation = 40  # sin datos o beneficios negativos: neutral-bajo
    elif pe < 15:
        valuation = 100
    elif pe < 25:
        valuation = 75
    elif pe < 35:
        valuation = 50
    elif pe < 50:
        valuation = 30
    else:
        valuation = 15

    # 2. Crecimiento (ingresos + beneficios)
    growth_values = [g for g in (fund.get("revenue_growth"), fund.get("earnings_growth")) if g is not None]
    if growth_values:
        avg_growth = sum(growth_values) / len(growth_values)
        if avg_growth > 0.20:
            growth = 100
        elif avg_growth > 0.10:
            growth = 80
        elif avg_growth > 0:
            growth = 55
        else:
            growth = 20
    else:
        growth = 50

    # 3. Rentabilidad (margenes + ROE)
    margin = fund.get("profit_margin")
    roe = fund.get("roe")
    prof_values = [v for v in (margin, roe) if v is not None]
    if prof_values:
        avg_prof = sum(prof_values) / len(prof_values)
        if avg_prof > 0.20:
            profitability = 100
        elif avg_prof > 0.10:
            profitability = 75
        elif avg_prof > 0:
            profitability = 50
        else:
            profitability = 20
    else:
        profitability = 50

    # 4. Consenso de analistas
    target_mean = fund.get("target_mean_price")
    rec_mean = fund.get("recommendation_mean")
    if target_mean and price:
        upside = (target_mean - price) / price
        if upside > 0.15:
            analyst_upside_score = 100
        elif upside > 0.05:
            analyst_upside_score = 75
        elif upside > -0.05:
            analyst_upside_score = 50
        else:
            analyst_upside_score = 20
    else:
        analyst_upside_score = 50

    if rec_mean:
        # recommendationMean: 1=compra fuerte, 5=venta fuerte
        rec_score = _clamp(100 - (rec_mean - 1) * 30, 0, 100)
    else:
        rec_score = 50

    analyst = (analyst_upside_score + rec_score) / 2

    total = valuation * 0.25 + growth * 0.30 + profitability * 0.20 + analyst * 0.25
    breakdown = {
        "valuation": round(valuation, 1),
        "growth": round(growth, 1),
        "profitability": round(profitability, 1),
        "analyst_consensus": round(analyst, 1),
    }
    return round(total, 1), breakdown


def compute_target_and_stop(tech: dict, fund: dict) -> dict:
    price = tech["price"]

    # --- Precio objetivo a 3 meses ---
    # Componente tecnico: extrapolacion amortiguada del retorno de los
    # ultimos 3 meses (evita proyectar tendencias insostenibles).
    tech_component = _clamp(tech["return_3m"] * 0.35, -0.12, 0.15)

    target_mean = fund.get("target_mean_price")
    if target_mean and price:
        annual_upside = (target_mean - price) / price
        # Un precio objetivo de analistas suele tener horizonte ~12 meses;
        # aplicamos solo una fraccion prudente a un horizonte de 3 meses.
        analyst_component = _clamp(annual_upside * 0.35, -0.12, 0.20)
        blended_return = 0.5 * tech_component + 0.5 * analyst_component
    else:
        blended_return = tech_component

    blended_return = _clamp(blended_return, -0.10, 0.25)
    target_price = round(price * (1 + blended_return), 2)

    # --- Stop loss ---
    atr14 = tech.get("atr14")
    atr_stop = price - 2 * atr14 if atr14 else price * 0.90
    swing_low = tech.get("low_20d", price * 0.90)
    stop_candidate = max(atr_stop, swing_low * 0.99)

    stop_pct = (price - stop_candidate) / price
    stop_pct = _clamp(stop_pct, 0.04, 0.15)
    stop_loss = round(price * (1 - stop_pct), 2)

    return {
        "target_price": target_price,
        "upside_pct": round(blended_return * 100, 1),
        "stop_loss": stop_loss,
        "stop_loss_pct": round(stop_pct * 100, 1),
    }


def combined_score(tech_s: float, fund_s: float) -> float:
    return round(tech_s * TECH_WEIGHT + fund_s * FUND_WEIGHT, 1)


def build_rationale(tech: dict, fund: dict, tech_breakdown: dict, fund_breakdown: dict) -> list[str]:
    notes = []

    if tech_breakdown["trend"] >= 90:
        notes.append("Tendencia alcista clara: precio por encima de sus medias de 50 y 200 sesiones.")
    elif tech_breakdown["trend"] <= 20:
        notes.append("Tendencia bajista: precio por debajo de sus medias moviles principales.")

    rsi14 = tech["rsi14"]
    if rsi14 > 70:
        notes.append(f"RSI en zona de sobrecompra ({rsi14:.0f}); posible correccion a corto plazo.")
    elif rsi14 < 30:
        notes.append(f"RSI en zona de sobreventa ({rsi14:.0f}); riesgo de continuar cayendo.")

    if tech_breakdown["macd"] >= 90:
        notes.append("MACD en cruce alcista con impulso creciente.")

    if fund.get("revenue_growth") and fund["revenue_growth"] > 0.15:
        notes.append(f"Crecimiento de ingresos solido ({fund['revenue_growth']*100:.1f}% interanual).")

    pe = fund.get("trailing_pe")
    if pe and pe < 18:
        notes.append(f"Valoracion contenida (PER {pe:.1f}x).")
    elif pe and pe > 45:
        notes.append(f"Valoracion exigente (PER {pe:.1f}x); ya descuenta buenas noticias.")

    if fund.get("target_mean_price") and fund.get("num_analysts"):
        notes.append(
            f"Consenso de {int(fund['num_analysts'])} analistas con precio objetivo medio "
            f"de {fund['target_mean_price']:.2f}."
        )

    if not notes:
        notes.append("Señales mixtas: perfil equilibrado entre riesgo y oportunidad.")

    return notes[:4]
