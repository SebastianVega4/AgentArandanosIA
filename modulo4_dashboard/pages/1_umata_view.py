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
from datetime import datetime

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

# ── Configuración de página ──────────────────────────────────────────────────
st.set_page_config(
    page_title="BerryMind — Vista UMATA",
    page_icon="📡",
    layout="wide"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
.stApp { background: #0A0F1E !important; font-family: 'Inter', sans-serif !important; }

/* Tarjetas de métricas */
.metric-card {
    background: #1A2235;
    border: 1px solid #1E293B;
    border-radius: 12px;
    padding: 15px;
    text-align: center;
}
.metric-value {
    font-size: 1.8rem;
    font-weight: 700;
    color: #F1F5F9;
}
.metric-label {
    font-size: 0.8rem;
    color: #94A3B8;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

/* Alertas */
.alert-box {
    padding: 15px;
    border-radius: 10px;
    margin-bottom: 15px;
    border-left: 5px solid;
}
.alert-critical { background: rgba(239, 68, 68, 0.1); border-color: #EF4444; color: #EF4444; }
.alert-warning  { background: rgba(245, 158, 11, 0.1); border-color: #F59E0B; color: #F59E0B; }
.alert-normal   { background: rgba(16, 185, 129, 0.1); border-color: #10B981; color: #10B981; }

/* Mapa de lotes */
.lot-map {
    background: #111827;
    border-radius: 15px;
    padding: 20px;
    border: 1px solid #1E293B;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# FUNCIONES DE DATOS
# ─────────────────────────────────────────────────────────────────────────────

def get_current_data():
    iot_file = ROOT / "modulo1_iot" / "latest_reading.json"
    if iot_file.exists():
        with open(iot_file) as f: return json.load(f)
    from modulo1_iot.iot_simulator import generate_reading
    return generate_reading(mode="normal")

def get_history_data():
    from modulo1_iot.iot_simulator import load_historical_data
    return load_historical_data(hours=12)

# ─────────────────────────────────────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────────────────────────────────────

col_t1, col_t2 = st.columns([3, 1])
with col_t1:
    st.markdown("""
    <h1 style="background: linear-gradient(90deg, #3B82F6, #8B5CF6); -webkit-background-clip: text;
               -webkit-text-fill-color: transparent; font-size: 2.2rem; font-weight: 800; margin-bottom: 0;">
        📡 Panel UMATA IoT
    </h1>
    <p style="color:#64748B; font-size:1rem;">Monitoreo en tiempo real — Sotaquirá, Boyacá</p>
    """, unsafe_allow_html=True)
with col_t2:
    st.markdown(f"<div style='text-align:right; color:#94A3B8; font-size:0.8rem; margin-top:20px;'>Actualizado: {datetime.now().strftime('%H:%M:%S')}</div>", unsafe_allow_html=True)

st.divider()

# ─────────────────────────────────────────────────────────────────────────────
# CUERPO PRINCIPAL
# ─────────────────────────────────────────────────────────────────────────────

current = get_current_data()
status = current.get("status", "NORMAL")
alert_class = {"NORMAL": "alert-normal", "ALERTA": "alert-warning", "CRÍTICO": "alert-critical"}.get(status, "alert-normal")

st.markdown(f"""
<div class="alert-box {alert_class}">
    <b style="font-size:1.1rem;">ESTADO DEL SISTEMA: {status}</b><br>
    Modo de simulación activo: {current.get('mode', 'Desconocido').upper()}
</div>
""", unsafe_allow_html=True)

# Fila 1: Métricas principales
m1, m2, m3, m4, m5, m6 = st.columns(6)
metrics = [
    ("🌡️ Temp", "temperatura", "°C"),
    ("💧 Hum. R", "humedad_relativa", "%"),
    ("🧪 pH", "ph_suelo", ""),
    ("⚡ CE", "conductividad", "mS/cm"),
    ("🌱 Hum. S", "humedad_suelo", "%"),
    ("☀️ Luz", "luminosidad", "lux")
]

for col, (label, key, unit) in zip([m1, m2, m3, m4, m5, m6], metrics):
    with col:
        val = current.get(key, 0)
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{val:.1f}<span style="font-size:0.9rem; font-weight:400;">{unit}</span></div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("---")

# Fila 2: Mapa y Gauges
col_left, col_right = st.columns([1.5, 1])

with col_left:
    st.markdown("### 🗺️ Mapa de Lotes (Estado Espacial)")
    # Simulación de mapa de calor por lotes
    lotes = pd.DataFrame({
        "Lote": ["Lote A (Biloxi)", "Lote B (Legacy)", "Lote C (Duke)", "Lote D (Bluecrop)"],
        "Humedad": [75, 82, 68, 71],
        "Salud": [95, 88, 72, 91],
        "x": [1, 2, 1, 2],
        "y": [1, 1, 2, 2]
    })
    fig_map = px.scatter(lotes, x="x", y="y", size="Humedad", color="Salud", 
                         text="Lote", color_continuous_scale="RdYlGn",
                         range_color=[60, 100], size_max=60)
    fig_map.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False, xaxis_visible=False, yaxis_visible=False,
        height=350, margin=dict(l=0, r=0, t=0, b=0)
    )
    st.plotly_chart(fig_map, use_container_width=True, config={'displayModeBar': False})

with col_right:
    st.markdown("### 📈 Tendencias Críticas")
    history = pd.DataFrame(get_history_data())
    history["timestamp"] = pd.to_datetime(history["timestamp"])
    
    fig_trend = go.Figure()
    fig_trend.add_trace(go.Scatter(x=history["timestamp"], y=history["temperatura"], name="Temp", line=dict(color="#3B82F6", width=3)))
    fig_trend.add_trace(go.Scatter(x=history["timestamp"], y=history["humedad_suelo"], name="Hum. S", line=dict(color="#10B981", width=3)))
    fig_trend.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=300, margin=dict(l=0, r=0, t=30, b=0),
        xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor="#1E293B")
    )
    st.plotly_chart(fig_trend, use_container_width=True, config={'displayModeBar': False})

# Fila 3: Alertas detalladas y Registro
st.markdown("### 📋 Registro de Alertas Recientes")
if current.get("alerts"):
    for alert in current["alerts"]:
        st.warning(f"**ALERTA EN {alert['sensor'].upper()}:** El valor actual ({alert['value']}{alert['unit']}) está fuera del rango óptimo.")
else:
    st.success("No hay alertas activas en los sensores. Todo opera bajo parámetros normales.")

if st.checkbox("Mostrar tabla de datos crudos"):
    st.dataframe(history.tail(20), use_container_width=True)

# Auto-refresh
time.sleep(5)
st.rerun()
