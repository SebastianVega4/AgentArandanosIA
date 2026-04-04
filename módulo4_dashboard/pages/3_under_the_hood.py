"""
BerryMind — Página 3: Under the Hood (Vista Técnica para Jurados)
=================================================================
Muestra en tiempo real el flujo de agentes LangGraph, el contexto RAG
recuperado, las métricas del LLM y la arquitectura del sistema.
"""

import sys
import json
import time
from pathlib import Path
from datetime import datetime

import streamlit as st

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

# ── Configuración ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="BerryMind — Under the Hood",
    page_icon="⚙️",
    layout="wide"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
.stApp { background: #0A0F1E !important; font-family: 'Inter', sans-serif !important; }
[data-testid="stSidebar"] { background: linear-gradient(180deg, #0D1529, #0A0F1E) !important; }
h1, h2, h3 { color: #F1F5F9 !important; }
p, span, .stMarkdown { color: #94A3B8 !important; }
.agent-node {
    background: #1A2235; border-radius: 10px; padding: 14px;
    border: 1px solid #1E293B; margin: 6px 0;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.8rem;
    transition: all 0.2s;
}
.agent-node.active {
    border-color: #3B82F6;
    box-shadow: 0 0 15px rgba(59,130,246,0.3);
    background: #1E2A3F;
}
.log-entry {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.75rem;
    padding: 4px 8px;
    border-left: 3px solid;
    margin: 2px 0;
    border-radius: 0 4px 4px 0;
}
.log-supervisor  { border-color: #F59E0B; background: rgba(245,158,11,0.05); color: #F59E0B; }
.log-ragagent    { border-color: #3B82F6; background: rgba(59,130,246,0.05); color: #A5D8FF; }
.log-visionnode  { border-color: #8B5CF6; background: rgba(139,92,246,0.05); color: #C4B5FD; }
.log-agronomicagent { border-color: #10B981; background: rgba(16,185,129,0.05); color: #6EE7B7; }
.log-irrigationagent { border-color: #EF4444; background: rgba(239,68,68,0.05); color: #FCA5A5; }
.log-outputnode  { border-color: #94A3B8; background: rgba(148,163,184,0.05); color: #94A3B8; }
.metric-pill {
    display: inline-block; padding: 4px 12px; border-radius: 20px;
    font-family: 'JetBrains Mono', monospace; font-size: 0.8rem; margin: 3px;
}
.stButton > button { background: linear-gradient(135deg, #7C3AED, #3B82F6) !important; color: white !important; border: none !important; border-radius: 8px !important; font-weight: 600 !important; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────────────────────────────────────

st.markdown("""
<h1 style="background: linear-gradient(90deg, #10B981, #3B82F6); -webkit-background-clip: text;
           -webkit-text-fill-color: transparent; font-size: 1.8rem; font-weight: 700; margin-bottom: 4px;">
    ⚙️ Under the Hood — Flujo Interno del Sistema IA
</h1>
<p style="color:#64748B; font-size:0.85rem; margin-bottom:20px;">
    Vista técnica para jurados: observe cómo BerryMind toma decisiones en tiempo real.
</p>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# LAYOUT: 3 columnas
# ─────────────────────────────────────────────────────────────────────────────

col_graph, col_logs, col_rag = st.columns([1, 1.2, 1])

# ── COLUMNA 1: Diagrama del Grafo LangGraph ───────────────────────────────────
with col_graph:
    st.markdown("### 🗺️ Grafo de 6 Agentes LangGraph")

    # Obtener el último agente activo del log de sesión
    last_logs  = st.session_state.get("agent_log", [])
    last_agent = last_logs[-1]["agent"] if last_logs else None

    nodes = [
        ("sensor",      "SensorAgent",    "#3B82F6", "📡 Sensor",      "Ingesta y normaliza datos IoT"),
        ("vision",      "VisionAgent",    "#8B5CF6", "👁️ Visión",      "YOLOv8/HSV → análisis foliar"),
        ("climate",     "ClimateAgent",   "#06B6D4", "☁️ Climático",   "Consulta IDEAM y evalúa riesgos"),
        ("agronomy",    "AgronomicAgent", "#10B981", "🌿 Agronómico",  "Razonamiento RAG + Llama 3"),
        ("irrigation",  "IrrigationAgent","#EF4444", "💧 Riego",       "Emite comandos de actuación"),
        ("monitor",     "MonitorAgent",   "#94A3B8", "🖥️ Monitor",     "Verifica y actualiza memoria"),
    ]

    for node_id, node_name, color, label, desc in nodes:
        is_active = last_agent and last_agent.lower() == node_name.lower()
        active_class = "active" if is_active else ""
        active_glow  = f"box-shadow: 0 0 20px {color}55;" if is_active else ""

        st.markdown(f"""
        <div class="agent-node {active_class}" style="{active_glow} border-color: {color if is_active else '#1E293B'};">
            <div style="color:{color}; font-weight:700; font-size:0.85rem">{label}</div>
            <div style="color:#F1F5F9; font-size:0.7rem; margin-top:2px">{desc}</div>
            {"<div style='color:#F59E0B; font-size:0.65rem; margin-top:4px'>▶ ACTIVO</div>" if is_active else ""}
        </div>
        """, unsafe_allow_html=True)

        # Flecha de conexión (excepto el último)
        if node_id != "monitor":
            st.markdown("""
            <div style="text-align:center; color:#1E293B; font-size:1.2rem; margin:-4px 0;">↕</div>
            """, unsafe_allow_html=True)

    # Aristas condicionales
    st.markdown("""
    <div style="background:#111827; border-radius:8px; padding:10px; margin-top:12px; font-family:'JetBrains Mono'; font-size:0.7rem;">
        <div style="color:#64748B; margin-bottom:6px;">Arquitectura de Flujo:</div>
        <div style="color:#94A3B8; padding-left:4px;">Ciclo continuo de monitoreo 360°:</div>
        <div style="color:#94A3B8; padding-left:12px;">1. Captura de datos (IoT)</div>
        <div style="color:#94A3B8; padding-left:12px;">2. Análisis visual (Hojas)</div>
        <div style="color:#94A3B8; padding-left:12px;">3. Contexto climático (IDEAM)</div>
        <div style="color:#94A3B8; padding-left:12px;">4. Inteligencia RAG (Cerebro)</div>
        <div style="color:#94A3B8; padding-left:12px;">5. Actuación física (Válvulas)</div>
        <div style="color:#94A3B8; padding-left:12px;">6. Supervisión de ciclo (Monitor)</div>
    </div>
    """, unsafe_allow_html=True)


# ── COLUMNA 2: Log en tiempo real ────────────────────────────────────────────
with col_logs:
    st.markdown("### 📋 Traza de Ejecución")

    agent_log = st.session_state.get("agent_log", [])

    if not agent_log:
        st.markdown("""
        <div style="text-align:center; padding:30px; color:#4B5563;">
            <div style="font-size:2rem; margin-bottom:10px;">💤</div>
            <p>Sin actividad aún.<br>
            Usa el chat o el analizador de imágenes para ver el flujo de agentes aquí.</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Mostrar los últimos 50 eventos
        log_css_map = {
            "SensorAgent":     "log-supervisor",
            "VisionAgent":     "log-visionnode",
            "ClimateAgent":    "log-ragagent",
            "AgronomicAgent":  "log-agronomicagent",
            "IrrigationAgent": "log-irrigationagent",
            "MonitorAgent":    "log-outputnode",
        }

        for entry in reversed(agent_log[-50:]):
            agent   = entry.get("agent", "Sistema")
            message = entry.get("message", "")
            ts      = entry.get("timestamp", "")
            css     = log_css_map.get(agent, "log-outputnode")

            st.markdown(f"""
            <div class="log-entry {css}">
                <span style="color:#4B5563; font-size:0.65rem;">[{ts}]</span>
                <span style="font-weight:600;"> {agent}</span>: {message}
            </div>
            """, unsafe_allow_html=True)

    # Botón de limpiar logs
    col_l1, col_l2 = st.columns(2)
    with col_l1:
        if st.button("🗑️ Limpiar logs", use_container_width=True):
            st.session_state.agent_log = []
            st.rerun()
    with col_l2:
        st.download_button(
            "📥 Exportar logs",
            data=json.dumps(agent_log, indent=2, ensure_ascii=False),
            file_name=f"berrymind_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            use_container_width=True,
        )

    st.divider()

    # Test del sistema en esta misma página
    st.markdown("### 🧪 Tests del Sistema")

    test_options = {
        "Consulta RAG: Botrytis":        ("rag",        "¿Cómo trato la Botrytis en arándanos?", None, None),
        "Consulta RAG: pH":              ("rag",        "¿Cuál es el pH óptimo del suelo?", None, None),
        "Alerta IoT: Helada":            ("irrigation", None, None, {"status": "CRÍTICO", "mode": "helada", "temperatura": -1.5, "humedad_suelo": 65, "alerts": [{"sensor": "temperatura", "level": "CRÍTICO"}]}),
        "Alerta IoT: Sequía":            ("irrigation", None, None, {"status": "CRÍTICO", "mode": "sequia", "temperatura": 28, "humedad_suelo": 22, "alerts": [{"sensor": "humedad_suelo", "level": "CRÍTICO"}]}),
        "Imágenes de prueba: Sano":      ("vision_test","sano", None, None),
        "Imágenes de prueba: Botrytis":  ("vision_test","botrytis", None, None),
    }

    selected_test = st.selectbox("Seleccionar test:", list(test_options.keys()), key="test_select")

    if st.button("▶️ Ejecutar Test", use_container_width=True, key="run_test"):
        test_type, query, img, sensor = test_options[selected_test]

        with st.spinner(f"Ejecutando: {selected_test}..."):
            try:
                if test_type == "rag":
                    from módulo3_cerebro.brain import run_berrymind
                    result = run_berrymind(user_input=query)
                    st.session_state.agent_log.extend(result.get("agent_log", []))
                    st.success(f"✅ Respondió: {result.get('responder')}")
                    with st.expander("Ver respuesta"):
                        st.markdown(result.get("response", "")[:500] + "...")

                elif test_type == "irrigation":
                    from módulo3_cerebro.brain import run_berrymind
                    result = run_berrymind(sensor_data=sensor)
                    st.session_state.agent_log.extend(result.get("agent_log", []))
                    cmd = result.get("irrigation_command", {})
                    st.success(f"✅ Comando: {cmd.get('comando')} — Prioridad: {cmd.get('prioridad')}")

                elif test_type == "vision_test":
                    test_dir = ROOT / "módulo2_vision" / "test_images"
                    img_path = test_dir / f"{query}.jpg"
                    if not img_path.exists():
                        from módulo2_vision.vision_agent import generate_test_images
                        generate_test_images()
                    from módulo2_vision.vision_agent import analyze_leaf
                    result = analyze_leaf(str(img_path))
                    st.success(f"✅ Estado: {result.get('estado')} — Confianza: {result.get('confianza'):.0%}")

            except Exception as e:
                st.error(f"❌ Error: {e}")

        st.rerun()


# ── COLUMNA 3: Contexto RAG + Métricas ───────────────────────────────────────
with col_rag:
    st.markdown("### 🔍 Estado del RAG")

    # Stats de ChromaDB
    try:
        from módulo3_cerebro.rag.retriever import get_collection_stats
        stats = get_collection_stats()
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            st.metric("Chunks indexados", stats.get("total_chunks", 0))
        with col_s2:
            st.metric("Estado", "✅ Listo" if stats.get("status") == "ready" else "⚠️ Vacío")
    except Exception as e:
        st.warning(f"ChromaDB no disponible: {e}")

    st.divider()

    # Búsqueda de prueba en RAG
    st.markdown("### 🔎 Probar Búsqueda RAG")
    rag_query = st.text_input("Consulta de búsqueda:", placeholder="ej: helada protección arándanos")

    if rag_query:
        with st.spinner("Buscando..."):
            try:
                from módulo3_cerebro.rag.retriever import search
                results = search(rag_query, k=3)
                for i, r in enumerate(results, 1):
                    with st.expander(f"📄 Fragmento {i} — {r['source']} ({r['score']:.0%})"):
                        st.markdown(f"```\n{r['text'][:400]}...\n```")
            except Exception as e:
                st.error(f"Error: {e}")

    st.divider()

    # Información técnica del sistema
    st.markdown("### 🏗️ Stack Tecnológico")

    tech_stack = [
        ("🔮 LLM",      "Groq (Llama 3.1-8B)",      "#8B5CF6"),
        ("📚 RAG",      "LangChain + ChromaDB",       "#3B82F6"),
        ("🧠 Orquesta", "LangGraph StateGraph",        "#F59E0B"),
        ("👁️ Visión",   "YOLOv8n / OpenCV HSV",      "#8B5CF6"),
        ("🔠 Embedds",  "paraphrase-multilingual",    "#10B981"),
        ("📡 IoT",      "Flask + threading",           "#EC4899"),
        ("📊 UI",       "Streamlit + Plotly",          "#F97316"),
    ]

    for label, value, color in tech_stack:
        st.markdown(f"""
        <div style="display:flex; justify-content:space-between; align-items:center;
                    background:#1A2235; border-radius:8px; padding:8px 12px; margin:4px 0;
                    border-left: 3px solid {color};">
            <span style="color:#94A3B8; font-size:0.8rem;">{label}</span>
            <span style="color:{color}; font-size:0.75rem; font-family:'JetBrains Mono';">{value}</span>
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    # Últimas métricas (si están disponibles en session_state)
    st.markdown("### 📊 Métricas de Sesión")
    n_messages  = len([m for m in st.session_state.get("chat_history", []) if m["role"] == "assistant"])
    n_log_items = len(st.session_state.get("agent_log", []))

    col_m1, col_m2 = st.columns(2)
    with col_m1:
        st.metric("Consultas atendidas", n_messages)
    with col_m2:
        st.metric("Eventos de agente", n_log_items)
