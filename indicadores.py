"""Indicadores técnicos clásicos + interpretación en lenguaje llano."""

from __future__ import annotations

import numpy as np
import pandas as pd

VENTANA_RSI = 14
VENTANA_RAPIDA = 12
VENTANA_LENTA = 26
VENTANA_SENAL = 9


def media_movil(precio: pd.Series, ventana: int) -> pd.Series:
    return precio.rolling(ventana).mean()


def ema(precio: pd.Series, ventana: int) -> pd.Series:
    return precio.ewm(span=ventana, adjust=False).mean()


def rsi(precio: pd.Series, ventana: int = VENTANA_RSI) -> pd.Series:
    delta = precio.diff()
    ganancia = delta.clip(lower=0).ewm(alpha=1 / ventana, adjust=False).mean()
    perdida = (-delta.clip(upper=0)).ewm(alpha=1 / ventana, adjust=False).mean()
    rs = ganancia / perdida
    resultado = 100 - 100 / (1 + rs)
    # perdida==0 -> rs=inf -> RSI=100; dias sin datos -> 50 (neutral)
    return resultado.replace([np.inf, -np.inf], 100).fillna(50)


def macd(precio: pd.Series) -> pd.DataFrame:
    rapida = ema(precio, VENTANA_RAPIDA)
    lenta = ema(precio, VENTANA_LENTA)
    linea = rapida - lenta
    senal = linea.ewm(span=VENTANA_SENAL, adjust=False).mean()
    return pd.DataFrame(
        {"macd": linea, "senal": senal, "histograma": linea - senal}
    )


def bollinger(precio: pd.Series, ventana: int = 20, desv: float = 2.0) -> pd.DataFrame:
    media = precio.rolling(ventana).mean()
    std = precio.rolling(ventana).std()
    return pd.DataFrame(
        {"media": media, "superior": media + desv * std, "inferior": media - desv * std}
    )


def evaluar_senal(
    precio: pd.Series, rsi_valor: float, macd_df: pd.DataFrame, bb_df: pd.DataFrame
) -> dict:
    """Convierte los indicadores en una lectura simple, no en orden de compra."""
    ultima = precio.iloc[-1]
    sma50 = media_movil(precio, 50).iloc[-1]
    sma200 = media_movil(precio, 200).iloc[-1] if len(precio) >= 200 else pd.NA

    tendencia = "neutral"
    if pd.notna(sma200):
        if ultima > sma50 > sma200:
            tendencia = "alcista (precio sobre medias de 50 y 200)"
        elif ultima < sma50 < sma200:
            tendencia = "bajista (precio bajo las medias de 50 y 200)"

    if rsi_valor >= 70:
        zona_rsi = "sobrecompra (>=70): cuidado, suele anticipar correcciones"
    elif rsi_valor <= 30:
        zona_rsi = "sobreventa (<=30): suele anticipar rebotes, no es garantía"
    else:
        zona_rsi = "neutra (30-70)"

    hist = macd_df["histograma"].iloc[-1]
    senal_macd = (
        "positiva (macd por encima de su señal)" if hist > 0 else "negativa (macd bajo su señal)"
    )

    sup, inf = bb_df["superior"].iloc[-1], bb_df["inferior"].iloc[-1]
    if pd.notna(sup):
        if ultima >= sup:
            zona_bb = "en banda superior: precio extendido respecto a su media"
        elif ultima <= inf:
            zona_bb = "en banda inferior: precio deprimido respecto a su media"
        else:
            zona_bb = "dentro de las bandas (zona normal)"
    else:
        zona_bb = "N/D"

    return {
        "tendencia": tendencia,
        "rsi": zona_rsi,
        "macd": senal_macd,
        "bollinger": zona_bb,
        "sma50": float(sma50) if pd.notna(sma50) else None,
        "sma200": float(sma200) if pd.notna(sma200) else None,
    }
