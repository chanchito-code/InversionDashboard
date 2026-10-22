"""Modelos de predicción, backtesting y métricas de riesgo.

Principios aplicados:
- Nunca se entrena con datos futuros (split cronológico estricto).
- Se reporta el error real de cada modelo sobre datos que no vio.
- Las "predicciones" son escenarios con intervalo, no certezas.
"""

from __future__ import annotations

import warnings

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from statsmodels.tsa.holtwinters import ExponentialSmoothing

DIAS_TRABAJO = 252


# ---------------------------------------------------------------------------
# 1) Escenario estadístico: Holt-Winters con intervalo creciente
# ---------------------------------------------------------------------------

def escenario_estadistico(precio: pd.Series, horizonte: int) -> pd.DataFrame:
    """Pronóstico suavizado con banda de confianza que crece con el tiempo."""
    serie = precio.astype(float).dropna()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")  # avisos menores de statsmodels sobre frecuencia
        modelo = ExponentialSmoothing(serie, trend="add", damped_trend=True).fit()
        punto = modelo.forecast(horizonte)

    residuos = modelo.resid.dropna()
    sigma = float(np.std(residuos, ddof=1))
    pasos = np.arange(1, horizonte + 1)
    ancho = 1.96 * sigma * np.sqrt(pasos)  # incertidumbre crece con la raíz del tiempo

    fechas = _fechas_futuras(serie.index[-1], horizonte)
    return pd.DataFrame(
        {
            "fecha": fechas,
            "pronostico": punto.values,
            "inferior": punto.values - ancho,
            "superior": punto.values + ancho,
        }
    ).set_index("fecha")


# ---------------------------------------------------------------------------
# 2) Modelo ML (Ridge con features rezagadas) + evaluación honesta
# ---------------------------------------------------------------------------

def _construir_features(serie: pd.Series) -> pd.DataFrame:
    # Solo variables estrictamente anteriores al día a predecir:
    # nunca se incluye el propio precio del día (eso sería hacer trampa).
    df = pd.DataFrame(index=serie.index)
    for lag in (1, 2, 3, 5, 10, 20):
        df[f"lag_{lag}"] = serie.shift(lag)
    df["media_5"] = serie.shift(1).rolling(5).mean()
    df["media_20"] = serie.shift(1).rolling(20).mean()
    df["std_20"] = serie.shift(1).rolling(20).std()
    # Retornos calculados solo con datos anteriores al día que se predice
    # (shift(1) en el cálculo evita fuga de información del objetivo).
    df["retorno_1"] = serie.shift(1) / serie.shift(2) - 1
    df["retorno_5"] = serie.shift(1) / serie.shift(6) - 1
    return df.dropna()


def modelo_ml(precio: pd.Series, horizonte: int) -> dict:
    """Regresión regularizada sobre el precio siguiente.

    Devuelve pronóstico, error MAE fuera de muestra y precisión direccional.
    """
    serie = precio.astype(float).dropna()
    datos = _construir_features(serie)
    objetivo = serie.loc[datos.index]

    corte = int(len(datos) * 0.8)  # split cronológico: 80% pasado, 20% futuro
    x_train, y_train = datos.iloc[:corte], objetivo.iloc[:corte]
    x_test, y_test = datos.iloc[corte:], objetivo.iloc[corte:]

    pipe = make_pipeline(StandardScaler(), Ridge(alpha=1.0))
    pipe.fit(x_train, y_train)

    pred_test = pipe.predict(x_test)
    mae = float(mean_absolute_error(y_test, pred_test))
    direccion_real = np.sign(y_test.values - x_test["lag_1"].values)
    direccion_pred = np.sign(pred_test - x_test["lag_1"].values)
    precision = float(np.mean(direccion_real == direccion_pred)) * 100

    pronostico = []
    work = serie.copy()
    for _ in range(horizonte):
        fila = _construir_features(work).iloc[[-1]]
        valor = float(pipe.predict(fila)[0])
        pronostico.append(valor)
        work = pd.concat([work, pd.Series([valor], index=[_siguiente(work.index[-1])])])

    fechas = _fechas_futuras(serie.index[-1], horizonte)
    return {
        "pronostico": pd.Series(pronostico, index=fechas, name="pronostico_ml"),
        "mae": mae,
        "precision_direccional": precision,
        "n_entrenamiento": len(x_train),
        "n_prueba": len(x_test),
        "explicacion": (
            f"MAE = {mae:,.2f}: error medio del modelo en dólares sobre datos que "
            f"nunca vio ({len(x_test)} sesiones). Precisión direccional = "
            f"{precision:.1f}% de aciertos al subir/bajar (50% = lanzar una moneda)."
        ),
    }


# ---------------------------------------------------------------------------
# 3) Escenarios alcista / base / bajista
# ---------------------------------------------------------------------------

