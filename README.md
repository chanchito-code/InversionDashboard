# InversionDashboard

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
