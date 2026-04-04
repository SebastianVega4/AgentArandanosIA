"""
BerryMind — Página 1: Vista UMATA / Agrónomo
=============================================
Monitoreo en tiempo real de sensores IoT del cultivo de arándanos.
Gráficas con Plotly, indicadores tipo gauge y sistema de alertas.
"""

import sys
import json
import time
import requests
from pathlib import Path
from datetime import datetime, timedelta

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

# ── Configuración de página ──────────────────────────────────────────────────
st.set_page_config(
    page_title="BerryMind — Vista UMATA",
    page_icon="📡",
    layout="wide"
)

# ── Reutilizar CSS del app principal ────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
.stApp { background: #0A0F1E !important; font-family: 'Inter', sans-serif !important; }
[data-testid="stSidebar"] { background: linear-gradient(180deg, #0D1529, #0A0F1E) !important; }
h1, h2, h3 { color: #F1F5F9 !important; font-family: 'Inter', sans-serif !important; }
p, span, .stMarkdown { color: #94A3B8 !important; }
[data-testid="stMetricValue"] { color: #F1F5F9 !important; font-size: 1.6rem !important; font-weight: 700 !important; }
.sensor-card { background: #1A2235; border: 1px solid #1E293B; border-radius: 12px; padding: 16px; margin: 6px 0; }
.alert-banner { background: rgba(239,68,68,0.1); border: 1px solid #EF4444; border-radius: 10px; padding: 12px 16px; margin: 8px 0; }
.warning-banner { background: rgba(245,158,11,0.1); border: 1px solid #F59E0B; border-radius: 10px; padding: 12px 16px; margin: 8px 0; }
.ok-banner { background: rgba(16,185,129,0.1); border: 1px solid #10B981; border-radius: 10px; padding: 12px 16px; margin: 8px 0; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# FUNCIONES DE DATOS
# ─────────────────────────────────────────────────────────────────────────────

IOT_API = "http://localhost:5001"

def get_current_data() -> dict | None:
    """Intenta leer datos del servidor IoT vía HTTP, luego del archivo."""
    # Intentar HTTP primero
    try:
        r = requests.get(f"{IOT_API}/sensors", timeout=1.5)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass

    # Fallback: leer el archivo JSON
    iot_file = ROOT / "modulo1_iot" / "latest_reading.json"
    if iot_file.exists():
        try:
            with open(iot_file) as f:
                return json.load(f)
        except Exception:
            pass

    return None


def get_history_data(n: int = 100) -> list:
    """Obtiene historial de lecturas del servidor IoT."""
    try:
        r = requests.get(f"{IOT_API}/sensors/history?n={n}", timeout=2)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass

    # Generar datos simulados si el servidor no está disponible
    from modulo1_iot.iot_simulator import load_historical_data
    return load_historical_data(hours=8, mode="normal")


def set_iot_mode(mode: str) -> bool:
    """Cambia el modo del simulador IoT vía HTTP."""
    try:
        r = requests.post(f"{IOT_API}/set_mode", json={"mode": mode}, timeout=2)
        return r.status_code == 200
    except Exception:
        return False


# ─────────────────────────────────────────────────────────────────────────────
# FUNCIONES DE GRÁFICAS
# ─────────────────────────────────────────────────────────────────────────────

PLOTLY_TEMPLATE = {
    "layout": {
        "paper_bgcolor": "#1A2235",
        "plot_bgcolor":  "#111827",
        "font":          {"color": "#94A3B8", "family": "Inter"},
        "xaxis":         {"gridcolor": "#1E293B", "linecolor": "#1E293B"},
        "yaxis":         {"gridcolor": "#1E293B", "linecolor": "#1E293B"},
        "margin":        {"l": 40, "r": 20, "t": 40, "b": 40},
    }
}


def make_gauge(value, min_val, max_val, opt_min, opt_max, title, unit, color):
    """Crea un gauge de Plotly para mostrar el valor actual de un sensor."""
    # Determinar color del indicador
    if opt_min <= value <= opt_max:
        bar_color = "#10B981"
    elif min_val <= value <= max_val:
        bar_color = "#F59E0B"
    else:
        bar_color = "#EF4444"

    fig = go.Figure(go.Indicator(
        mode  = "gauge+number",
        value = value,
        title = {"text": f"<b>{title}</b><br><span style='font-size:0.75rem'>{unit}</span>",
                 "font": {"color": "#F1F5F9", "size": 13}},
        number= {"suffix": f" {unit}", "font": {"color": "#F1F5F9", "size": 22}},
        gauge = {
            "axis": {
                "range": [min_val, max_val],
                "tickfont": {"color": "#64748B", "size": 10},
            },
            "bgcolor":     "#0A0F1E",
            "bordercolor": "#1E293B",
            "bar":    {"color": bar_color, "thickness": 0.3},
            "steps":  [
                {"range": [min_val, opt_min],  "color": "rgba(239,68,68,0.15)"},
                {"range": [opt_min, opt_max],  "color": "rgba(16,185,129,0.15)"},
                {"range": [opt_max, max_val],  "color": "rgba(239,68,68,0.15)"},
            ],
            "threshold": {
                "line":  {"color": bar_color, "width": 3},
                "value": value,
            }
        }
    ))
    fig.update_layout(
        paper_bgcolor="#1A2235",
        height=180,
        margin=dict(l=20, r=20, t=50, b=10)
    )
    return fig


def make_time_series(df: pd.DataFrame, col: str, title: str, unit: str,
                     opt_min: float, opt_max: float, color: str):
    """Crea una gráfica de serie de tiempo con banda de rango óptimo."""
    fig = go.Figure()

    # Línea principal
    fig.add_trace(go.Scatter(
        x=df["timestamp"], y=df[col],
        mode="lines",
        line={"color": color, "width": 2, "shape": "spline"},
        name=title,
        hovertemplate=f"<b>{title}</b><br>{{y:.2f}} {unit}<br>{{x}}<extra></extra>",
    ))

    # Relleno bajo la curva
    fig.add_trace(go.Scatter(
        x=df["timestamp"], y=df[col],
        mode="lines",
        line={"width": 0},
        fill="tozeroy",
        fillcolor=f"{color}22",
        showlegend=False,
        hoverinfo="skip",
    ))

    # Banda de rango óptimo
    fig.add_hrect(
        y0=opt_min, y1=opt_max,
        fillcolor="rgba(16,185,129,0.08)",
        line={"color": "rgba(16,185,129,0.4)", "width": 1, "dash": "dot"},
        annotation_text="Óptimo", annotation_position="top right",
        annotation={"font": {"color": "#10B981", "size": 10}},
    )

    fig.update_layout(
        title={"text": title, "font": {"color": "#F1F5F9", "size": 14}},
        paper_bgcolor="#1A2235",
        plot_bgcolor="#111827",
        font={"color": "#94A3B8", "family": "Inter"},
        xaxis={"gridcolor": "#1E293B", "linecolor": "#1E293B"},
        yaxis={"gridcolor": "#1E293B", "linecolor": "#1E293B",
               "title": unit, "titlefont": {"color": "#64748B"}},
        height=220,
        margin={"l": 50, "r": 20, "t": 40, "b": 20},
        showlegend=False,
        hovermode="x unified",
    )
    return fig


# ─────────────────────────────────────────────────────────────────────────────
# LAYOUT PRINCIPAL
# ─────────────────────────────────────────────────────────────────────────────

st.markdown("""
<h1 style="
    background: linear-gradient(90deg, #3B82F6, #8B5CF6);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    font-size: 1.8rem; font-weight: 700; margin-bottom: 4px;">
    📡 Vista UMATA — Monitoreo de Sensores IoT
</h1>
<p style="color:#64748B; font-size:0.85rem; margin-bottom:20px;">
    Cultivo de Arándanos — Valle de Sotaquirá, Boyacá | Actualización automática cada 5s
</p>
""", unsafe_allow_html=True)

# ── Controles de modo de simulación ─────────────────────────────────────────
with st.expander(" Control del Simulador IoT", expanded=False):
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    mode_buttons = {
        "🌤️ Normal":  "normal",
        "🌡️ Helada":  "helada",
        "☀️ Sequía":  "sequia",
        "🌧️ Lluvia":  "lluvia",
    }
    for (label, mode), col in zip(mode_buttons.items(), [col_m1, col_m2, col_m3, col_m4]):
        with col:
            if st.button(label, key=f"mode_{mode}", use_container_width=True):
                if set_iot_mode(mode):
                    st.success(f"Modo '{mode}' activado")
                else:
                    st.warning("Servidor IoT no disponible. Inicia: `python modulo1_iot/iot_simulator.py --server`")

# ── Auto-refresh ─────────────────────────────────────────────────────────────
auto_refresh = st.checkbox(" Auto-actualizar cada 5 segundos", value=True)

# Obtener datos actuales
current = get_current_data()

if current is None:
    st.warning("""
    ⚠️ **Simulador IoT no disponible**

    Para ver datos en tiempo real, inicia el simulador en otra terminal:
    ```bash
    python modulo1_iot/iot_simulator.py --server
    ```
    """)

    # Generar datos de demo
    from modulo1_iot.iot_simulator import generate_reading
    current = generate_reading(mode="normal", step=100)
    st.info(" Mostrando datos de *demostración* generados localmente.")

# ── Banner de estado general ─────────────────────────────────────────────────
status = current.get("status", "NORMAL")
mode   = current.get("mode", "normal")
ts     = current.get("timestamp_human", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

banner_css = {"NORMAL": "ok-banner", "ALERTA": "warning-banner", "CRÍTICO": "alert-banner"}
banner_icon = {"NORMAL": "✅", "ALERTA": "⚠️", "CRÍTICO": "🚨"}

alerts      = current.get("alerts", [])
alert_text  = " | ".join([f"{a['sensor']}: {a['value']}{a['unit']}" for a in alerts]) if alerts else "Todos los parámetros en rango"

st.markdown(f"""
<div class="{banner_css.get(status, 'ok-banner')}">
    <b>{banner_icon.get(status, '✅')} Estado General: {status}</b> — Modo: {mode.upper()} — Última lectura: {ts}<br>
    <span style="font-size:0.8rem; color:#94A3B8;">{alert_text}</span>
</div>
""", unsafe_allow_html=True)

# ── Métricas en tiempo real (fila de gauges) ─────────────────────────────────
st.markdown("### 📊 Valores Actuales")

sensor_config = [
    ("temperatura",     "Temperatura",    -10, 40,  10, 25,  "°C",     "#3B82F6"),
    ("humedad_relativa","Humedad Rel.",    20,  100, 60, 80,  "%",      "#8B5CF6"),
    ("ph_suelo",        "pH Suelo",        3.0, 7.0, 4.5,5.5,"pH",     "#10B981"),
    ("conductividad",   "Conductividad",   0,   4.5, 0.5,2.0, "mS/cm", "#F59E0B"),
    ("humedad_suelo",   "Hum. Suelo",      10,  100, 60, 80,  "%",      "#EC4899"),
    ("luminosidad",     "Luminosidad",     0,   80000,15000,50000,"lux","#F97316"),
]

cols = st.columns(6)
for i, (key, title, mn, mx, opt_min, opt_max, unit, color) in enumerate(sensor_config):
    with cols[i]:
        val = current.get(key, 0)
        fig = make_gauge(val, mn, mx, opt_min, opt_max, title, unit, color)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

# ── Gráficas de series de tiempo ─────────────────────────────────────────────
st.markdown("### 📈 Histórico (últimas 8 horas)")

with st.spinner("Cargando datos históricos..."):
    history = get_history_data(n=96)

if history:
    df = pd.DataFrame(history)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values("timestamp")

    col_g1, col_g2 = st.columns(2)

    with col_g1:
        fig_temp = make_time_series(df, "temperatura", "🌡️ Temperatura", "°C",
                                     10, 25, "#3B82F6")
        st.plotly_chart(fig_temp, use_container_width=True, config={"displayModeBar": False})

        fig_ph = make_time_series(df, "ph_suelo", "🧪 pH del Suelo", "pH",
                                   4.5, 5.5, "#10B981")
        st.plotly_chart(fig_ph, use_container_width=True, config={"displayModeBar": False})

        fig_cond = make_time_series(df, "conductividad", "⚡ Conductividad Eléctrica", "mS/cm",
                                     0.5, 2.0, "#F59E0B")
        st.plotly_chart(fig_cond, use_container_width=True, config={"displayModeBar": False})

    with col_g2:
        fig_hr = make_time_series(df, "humedad_relativa", "💧 Humedad Relativa", "%",
                                   60, 80, "#8B5CF6")
        st.plotly_chart(fig_hr, use_container_width=True, config={"displayModeBar": False})

        fig_hs = make_time_series(df, "humedad_suelo", "🌱 Humedad del Suelo", "%",
                                   60, 80, "#EC4899")
        st.plotly_chart(fig_hs, use_container_width=True, config={"displayModeBar": False})

        fig_lux = make_time_series(df, "luminosidad", "☀️ Luminosidad", "lux",
                                    15000, 50000, "#F97316")
        st.plotly_chart(fig_lux, use_container_width=True, config={"displayModeBar": False})

# ── Tabla de últimas lecturas ─────────────────────────────────────────────────
st.markdown("### 📋 Últimas Lecturas")
if history:
    display_df = df[["timestamp_human", "temperatura", "humedad_relativa", "ph_suelo",
                      "conductividad", "humedad_suelo", "luminosidad", "status", "mode"]].tail(20).copy()
    display_df = display_df.rename(columns={
        "timestamp_human": "Hora",
        "temperatura": "Temp (°C)",
        "humedad_relativa": "HR (%)",
        "ph_suelo": "pH",
        "conductividad": "CE (mS/cm)",
        "humedad_suelo": "Hum. Suelo (%)",
        "luminosidad": "Luz (lux)",
        "status": "Estado",
        "mode": "Modo",
    })
    st.dataframe(
        display_df[::-1],
        use_container_width=True,
        hide_index=True,
        column_config={
            "Estado": st.column_config.TextColumn("Estado"),
            "Temp (°C)": st.column_config.NumberColumn(format="%.1f"),
            "pH": st.column_config.NumberColumn(format="%.2f"),
        }
    )

# Auto-refresh
if auto_refresh:
    time.sleep(5)
    st.rerun()