def escenarios_multibanda(precio: pd.Series, horizonte: int) -> pd.DataFrame:
    """Tres trayectorias basadas en deriva y volatilidad históricas reales."""
    serie = precio.astype(float).dropna()
    retornos = serie.pct_change().dropna()
    mu = float(retornos.mean())
    sigma = float(retornos.std(ddof=1))
    ultimo = float(serie.iloc[-1])
    dias = np.arange(1, horizonte + 1)

    def trayectoria(factor_mu: float) -> np.ndarray:
        drift = mu * factor_mu
        return ultimo * np.exp(drift * dias - 0.5 * (sigma**2) * dias + 0)

    base = ultimo * np.exp((mu - 0.5 * sigma**2) * dias)
    alcista = trayectoria(2.0) * np.exp(1.0 * sigma * np.sqrt(dias))
    bajista = trayectoria(0.0) * np.exp(-1.0 * sigma * np.sqrt(dias))

    fechas = _fechas_futuras(serie.index[-1], horizonte)
    return pd.DataFrame(
        {"alcista": alcista, "base": base, "bajista": bajista}, index=fechas
    )


# ---------------------------------------------------------------------------
# 4) Backtest: cruce de medias vs comprar y mantener
# ---------------------------------------------------------------------------

def backtest_cruce_medias(
    df: pd.DataFrame, rapida: int = 50, lenta: int = 200, comision: float = 0.001
) -> dict:
    """Estrategia long-only: invertido cuando precio > SMA_lenta, fuera si no.

    comision = coste por operación (0.1% por defecto, ida y vuelta).
    """
    data = df[["Close"]].dropna().copy()
    if len(data) < lenta + 10:
        raise ValueError(
            f"Se necesitan al menos {lenta + 10} sesiones para el backtest "
            f"con SMA {lenta}. Amplía el periodo de datos."
        )
    precio = data["Close"]
    sma_r = precio.rolling(rapida).mean()
    sma_l = precio.rolling(lenta).mean()

    posicion = (sma_r > sma_l).astype(float)  # 1 = invertido, 0 = en efectivo
    posicion = posicion.shift(1).fillna(0)  # opera al día siguiente de la señal

    retorno = precio.pct_change().fillna(0)
    cambios = posicion.diff().abs().fillna(0)
    costos = cambios * comision
    estrategia = posicion * retorno - costos
    buy_hold = retorno

    eq_est = (1 + estrategia).cumprod()
    eq_bh = (1 + buy_hold).cumprod()

    metricas = {
        "compraymantener": _resumen_curva(eq_bh, retorno),
        "estrategia": _resumen_curva(eq_est, estrategia),
        "curvas": pd.DataFrame(
            {"estrategia": eq_est, "compraymantener": eq_bh, "posicion": posicion}
        ),
        "operaciones": int(cambios.sum()),
        "parametros": {"rapida": rapida, "lenta": lenta, "comision": comision},
    }
    return metricas


def _resumen_curva(equity: pd.Series, retornos: pd.Series) -> dict:
    anos = max(len(equity) / DIAS_TRABAJO, 1e-9)
    total = float(equity.iloc[-1] - 1)
    cagr = float((equity.iloc[-1]) ** (1 / anos) - 1)
    vol = float(retornos.std(ddof=1) * np.sqrt(DIAS_TRABAJO))
    sharpe = float(retornos.mean() / retornos.std(ddof=1) * np.sqrt(DIAS_TRABAJO)) if retornos.std(ddof=1) > 0 else 0.0
    dd = equity / equity.cummax() - 1
    return {
        "rentabilidad_total": total,
        "cagr": cagr,
        "volatilidad": vol,
        "sharpe": sharpe,
        "max_drawdown": float(dd.min()),
    }


# ---------------------------------------------------------------------------
# 5) Métricas de riesgo del instrumento
# ---------------------------------------------------------------------------

def metricas_riesgo(precio: pd.Series, capital: float = 10000.0) -> dict:
    serie = precio.astype(float).dropna()
    retornos = serie.pct_change().dropna()
    vol = float(retornos.std(ddof=1) * np.sqrt(DIAS_TRABAJO))
    var_hist = float(np.percentile(retornos, 5))  # VaR 95% histórico diario
    dd = serie / serie.cummax() - 1
    peor_dia = float(retornos.min())
    caida_esperada = float(np.mean(retornos[retornos < 0])) if (retornos < 0).any() else 0.0
    recuperacion = 1 / abs(caida_esperada) if caida_esperada < 0 else float("inf")

    return {
        "volatilidad_anual": vol,
        "var_95_diario": var_hist,
        "perdida_esperada_dia": float(np.mean(retornos)),
        "max_drawdown": float(dd.min()),
        "peor_dia": peor_dia,
        "dias_recuperacion": recuperacion,
        "valor_en_riesgo": abs(var_hist) * capital,
        "capital": capital,
    }


# ---------------------------------------------------------------------------
# Utilidades de fechas
# ---------------------------------------------------------------------------

def _siguiente(fecha: pd.Timestamp) -> pd.Timestamp:
    nxt = fecha + pd.Timedelta(days=1)
    while nxt.weekday() >= 5:  # saltar fines de semana
        nxt += pd.Timedelta(days=1)
    return nxt


def _fechas_futuras(ultima: pd.Timestamp, horizonte: int) -> pd.DatetimeIndex:
    fechas, actual = [], ultima
    for _ in range(horizonte):
        actual = _siguiente(actual)
        fechas.append(actual)
    return pd.DatetimeIndex(fechas)
