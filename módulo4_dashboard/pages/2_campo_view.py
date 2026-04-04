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

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

# ── Configuración ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="BerryMind — Vista de Campo",
    page_icon="🤖",
    layout="wide"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
.stApp { background: #0A0F1E !important; font-family: 'Inter', sans-serif !important; }
[data-testid="stSidebar"] { background: linear-gradient(180deg, #0D1529, #0A0F1E) !important; }
h1, h2, h3 { color: #F1F5F9 !important; }
p, span, .stMarkdown { color: #94A3B8 !important; }
.chat-msg-user { background: linear-gradient(135deg, #3B82F6, #8B5CF6); color: white; border-radius: 12px 12px 4px 12px; padding: 12px 16px; margin: 8px 0; }
.chat-msg-bot  { background: #1A2235; border: 1px solid #1E293B; border-radius: 12px 12px 12px 4px; padding: 12px 16px; margin: 8px 0; }
.vision-result-sano     { background: rgba(16,185,129,0.1); border: 1px solid #10B981; border-radius: 10px; padding: 16px; margin: 10px 0; }
.vision-result-alerta   { background: rgba(245,158,11,0.1);  border: 1px solid #F59E0B; border-radius: 10px; padding: 16px; margin: 10px 0; }
.vision-result-botrytis { background: rgba(239,68,68,0.1);   border: 1px solid #EF4444; border-radius: 10px; padding: 16px; margin: 10px 0; }
.stButton > button { background: linear-gradient(135deg, #7C3AED, #3B82F6) !important; color: white !important; border: none !important; border-radius: 8px !important; font-weight: 600 !important; }
[data-testid="stFileUploader"] { background: #1A2235 !important; border: 2px dashed #8B5CF6 !important; border-radius: 12px !important; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# INICIALIZAR ESTADO DE LA SESIÓN
# ─────────────────────────────────────────────────────────────────────────────

if "chat_history"  not in st.session_state:
    st.session_state.chat_history   = []
if "agent_log"     not in st.session_state:
    st.session_state.agent_log      = []
if "last_vision"   not in st.session_state:
    st.session_state.last_vision    = None

# ─────────────────────────────────────────────────────────────────────────────
# FUNCIÓN PRINCIPAL: Invocar al cerebro BerryMind
# ─────────────────────────────────────────────────────────────────────────────

def invoke_brain(user_input=None, image_path=None, sensor_data=None):
    """Llama al grafo LangGraph y retorna la respuesta."""
    try:
        from módulo3_cerebro.brain import run_berrymind
        result = run_berrymind(
            user_input  = user_input,
            image_path  = image_path,
            sensor_data = sensor_data,
        )
        # Acumular logs del agente
        st.session_state.agent_log.extend(result.get("agent_log", []))
        return result
    except ImportError as e:
        return {
            "response":  f"⚠️ Error al importar el cerebro: {e}\n\nVerifica que has instalado todas las dependencias:\n```bash\npip install -r requirements.txt\n```",
            "responder": "Sistema",
            "agent_log": [],
        }
    except Exception as e:
        return {
            "response":  f"❌ Error inesperado: {str(e)}",
            "responder": "Sistema",
            "agent_log": [],
        }

# ─────────────────────────────────────────────────────────────────────────────
# LAYOUT
# ─────────────────────────────────────────────────────────────────────────────

st.markdown("""
<h1 style="background: linear-gradient(90deg, #8B5CF6, #3B82F6); -webkit-background-clip: text;
           -webkit-text-fill-color: transparent; font-size: 1.8rem; font-weight: 700; margin-bottom: 4px;">
    🤖 Vista de Campo — Asistente BerryMind
</h1>
<p style="color:#64748B; font-size:0.85rem; margin-bottom:20px;">
    Chatea con la IA agronómica o sube una foto de una hoja para diagnóstico instantáneo
</p>
""", unsafe_allow_html=True)

# Dos columnas: chat izquierda, herramientas derecha
col_chat, col_tools = st.columns([2, 1])

# ── COLUMNA DERECHA: Herramientas ────────────────────────────────────────────
with col_tools:

    # Upload de imagen
    st.markdown("### 📸 Diagnóstico Visual de Hoja")
    st.markdown("""
    <p style="font-size:0.8rem; color:#64748B;">
    Sube una foto de la hoja del arándano. La IA detectará si está:<br>
    🟢 Sana · 🟡 En Alerta · 🔴 Con Botrytis
    </p>
    """, unsafe_allow_html=True)

    uploaded_file = st.file_uploader(
        "Selecciona una imagen",
        type=["jpg", "jpeg", "png", "webp"],
        key="leaf_upload",
        label_visibility="collapsed"
    )

    if uploaded_file:
        st.image(uploaded_file, caption="Imagen cargada", use_column_width=True)

        if st.button("🔍 Analizar con IA", use_container_width=True, key="btn_analyze"):
            with st.spinner("🧠 BerryMind está analizando la hoja..."):
                # Guardar en archivo temporal
                with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
                    tmp.write(uploaded_file.getbuffer())
                    tmp_path = tmp.name

                result = invoke_brain(image_path=tmp_path)

                # Guardar resultado de visión
                vision = result.get("vision_result", {})
                st.session_state.last_vision = vision

                # Añadir al chat
                st.session_state.chat_history.append({
                    "role":     "user",
                    "content":  f"📸 [Imagen subida: {uploaded_file.name}]",
                    "type":     "image",
                })
                st.session_state.chat_history.append({
                    "role":     "assistant",
                    "content":  result.get("response", "Sin respuesta"),
                    "responder": result.get("responder", "AgronomicAgent"),
                    "vision":   vision,
                    "type":     "vision_response",
                })

            os.unlink(tmp_path)
            st.rerun()

    # Resultado de visión en tiempo real
    if st.session_state.last_vision:
        v = st.session_state.last_vision
        estado    = v.get("estado", "Sano")
        confianza = v.get("confianza", 0.0)
        css_map   = {"Sano": "vision-result-sano", "Alerta": "vision-result-alerta", "Botrytis": "vision-result-botrytis"}
        icon_map  = {"Sano": "🟢", "Alerta": "🟡", "Botrytis": "🔴"}

        st.markdown(f"""
        <div class="{css_map.get(estado, 'vision-result-sano')}">
            <b style="font-size:1.1rem; color:#F1F5F9;">{icon_map.get(estado,'⚪')} {estado}</b><br>
            <span style="font-size:0.8rem; color:#94A3B8;">Confianza: {confianza:.0%} · Método: {v.get('metodo','N/A')}</span>
        </div>
        """, unsafe_allow_html=True)

        if v.get("color_stats"):
            cs = v["color_stats"]
            cols_cs = st.columns(3)
            for col_c, (label, key, color) in zip(cols_cs, [
                ("Verde", "pct_verde", "#10B981"),
                ("Amarillo", "pct_amarillo", "#F59E0B"),
                ("Gris", "pct_gris", "#94A3B8"),
            ]):
                with col_c:
                    st.markdown(f"""
                    <div style="text-align:center; background:#111827; border-radius:8px; padding:8px;">
                        <div style="color:{color}; font-size:1.2rem; font-weight:700;">{cs.get(key, 0):.0f}%</div>
                        <div style="color:#64748B; font-size:0.65rem;">{label}</div>
                    </div>
                    """, unsafe_allow_html=True)

    st.divider()

    # Preguntas rápidas
    st.markdown("### 💡 Preguntas Rápidas")
    quick_questions = [
        "¿Cuáles son los síntomas de la Botrytis?",
        "¿Qué hago si hay helada en el cultivo?",
        "¿Cuál es el pH óptimo del suelo?",
        "¿Cómo controlo los thrips?",
        "¿Cuándo debo fertilizar?",
        "¿Cuál es el riego ideal para arándanos?",
    ]

    for q in quick_questions:
        if st.button(q, key=f"quick_{q[:20]}", use_container_width=True):
            with st.spinner("🤔 BerryMind está pensando..."):
                result = invoke_brain(user_input=q)
            st.session_state.chat_history.append({"role": "user", "content": q, "type": "text"})
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": result.get("response", "Sin respuesta"),
                "responder": result.get("responder", "RAGAgent"),
                "type": "text",
            })
            st.rerun()

    # Botón limpiar chat
    if st.button("🗑️ Limpiar conversación", use_container_width=True):
        st.session_state.chat_history = []
        st.session_state.last_vision  = None
        st.rerun()


# ── COLUMNA IZQUIERDA: Chat ──────────────────────────────────────────────────
with col_chat:
    st.markdown("### 💬 Chat con BerryMind")

    # Contenedor del chat con scroll
    chat_container = st.container()

    with chat_container:
        if not st.session_state.chat_history:
            st.markdown("""
            <div style="text-align:center; padding: 40px 20px;">
                <div style="font-size:3rem; margin-bottom:16px;">🫐</div>
                <h3 style="color:#F1F5F9;">¡Hola! Soy BerryMind</h3>
                <p style="color:#64748B;">
                    Tu asistente inteligente para el cultivo de arándanos.<br>
                    Hazme una pregunta o sube una foto de una hoja para comenzar.
                </p>
            </div>
            """, unsafe_allow_html=True)
        else:
            for msg in st.session_state.chat_history:
                if msg["role"] == "user":
                    with st.chat_message("user", avatar="👤"):
                        st.markdown(msg["content"])
                else:
                    agent = msg.get("responder", "BerryMind")
                    agent_icons = {
                        "SensorAgent":     "📡",
                        "VisionAgent":     "👁️",
                        "ClimateAgent":    "☁️",
                        "AgronomicAgent":  "🌿",
                        "IrrigationAgent": "💧",
                        "MonitorAgent":    "🖥️",
                        "RAGAgent":        "📚",
                        "Sistema":         "⚙️",
                    }
                    icon = agent_icons.get(agent, "🫐")

                    with st.chat_message("assistant", avatar=icon):
                        if "Multi-Agente" in agent:
                            st.markdown(f"**[{agent}]** 🤖")
                        else:
                            st.markdown(f"**[{agent}]** {icon}")
                        st.markdown(msg["content"])

    # Input de chat
    user_question = st.chat_input("Escribe tu pregunta sobre el cultivo de arándanos...")

    if user_question:
        st.session_state.chat_history.append({"role": "user", "content": user_question, "type": "text"})

        with st.spinner("🧠 BerryMind está procesando tu consulta..."):
            result = invoke_brain(user_input=user_question)

        st.session_state.chat_history.append({
            "role":     "assistant",
            "content":  result.get("response", "Sin respuesta"),
            "responder": result.get("responder", "RAGAgent"),
            "type":     "text",
        })
        st.rerun()
