"""Dashboard de análisis y predicción bursátil (solo análisis, sin operar dinero real)."""

from __future__ import annotations

import json
import os

import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

import datos
import indicadores as ind
import modelos as mod

st.set_page_config(
    page_title="InversionDashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

ARCHIVO_WATCHLIST = os.path.join(os.path.dirname(__file__), "watchlist.json")
WATCHLIST_DEFECTO = ["SPY", "QQQ", "AAPL", "MSFT", "WALMEX.MX", "AMXB.MX"]

AVISO = (
    "**⚠️ Aviso importante:** esto es una herramienta de **análisis educativo**. "
    "No es asesoría financiera, no ejecuta operaciones y **ningún modelo puede "
    "garantizar ganancias**: los precios futuros son inciertos. Invertir siempre "
    "implica riesgo de pérdida de capital. Consulta a un asesor certificado antes "
    "de tomar decisiones con tu patrimonio."
)


# ---------------------------------------------------------------------------
# Persistencia simple de la watchlist
# ---------------------------------------------------------------------------

def cargar_watchlist() -> list[str]:
    try:
        with open(ARCHIVO_WATCHLIST, encoding="utf-8") as fh:
            datos_wl = json.load(fh)
        if isinstance(datos_wl, list) and datos_wl:
            return [str(t).upper() for t in datos_wl]
    except (OSError, json.JSONDecodeError):
        pass
    return list(WATCHLIST_DEFECTO)


def guardar_watchlista(wl: list[str]) -> None:
    try:
        with open(ARCHIVO_WATCHLIST, "w", encoding="utf-8") as fh:
            json.dump(wl, fh, indent=2)
    except OSError:
        pass


# ---------------------------------------------------------------------------
# Acceso a datos con caché
# ---------------------------------------------------------------------------

@st.cache_data(ttl=3600, show_spinner=False)
def obtener_historial(ticker: str, periodo: str):
    return datos.descargar_historial(ticker, periodo)


@st.cache_data(ttl=3600, show_spinner=False)
def obtener_fundamentales(ticker: str):
    return datos.descargar_fundamentales(ticker)


def formato_money(valor) -> str:
    if valor is None:
        return "N/D"
    if abs(valor) >= 1e9:
        return f"{valor / 1e9:,.1f} B"
    if abs(valor) >= 1e6:
        return f"{valor / 1e6:,.1f} M"
    return f"{valor:,.2f}"


def formato_pct(valor, dec=2) -> str:
    if valor is None:
        return "N/D"
    return f"{valor * 100:.{dec}f}%"


# ---------------------------------------------------------------------------
# Barra lateral
# ---------------------------------------------------------------------------

st.sidebar.title("📈 InversionDashboard")
st.sidebar.caption("Análisis y predicción · sin dinero real en juego")

watchlist = cargar_watchlist()

ticker_input = st.sidebar.text_input(
    "Símbolo (ticker)", value="SPY",
    help="Ej.: AAPL, SPY, VOO, TSLA. Mexicano: WALMEX.MX, AMXB.MX, GFNORTEO.MX",
)
periodo_label = st.sidebar.selectbox("Periodo histórico", list(datos.PERIODOS), index=1)
capital = st.sidebar.number_input(
    "Capital simulado para medir riesgo", min_value=100.0, value=10000.0, step=500.0
)

st.sidebar.subheader("Mi watchlist")
agregado = st.sidebar.text_input("Agregar símbolo", placeholder="ej. GOOGL")
if st.sidebar.button("＋ Agregar") and agregado.strip():
    t = datos.resolver_ticker(agregado)
    if t not in watchlist:
        watchlist.append(t)
        guardar_watchlista(watchlist)
        st.sidebar.success(f"Agregado: {t}")

seleccion = st.sidebar.multiselect("Tus símbolos", watchlist, default=watchlist[:1])

st.sidebar.divider()
st.sidebar.markdown(AVISO)

# ---------------------------------------------------------------------------
# Carga de datos
# ---------------------------------------------------------------------------

try:
    ticker = datos.resolver_ticker(ticker_input)
    periodo = datos.PERIODOS[periodo_label]
    with st.spinner(f"Descargando datos de {ticker}…"):
        df = obtener_historial(ticker, periodo)
        fundamentales = obtener_fundamentales(ticker)
except datos.ErrorDatos as exc:
    st.error(f"❌ {exc}")
    st.stop()
except Exception as exc:  # noqa: BLE001
    st.error(f"❌ Error inesperado obteniendo datos: {exc}")
    st.stop()

precio = df["Close"].dropna()

st.title(f"{fundamentales['nombre']}  ·  `{ticker}`")
st.caption(f"Sector: {fundamentales['sector']} · Última sesión: {df.index[-1].date()} · Datos: Yahoo Finance (pueden tener retardo)")

# ---------------------------------------------------------------------------
# 1) Cotización
# ---------------------------------------------------------------------------

st.subheader("1 · Cotización y fundamentales")

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Último precio", f"{float(precio.iloc[-1]):,.2f}")
ret_dia = float(precio.iloc[-1] / precio.iloc[-2] - 1)
c2.metric("Variación sesión", formato_pct(ret_dia))
c3.metric("PER (trailing)", "N/D" if fundamentales["per"] is None else f"{fundamentales['per']:.1f}")
c4.metric("Dividendo", "N/D" if fundamentales["dividendo"] is None else formato_pct(fundamentales["dividendo"]))
if fundamentales["rango_52s"]:
    lo, hi = fundamentales["rango_52s"]
    pos_52 = (float(precio.iloc[-1]) - lo) / (hi - lo) * 100
    c5.metric("Posición rango 52s", f"{pos_52:.0f}% (de {lo:,.0f} a {hi:,.0f})")
else:
    c5.metric("Capitalización", formato_money(fundamentales["capitalizacion"]))

if fundamentales["descripcion"]:
    st.expander("Descripción de la empresa").write(fundamentales["descripcion"][:1200])

sma50 = ind.media_movil(precio, 50)
sma200 = ind.media_movil(precio, 200)

fig = make_subplots(
    rows=3, cols=1, shared_xaxes=True, row_heights=[0.6, 0.2, 0.2],
    vertical_spacing=0.03, subplot_titles=("Precio y medias móviles", "Volumen", "RSI(14)"),
)
fig.add_trace(
    go.Candlestick(
        x=df.index, open=df["Open"], high=df["High"], low=df["Low"], close=df["Close"],
        name="Velas",
    ),
    row=1, col=1,
)
fig.add_trace(go.Scatter(x=df.index, y=sma50, name="SMA 50", line=dict(width=1.5)), row=1, col=1)
fig.add_trace(go.Scatter(x=df.index, y=sma200, name="SMA 200", line=dict(width=1.5)), row=1, col=1)
fig.add_trace(go.Bar(x=df.index, y=df["Volume"], name="Volumen", marker_color="#9aa5b1"), row=2, col=1)
fig.add_trace(go.Scatter(x=df.index, y=ind.rsi(precio), name="RSI", line=dict(color="#f39c12")), row=3, col=1)
fig.add_hline(y=70, line_dash="dot", line_color="red", row=3, col=1)
fig.add_hline(y=30, line_dash="dot", line_color="green", row=3, col=1)
fig.update_layout(height=720, xaxis_rangeslider_visible=False, margin=dict(t=40, b=20))
st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------------------------
# 2) Indicadores
# ---------------------------------------------------------------------------

st.subheader("2 · Indicadores técnicos")

rsi_ult = float(ind.rsi(precio).iloc[-1])
macd_df = ind.macd(precio)
bb_df = ind.bollinger(precio)
lectura = ind.evaluar_senal(precio, rsi_ult, macd_df, bb_df)

i1, i2, i3, i4 = st.columns(4)
i1.metric("RSI(14)", f"{rsi_ult:.1f}")
i2.metric("MACD", f"{macd_df['macd'].iloc[-1]:,.3f}", delta=f"hist {macd_df['histograma'].iloc[-1]:,.3f}")
i3.metric("SMA 50", "N/D" if lectura["sma50"] is None else f"{lectura['sma50']:,.2f}")
i4.metric("SMA 200", "N/D" if lectura["sma200"] is None else f"{lectura['sma200']:,.2f}")

st.markdown(
    f"""
| Indicador | Lectura actual |
|---|---|
| **Tendencia** | {lectura['tendencia']} |
| **RSI** | {lectura['rsi']} |
| **MACD** | {lectura['macd']} |
| **Bollinger** | {lectura['bollinger']} |
"""
)
st.caption(
    "Los indicadores describen lo que ya pasó; por sí solos no predicen el futuro "
    "ni constituyen una orden de compra o venta."
)

# ---------------------------------------------------------------------------
# 3) Predicciones
# ---------------------------------------------------------------------------

st.subheader("3 · Modelos de predicción (escenarios, no certezas)")
horizonte = st.slider("Horizonte de proyección (sesiones)", 5, 60, 20, step=5)

tab1, tab2, tab3 = st.tabs(
    ["🔮 Escenario estadístico (Holt-Winters)", "🤖 Modelo ML evaluado", "📈 Tres escenarios"]
)

with tab1:
    try:
        hw = mod.escenario_estadistico(precio, horizonte)
        fig_hw = go.Figure()
        fig_hw.add_trace(
            go.Scatter(x=precio.index[-120:], y=precio.iloc[-120:], name="Histórico", line=dict(color="#2c3e50"))
        )
        fig_hw.add_trace(
            go.Scatter(x=hw.index, y=hw["pronostico"], name="Pronóstico", line=dict(color="#2980b9", dash="dash"))
        )
        fig_hw.add_trace(
            go.Scatter(
                x=hw.index, y=hw["superior"], name="Límite superior (95%)",
                line=dict(width=0.5, color="rgba(41,128,185,0.4)"), showlegend=False,
            )
        )
        fig_hw.add_trace(
            go.Scatter(
                x=hw.index, y=hw["inferior"], name="Límite inferior (95%)",
                line=dict(width=0.5, color="rgba(41,128,185,0.4)"),
                fill="tonexty", fillcolor="rgba(41,128,185,0.15)", showlegend=False,
            )
        )
        fig_hw.update_layout(height=420, margin=dict(t=30, b=20))
        st.plotly_chart(fig_hw, use_container_width=True)
        pc, pm, pi, ps = st.columns(4)
        pc.metric("Precio actual", f"{float(precio.iloc[-1]):,.2f}")
        pm.metric("Punto medio pronóstico", f"{float(hw['pronostico'].iloc[-1]):,.2f}")
        pi.metric("Límite inferior", f"{float(hw['inferior'].iloc[-1]):,.2f}")
        ps.metric("Límite superior", f"{float(hw['superior'].iloc[-1]):,.2f}")
        st.info(
            "La banda se ensancha con el tiempo: cuanto más lejos, menos útil el "
            "pronóstico. Si el precio real sale de la banda, el modelo se equivocó "
            "— puede pasar."
        )
    except Exception as exc:  # noqa: BLE001
        st.error(f"No se pudo calcular el modelo estadístico: {exc}")

with tab2:
    try:
        ml = mod.modelo_ml(precio, horizonte)
        fig_ml = go.Figure()
        fig_ml.add_trace(
            go.Scatter(x=precio.index[-120:], y=precio.iloc[-120:], name="Histórico", line=dict(color="#2c3e50"))
        )
        fig_ml.add_trace(
            go.Scatter(x=ml["pronostico"].index, y=ml["pronostico"], name="Pronóstico ML",
                       line=dict(color="#8e44ad", dash="dash"))
        )
        fig_ml.update_layout(height=420, margin=dict(t=30, b=20))
        st.plotly_chart(fig_ml, use_container_width=True)
        m1, m2, m3 = st.columns(3)
        m1.metric("Error MAE (fuera de muestra)", f"{ml['mae']:,.2f}")
        m2.metric("Precisión direccional", f"{ml['precision_direccional']:.1f}%")
        m3.metric("Datos prueba", f"{ml['n_prueba']} sesiones")
        st.warning(ml["explicacion"])
    except Exception as exc:  # noqa: BLE001:
        st.error(f"No se pudo calcular el modelo ML: {exc}")

with tab3:
    try:
        esc = mod.escenarios_multibanda(precio, horizonte)
        fig_esc = go.Figure()
        fig_esc.add_trace(
            go.Scatter(x=precio.index[-120:], y=precio.iloc[-120:], name="Histórico", line=dict(color="#2c3e50"))
        )
        for col, color in (("alcista", "#27ae60"), ("base", "#2980b9"), ("bajista", "#c0392b")):
            fig_esc.add_trace(
                go.Scatter(x=esc.index, y=esc[col], name=col.capitalize(), line=dict(color=color, dash="dash"))
            )
        fig_esc.update_layout(height=420, margin=dict(t=30, b=20))
        st.plotly_chart(fig_esc, use_container_width=True)
        e1, e2, e3 = st.columns(3)
        e1.metric("Escenario alcista (+1σ)", f"{float(esc['alcista'].iloc[-1]):,.2f}")
        e2.metric("Escenario base", f"{float(esc['base'].iloc[-1]):,.2f}")
        e3.metric("Escenario bajista (-1σ)", f"{float(esc['bajista'].iloc[-1]):,.2f}")
        st.caption(
            "Construidos con la deriva y volatilidad históricas reales del título. "
            "No son predicciones: son bordes razonables de lo que podría ocurrir."
        )
    except Exception as exc:  # noqa: BLE001
        st.error(f"No se pudieron calcular los escenarios: {exc}")

# ---------------------------------------------------------------------------
# 4) Backtest
# ---------------------------------------------------------------------------

st.subheader("4 · Backtest: ¿le gana la estrategia a comprar y mantener?")

col_r, col_l, col_c = st.columns(3)
rapida = col_r.number_input("Media rápida", 5, 100, 50, step=5)
lenta = col_l.number_input("Media lenta", 20, 300, 200, step=10)
comision = col_c.number_input("Comisión por operación", 0.0, 0.02, 0.001, step=0.0005, format="%.4f")

if rapida >= lenta:
    st.warning("La media rápida debe ser menor que la lenta.")
else:
    try:
        bt = mod.backtest_cruce_medias(df, int(rapida), int(lenta), float(comision))
        est, bh = bt["estrategia"], bt["compraymantener"]

        b1, b2, b3, b4 = st.columns(4)
        b1.metric("Estrategia (total)", formato_pct(est["rentabilidad_total"]))
        b2.metric("Comprar y mantener", formato_pct(bh["rentabilidad_total"]))
        b3.metric("Máx. drawdown estrategia", formato_pct(est["max_drawdown"]))
        b4.metric("Operaciones", bt["operaciones"])

        eq = bt["curvas"]
        fig_bt = go.Figure()
        fig_bt.add_trace(go.Scatter(x=eq.index, y=eq["estrategia"], name="Estrategia", line=dict(color="#2980b9")))
        fig_bt.add_trace(
            go.Scatter(x=eq.index, y=eq["compraymantener"], name="Comprar y mantener",
                       line=dict(color="#7f8c8d"))
        )
        fig_bt.update_layout(
            height=400, yaxis_title="Crecimiento de 1 unidad invertida",
            margin=dict(t=30, b=20),
        )
        st.plotly_chart(fig_bt, use_container_width=True)

        st.dataframe(
            {
                "Métrica": [
                    "Rentabilidad total", "CAGR", "Volatilidad anual",
                    "Sharpe (mayor = mejor relación riesgo/beneficio)", "Máx. drawdown",
                ],
                "Estrategia": [
                    formato_pct(est["rentabilidad_total"]), formato_pct(est["cagr"]),
                    formato_pct(est["volatilidad"]), f"{est['sharpe']:.2f}",
                    formato_pct(est["max_drawdown"]),
                ],
                "Comprar y mantener": [
                    formato_pct(bh["rentabilidad_total"]), formato_pct(bh["cagr"]),
                    formato_pct(bh["volatilidad"]), f"{bh['sharpe']:.2f}",
                    formato_pct(bh["max_drawdown"]),
                ],
            },
            hide_index=True, use_container_width=True,
        )
        st.caption(
            "Backtest sobre datos pasados. Los resultados pasados NO garantizan "
            "resultados futuros: una estrategia que ganó en el histórico puede perder "
            "en los próximos años (sobreajuste)."
        )
    except ValueError as exc:
        st.warning(str(exc))
    except Exception as exc:  # noqa: BLE001
        st.error(f"Error en el backtest: {exc}")

# ---------------------------------------------------------------------------
# 5) Panel de riesgo
# ---------------------------------------------------------------------------

st.subheader("5 · Panel de riesgo")

try:
    riesgo = mod.metricas_riesgo(precio, float(capital))
    r1, r2, r3, r4 = st.columns(4)
    r1.metric("Volatilidad anual", formato_pct(riesgo["volatilidad_anual"]))
    r2.metric("VaR 95% (pérdida diaria no excedida)", formato_pct(riesgo["var_95_diario"]))
    r3.metric("Valor en riesgo (capital)", f"${riesgo['valor_en_riesgo']:,.0f}")
    r4.metric("Máx. caída histórica", formato_pct(riesgo["max_drawdown"]))
    r5, r6, r7 = st.columns(3)
    r5.metric("Peor día histórico", formato_pct(riesgo["peor_dia"]))
    r6.metric("Sesiones promedio de recuperación", f"{riesgo['dias_recuperacion']:.0f}")
    r7.metric("Rentabilidad esperada por día", formato_pct(riesgo["perdida_esperada_dia"], 3))

    st.markdown(
        f"""
**¿Qué significan estos números?**
- **Volatilidad anual {formato_pct(riesgo['volatilidad_anual'])}**: qué tanto se mueve el precio en un año típico.
- **VaR 95% = {formato_pct(riesgo['var_95_diario'])}**: en 9 de cada 10 días la pérdida diaria no supera ese nivel; el día décimo puede ser peor.
- **Valor en riesgo = ${riesgo['valor_en_riesgo']:,.0f}** sobre tu capital de ${capital:,.0f}: pérdida posible en un día "malo" al 95%.
- **Máx. caída histórica {formato_pct(riesgo['max_drawdown'])}**: la peor caída desde un pico: cuánto tendrías que aguantar sin vender.
"""
    )
except Exception as exc:  # noqa: BLE001
    st.error(f"No se pudieron calcular las métricas de riesgo: {exc}")

# ---------------------------------------------------------------------------
# Watchlist comparativa
# ---------------------------------------------------------------------------

st.subheader("6 · Comparativa de tu watchlist")

filas = []
for sym in seleccion:
    try:
        d = obtener_historial(sym, periodo)
        p = d["Close"].dropna()
        r = mod.metricas_riesgo(p, float(capital))
        filas.append(
            {
                "Símbolo": sym,
                "Precio": float(p.iloc[-1]),
                "Var. 1 sesión %": float(p.iloc[-1] / p.iloc[-2] - 1) * 100,
                "Vol. anual %": r["volatilidad_anual"] * 100,
                "Máx. caída %": r["max_drawdown"] * 100,
                "VaR 95% día %": r["var_95_diario"] * 100,
            }
        )
    except Exception as exc:  # noqa: BLE001
        filas.append({"Símbolo": sym, "Precio": None, "Error": str(exc)})

if filas:
    st.dataframe(filas, hide_index=True, use_container_width=True)
else:
    st.caption("Agrega símbolos desde la barra lateral para compararlos aquí.")

st.divider()
st.markdown(AVISO)
st.caption(
    "Datos: Yahoo Finance vía yfinance (fuente no oficial, pueden existir retrasos o "
    "errores). Modelos: Holt-Winters, Ridge (scikit-learn) y reglas de cruce de medias "
    "implementados en este proyecto."
)
