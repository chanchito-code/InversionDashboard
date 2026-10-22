"""Capa de datos: descarga histórica y fundamentales vía yfinance.

yfinance no es una API oficial de Yahoo: puede fallar o cambiar sin aviso.
Por eso aquí hay reintentos, validación y mensajes de error claros.
"""

from __future__ import annotations

import logging
import time

import pandas as pd
import yfinance as yf

# yfinance escribe avisos ruidosos ("Failed download") en la terminal;
# los dejamos solo en nivel ERROR para no confundir al usuario.
logging.getLogger("yfinance").setLevel(logging.ERROR)

PERIODOS = {
    "1 mes": "1mo",
    "3 meses": "3mo",
    "6 meses": "6mo",
    "1 año": "1y",
    "2 años": "2y",
    "5 años": "5y",
    "10 años": "10y",
    "Máximo": "max",
}

INTENTOS = 4
ESPERA_SEGUNDOS = 4


class ErrorDatos(Exception):
    """Error controlado al obtener datos de mercado."""


def _reintentar(func, *args, **kwargs):
    ultimo_error = None
    for intento in range(INTENTOS):
        try:
            resultado = func(*args, **kwargs)
            if resultado is None:
                raise ErrorDatos("La fuente devolvió una respuesta vacía.")
            return resultado
        except ErrorDatos:
            raise
        except Exception as exc:  # noqa: BLE001 - yfinance lanza tipos variados
            ultimo_error = exc
            if intento < INTENTOS - 1:
                time.sleep(ESPERA_SEGUNDOS * (intento + 1))
    raise ErrorDatos(
        f"No se pudo descargar la información tras {INTENTOS} intentos. "
        f"Detalle: {ultimo_error}"
    )


def descargar_historial(ticker: str, periodo: str = "2y") -> pd.DataFrame:
    """Devuelve velas OHLCV diarias del ticker. Lanza ErrorDatos si falla."""

    def _fetch():
        df = yf.download(
            ticker,
            period=periodo,
            interval="1d",
            auto_adjust=True,
            progress=False,
            threads=False,
        )
        if df is None or df.empty:
            raise ErrorDatos(
                f"No hay datos para '{ticker}'. Verifica el símbolo "
                "(ej.: AAPL, SPY, WALMEX.MX)."
            )
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        return df

    df = _reintentar(_fetch)
    df = df.dropna(how="all")
    if len(df) < 30:
        raise ErrorDatos(
            f"'{ticker}' solo tiene {len(df)} sesiones. Se necesitan al menos 30 "
            "para calcular indicadores y modelos."
        )
    return df


def descargar_fundamentales(ticker: str) -> dict:
    """Datos básicos de la empresa/fondo. Devuelve dict (puede tener Nones)."""
    vacio = {
        "nombre": ticker,
        "sector": "N/D",
        "precio": None,
        "per": None,
        "dividendo": None,
        "rango_52s": None,
        "capitalizacion": None,
        "beta": None,
        "descripcion": "",
    }

    def _fetch():
        info = yf.Ticker(ticker).info
        if not info:
            raise ErrorDatos("Sin fundamentales disponibles.")
        return info

    try:
        info = _reintentar(_fetch)
    except ErrorDatos:
        return vacio

    def _num(*claves):
        for clave in claves:
            valor = info.get(clave)
            if isinstance(valor, (int, float)):
                return valor
        return None

    min52, max52 = _num("fiftyTwoWeekLow"), _num("fiftyTwoWeekHigh")
    return {
        "nombre": info.get("longName") or info.get("shortName") or ticker,
        "sector": info.get("sector") or "N/D",
        "precio": _num("currentPrice", "regularMarketPrice"),
        "per": _num("trailingPE"),
        "dividendo": _num("dividendYield"),
        "rango_52s": (min52, max52) if min52 and max52 else None,
        "capitalizacion": _num("marketCap"),
        "beta": _num("beta"),
        "descripcion": info.get("longBusinessSummary") or "",
    }


def resolver_ticker(entrada: str) -> str:
    """Normaliza la entrada del usuario a formato yfinance.

    'walmex' -> 'WALMEX.MX' si es mexicano; 'aapl' -> 'AAPL'.
    """
    t = entrada.strip().upper().replace(" ", "")
    if not t:
        raise ErrorDatos("Escribe un símbolo, por ejemplo: AAPL, SPY o WALMEX.MX")
    if "." in t or ":" in t:
        return t.replace(":", ".")
    if t.endswith("MX"):
        return t
    return t
