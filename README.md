# InversionDashboard

**Español** | [English](#english)

Dashboard web de **análisis y predicción bursátil** (acciones y ETF de EE.UU. y México).
Solo análisis: **no opera ni toca tu dinero**.

> **Aviso**: esto no es asesoría financiera. Ningún modelo puede garantizar ganancias
> ni eliminar el riesgo; invertir siempre implica posibilidad de pérdida de capital.
> Consulta a un asesor certificado antes de decidir sobre tu patrimonio.

## Cómo usarlo (no sabes programar, no importa)

1. Haz **doble clic en `iniciar.bat`**.
2. La primera vez tarda 1-2 minutos (instala todo automáticamente).
3. Se abre solo en tu navegador (`http://localhost:8501`).
4. Para cerrar: cierra la ventana negra de la terminal.

Si Streamlit no abre el navegador, copia y pega `http://localhost:8501` en tu navegador.

## Qué incluye

| Sección | Qué hace |
|---|---|
| 1 · Cotización | Velas, volumen, SMA 50/200 y fundamentales (PER, dividendo, rango 52 semanas) |
| 2 · Indicadores | RSI, MACD, Bollinger y tendencia, con lectura en lenguaje llano |
| 3 · Predicciones | Tres modelos: Holt-Winters con banda 95%, modelo ML con **error real medido**, y escenarios alcista/base/bajista |
| 4 · Backtest | Estrategia de cruce de medias vs. comprar y mantener (Sharpe, drawdown, volatilidad) |
| 5 · Riesgo | Volatilidad anual, VaR 95%, valor en riesgo de tu capital, peor día histórico |
| 6 · Watchlist | Compara tus símbolos en una tabla |

## Símbolos

- EE.UU.: `AAPL`, `SPY`, `QQQ`, `TSLA`...
- México (sufijo `.MX`): `WALMEX.MX`, `AMXB.MX`, `GFNORTEO.MX`, `AMXBM.MX`...
- Tu watchlist se guarda automáticamente en `watchlist.json`.

## Sobre los datos y los modelos

- **Datos**: Yahoo Finance vía `yfinance` (fuente no oficial y gratuita; puede haber
  retrasos o fallos puntuales). Hay caché de 1 hora y reintentos automáticos.
  *Plan B si Yahoo falla mucho*: registrarse gratis en Finnhub (API oficial, 60 llamadas/min).
- **Modelos**: Holt-Winters (statsmodels), Ridge (scikit-learn) y reglas de cruce de
  medias. Todos con split entrenamiento/prueba: el error que ves es sobre datos que
  el modelo nunca vio.
- **Expectativas realistas**: un MAE de X significa que el modelo se equivoca en promedio
  por X dólares; la precisión direccional cercana a 50% indica que acierta como una moneda
  al aire. Úsalo para entender riesgo, no para creer que adivina el futuro.

## Requisitos

- Windows 10/11 con Python 3.11+ (https://www.python.org/downloads/).
- Conexión a internet para descargar datos.

## Estructura

```
InversionDashboard/
├── iniciar.bat       ← doble clic para arrancar
├── requirements.txt
├── app.py            ← interfaz (Streamlit)
├── datos.py          ← descarga de datos (yfinance)
├── indicadores.py    ← RSI, MACD, medias, Bollinger
├── modelos.py        ← predicciones, backtest, riesgo
└── watchlist.json    ← se crea solo con tus símbolos
```

---

# English

[Español](#inversiondashboard) | **English**

Web dashboard for **stock and ETF analysis and forecasting** (US and Mexican markets).
Analysis only: **it never trades or touches your money**.

> **Disclaimer**: this is not financial advice. No model can guarantee profits or
> eliminate risk; investing always involves the possibility of losing capital.
> Consult a certified advisor before making decisions about your money.

## How to use it (no programming needed)

1. **Double-click `iniciar.bat`**.
2. The first run takes 1-2 minutes (it installs everything automatically).
3. It opens in your browser (`http://localhost:8501`).
4. To close it: close the black terminal window.

If Streamlit does not open the browser, copy and paste `http://localhost:8501` into your browser.

## What it includes

| Section | What it does |
|---|---|
| 1 · Quote | Candlesticks, volume, SMA 50/200 and fundamentals (P/E, dividend, 52-week range) |
| 2 · Indicators | RSI, MACD, Bollinger Bands and trend, explained in plain language |
| 3 · Forecasts | Three models: Holt-Winters with a 95% band, an ML model with **real measured error**, and bullish/base/bearish scenarios |
| 4 · Backtest | Moving-average crossover strategy vs. buy and hold (Sharpe, drawdown, volatility) |
| 5 · Risk | Annual volatility, 95% VaR, value at risk for your capital, worst historical day |
| 6 · Watchlist | Compare your symbols in a single table |

## Symbols

- US: `AAPL`, `SPY`, `QQQ`, `TSLA`...
- Mexico (`.MX` suffix): `WALMEX.MX`, `AMXB.MX`, `GFNORTEO.MX`, `AMXBM.MX`...
- Your watchlist is saved automatically to `watchlist.json`.

## About the data and models

- **Data**: Yahoo Finance via `yfinance` (unofficial, free source; occasional delays
  or failures may occur). Includes a 1-hour cache and automatic retries.
  *Plan B if Yahoo fails often*: sign up for a free Finnhub account (official API, 60 calls/min).
- **Models**: Holt-Winters (statsmodels), Ridge (scikit-learn) and moving-average
  crossover rules. All use a train/test split: the error shown is measured on data
  the model never saw.
- **Realistic expectations**: a MAE of X means the model is off by X dollars on average;
  directional accuracy near 50% means it is as right as a coin flip. Use it to understand
  risk, not to believe it can predict the future.

## Requirements

- Windows 10/11 with Python 3.11+ (https://www.python.org/downloads/).
- Internet connection to download data.

## Structure

```
InversionDashboard/
├── iniciar.bat       ← double-click to start
├── requirements.txt
├── app.py            ← UI (Streamlit)
├── datos.py          ← data download (yfinance)
├── indicadores.py    ← RSI, MACD, moving averages, Bollinger
├── modelos.py        ← forecasts, backtest, risk
└── watchlist.json    ← created automatically with your symbols
```
