"""
BerryMind — Página 2: Vista de Campo / Bot
==========================================
Chat interactivo con el agente BerryMind + análisis de imágenes de hojas.
Permite hacer preguntas agronómicas y subir fotos para diagnóstico IA.
"""

import sys
import os
import json
import time
import tempfile
from pathlib import Path
from datetime import datetime

import streamlit as st
import plotly.graph_objects as go

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

# ── Configuración ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="BerryMind — Asistente de Campo",
    page_icon="🤖",
    layout="wide"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
.stApp { background: #0A0F1E !important; font-family: 'Inter', sans-serif !important; }

/* Mensajes de Chat */
.stChatMessage {
    border-radius: 15px !important;
    padding: 15px !important;
    margin-bottom: 10px !important;
    border: 1px solid #1E293B !important;
}
.stChatMessage[data-testid="stChatMessageUser"] {
    background: #1E293B !important;
}
.stChatMessage[data-testid="stChatMessageAssistant"] {
    background: #111827 !important;
    border-left: 4px solid #8B5CF6 !important;
}

/* Resultados de Visión */
.vision-card {
    background: #1A2235;
    border: 1px solid #1E293B;
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 20px;
}
.badge {
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 0.8rem;
    font-weight: 600;
    text-transform: uppercase;
}
.badge-sano     { background: rgba(16,185,129,0.2); color: #10B981; border: 1px solid #10B981; }
.badge-estres   { background: rgba(245,158,11,0.2);  color: #F59E0B; border: 1px solid #F59E0B; }
.badge-temprano { background: rgba(239,68,68,0.2);   color: #EF4444; border: 1px solid #EF4444; }
.badge-avanzado { background: rgba(124,58,237,0.2);  color: #A78BFA; border: 1px solid #A78BFA; }

/* Botones */
.stButton > button {
    border-radius: 8px !important;
    transition: all 0.3s ease !important;
}
.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(139, 92, 246, 0.3);
}

/* File Uploader */
[data-testid="stFileUploader"] {
    border: 2px dashed #3B82F6 !important;
    border-radius: 12px !important;
    background: #111827 !important;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# INICIALIZAR ESTADO DE LA SESIÓN
# ─────────────────────────────────────────────────────────────────────────────

if "chat_history"  not in st.session_state:
    st.session_state.chat_history   = []
if "last_vision"   not in st.session_state:
    st.session_state.last_vision    = None

# ─────────────────────────────────────────────────────────────────────────────
# UTILIDADES DE UI
# ─────────────────────────────────────────────────────────────────────────────

def make_donut_chart(stats):
    """Crea un gráfico de dona para las estadísticas de color."""
    labels = ["Verde", "Amarillo", "Necrosis", "Gris"]
    values = [stats.get("pct_verde", 0), stats.get("pct_amarillo", 0), 
              stats.get("pct_rojo_marron", 0), stats.get("pct_gris", 0)]
    colors = ["#10B981", "#F59E0B", "#EF4444", "#64748B"]
    
    fig = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.6, 
                                 marker_colors=colors, textinfo='none')])
    fig.update_layout(
        showlegend=False,
        margin=dict(l=0, r=0, t=0, b=0),
        height=140,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)"
    )
    return fig

def invoke_brain(user_input=None, image_path=None):
    from modulo3_cerebro.brain import run_berrymind
    return run_berrymind(user_input=user_input, image_path=image_path)

# ─────────────────────────────────────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────────────────────────────────────

col_h1, col_h2 = st.columns([3, 1])
with col_h1:
    st.markdown("""
    <h1 style="background: linear-gradient(90deg, #8B5CF6, #3B82F6); -webkit-background-clip: text;
               -webkit-text-fill-color: transparent; font-size: 2.2rem; font-weight: 800; margin-bottom: 0;">
        🤖 Asistente BerryMind
    </h1>
    <p style="color:#64748B; font-size:1rem;">Diagnóstico fitosanitario avanzado para arándanos</p>
    """, unsafe_allow_html=True)
with col_h2:
    if st.button("🗑️ Reiniciar Sesión", use_container_width=True):
        st.session_state.chat_history = []
        st.session_state.last_vision = None
        st.rerun()

st.divider()

# ─────────────────────────────────────────────────────────────────────────────
# CUERPO PRINCIPAL
# ─────────────────────────────────────────────────────────────────────────────

col_chat, col_tools = st.columns([1.8, 1])

with col_tools:
    st.markdown("### 📸 Análisis de Imagen")
    
    uploaded_file = st.file_uploader("Sube una foto de la hoja", type=["jpg", "png", "webp"], label_visibility="collapsed")
    
    if uploaded_file:
        st.image(uploaded_file, use_column_width=True, caption="Imagen cargada")
        if st.button("🔍 Iniciar Diagnóstico", use_container_width=True):
            with st.spinner("Analizando estructuras foliares..."):
                with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
                    tmp.write(uploaded_file.getbuffer())
                    tmp_path = tmp.name
                
                result = invoke_brain(image_path=tmp_path)
                vision = result.get("vision_result", {})
                response_text = result.get("response")
                
                if not response_text:
                    response_text = "El sistema completó el análisis pero no generó una respuesta textual. Revisa los logs técnicos."
                
                st.session_state.last_vision = vision
                
                # Integrar al chat
                st.session_state.chat_history.append({"role": "user", "content": f"Analiza esta hoja: {uploaded_file.name}", "is_image": True})
                st.session_state.chat_history.append({
                    "role": "assistant", 
                    "content": response_text,
                    "vision": vision,
                    "responder": result.get("responder", "BerryMind")
                })
                os.unlink(tmp_path)
                st.rerun()

    if st.session_state.last_vision:
        v = st.session_state.last_vision
        estado = v.get("estado", "Sano")
        badge_class = {
            "Sano": "badge-sano", 
            "Estrés / Clorosis": "badge-estres",
            "Infección Temprana": "badge-temprano",
            "Botrytis (Avanzado)": "badge-avanzado"
        }.get(estado, "badge-sano")
        
        st.markdown(f"""
        <div class="vision-card">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:15px;">
                <span class="badge {badge_class}">{estado}</span>
                <span style="color:#94A3B8; font-size:0.8rem;">Confianza: {v.get('confianza', 0):.0%}</span>
            </div>
        """, unsafe_allow_html=True)
        
        c1, c2 = st.columns([1, 1.5])
        with c1:
            if v.get("color_stats"):
                st.plotly_chart(make_donut_chart(v["color_stats"]), config={'displayModeBar': False}, use_container_width=True)
        with c2:
            st.markdown(f"<p style='font-size:0.85rem; color:#F1F5F9;'>{v.get('detalles', '')}</p>", unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("### 💡 Consultas Frecuentes")
    faqs = ["¿Tratamiento para Botrytis?", "¿Riesgo de helada hoy?", "¿PH ideal del suelo?"]
    for faq in faqs:
        if st.button(faq, use_container_width=True, key=faq):
            st.session_state.chat_history.append({"role": "user", "content": faq})
            with st.spinner("Consultando base de conocimientos..."):
                result = invoke_brain(user_input=faq)
                st.session_state.chat_history.append({"role": "assistant", "content": result.get("response", ""), "responder": result.get("responder")})
            st.rerun()

with col_chat:
    chat_box = st.container(height=600)
    with chat_box:
        if not st.session_state.chat_history:
            st.markdown("""
            <div style="text-align:center; padding: 100px 20px;">
                <h2 style="color:#F1F5F9;">¡Bienvenido a BerryMind! 🫐</h2>
                <p>Soy tu experto en cultivo de arándanos. Puedes:<br>
                1. Subir fotos de hojas para diagnóstico.<br>
                2. Consultar sobre riego, nutrición y plagas.<br>
                3. Recibir alertas basadas en sensores IoT.</p>
            </div>
            """, unsafe_allow_html=True)
        
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"], avatar="👤" if msg["role"]=="user" else "🫐"):
                if msg.get("responder"):
                    st.markdown(f"<span style='color:#8B5CF6; font-size:0.7rem; font-weight:700;'>{msg['responder'].upper()}</span>", unsafe_allow_html=True)
                st.markdown(msg["content"])
                if msg.get("vision"):
                    st.success(f"Detección: {msg['vision']['estado']}")

    user_input = st.chat_input("Escribe tu consulta aquí...")
    if user_input:
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        with st.spinner("BerryMind está razonando..."):
            result = invoke_brain(user_input=user_input)
            response_text = result.get("response")
            if not response_text:
                response_text = "Lo siento, el agente no pudo generar una respuesta en este momento. Inténtalo de nuevo."
            
            st.session_state.chat_history.append({
                "role": "assistant", 
                "content": response_text, 
                "responder": result.get("responder", "BerryMind")
            })
        st.rerun()
