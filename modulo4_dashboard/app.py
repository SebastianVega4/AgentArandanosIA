"""
BerryMind — Dashboard Principal (Streamlit)
============================================
App principal del sistema BerryMind con diseño oscuro profesional.

Para ejecutar:
    streamlit run app.py
    (desde el directorio berrymind/)

Acceso: http://localhost:8501
"""

import sys
import os
from pathlib import Path

# Añadir raíz al path para imports de modulos
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

import streamlit as st

# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURACIÓN DE PÁGINA
# ─────────────────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title    = "BerryMind — Sistema IA para Arándanos",
    page_icon     = "🫐",
    layout        = "wide",
    initial_sidebar_state = "expanded",
    menu_items    = {
        "Get Help":    "https://github.com/berrymind",
        "About":       "## BerryMind 🫐\nSistema de IA para monitoreo inteligente de arándanos — Valle de Sotaquirá, Boyacá",
    }
)

# ─────────────────────────────────────────────────────────────────────────────
# CSS PERSONALIZADO — Tema oscuro premium
# ─────────────────────────────────────────────────────────────────────────────

st.markdown("""
<style>
/* ── Google Fonts ── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

/* ── Variables de color ── */
:root {
    --bg-primary:     #0A0F1E;
    --bg-secondary:   #111827;
    --bg-card:        #1A2235;
    --bg-card-hover:  #1E2A3F;
    --accent-blue:    #3B82F6;
    --accent-purple:  #8B5CF6;
    --accent-green:   #10B981;
    --accent-orange:  #F59E0B;
    --accent-red:     #EF4444;
    --accent-berry:   #7C3AED;
    --text-primary:   #F1F5F9;
    --text-secondary: #94A3B8;
    --text-muted:     #64748B;
    --border-color:   #1E293B;
    --glow-blue:      0 0 20px rgba(59,130,246,0.3);
    --glow-purple:    0 0 20px rgba(139,92,246,0.3);
    --glow-green:     0 0 20px rgba(16,185,129,0.3);
}

/* ── Fondo principal ── */
.stApp {
    background: var(--bg-primary) !important;
    font-family: 'Inter', sans-serif !important;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0D1529 0%, #0A0F1E 100%) !important;
    border-right: 1px solid var(--border-color) !important;
}

/* ── Textos ── */
h1, h2, h3, h4, h5, h6 {
    color: var(--text-primary) !important;
    font-family: 'Inter', sans-serif !important;
}

p, span, label, .stMarkdown {
    color: var(--text-secondary) !important;
    font-family: 'Inter', sans-serif !important;
}

/* ── Métricas ── */
[data-testid="stMetricValue"] {
    color: var(--text-primary) !important;
    font-size: 1.8rem !important;
    font-weight: 700 !important;
}
[data-testid="stMetricLabel"] {
    color: var(--text-secondary) !important;
    font-size: 0.8rem !important;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

/* ── Cards personalizados ── */
.berrymind-card {
    background: var(--bg-card);
    border: 1px solid var(--border-color);
    border-radius: 12px;
    padding: 20px;
    margin: 8px 0;
    transition: all 0.2s ease;
}
.berrymind-card:hover {
    background: var(--bg-card-hover);
    border-color: var(--accent-blue);
    box-shadow: var(--glow-blue);
}

/* ── Badge de estado ── */
.status-badge {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.05em;
    text-transform: uppercase;
}
.status-ok       { background: rgba(16,185,129,0.15); color: #10B981; border: 1px solid #10B981; }
.status-alert    { background: rgba(245,158,11,0.15); color: #F59E0B; border: 1px solid #F59E0B; }
.status-critical { background: rgba(239,68,68,0.15);  color: #EF4444; border: 1px solid #EF4444; }

/* ── Logo BerryMind en sidebar ── */
.berrymind-logo {
    text-align: center;
    padding: 20px 10px;
}
.berrymind-logo h1 {
    font-size: 1.8rem !important;
    font-weight: 700 !important;
    background: linear-gradient(135deg, #8B5CF6, #3B82F6);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin: 0 !important;
}
.berrymind-logo p {
    font-size: 0.75rem !important;
    color: var(--text-muted) !important;
    margin: 4px 0 0 0 !important;
}

/* ── Input de chat ── */
.stChatInput textarea {
    background: var(--bg-card) !important;
    border: 1px solid var(--border-color) !important;
    color: var(--text-primary) !important;
    font-family: 'Inter', sans-serif !important;
}

/* ── Botones ── */
.stButton > button {
    background: linear-gradient(135deg, #7C3AED, #3B82F6) !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    transition: all 0.2s ease !important;
}
.stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: var(--glow-purple) !important;
}

/* ── Select box ── */
.stSelectbox > div > div {
    background: var(--bg-card) !important;
    border-color: var(--border-color) !important;
    color: var(--text-primary) !important;
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    background: var(--bg-secondary) !important;
    border-radius: 10px;
    padding: 4px;
}
.stTabs [data-baseweb="tab"] {
    color: var(--text-secondary) !important;
    font-weight: 500 !important;
}
.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, #7C3AED22, #3B82F622) !important;
    color: var(--text-primary) !important;
    border-radius: 8px !important;
}

/* ── Expander ── */
details > summary {
    color: var(--text-primary) !important;
    font-weight: 500 !important;
}

/* ── Divider ── */
hr { border-color: var(--border-color) !important; }

/* ── Scrollbar elegante ── */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: var(--bg-primary); }
::-webkit-scrollbar-thumb { background: var(--border-color); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--accent-blue); }

/* ── Animación de pulso para alertas ── */
@keyframes pulse-red {
    0%, 100% { opacity: 1; }
    50%       { opacity: 0.6; }
}
.pulsing { animation: pulse-red 1.5s infinite; }

/* ── Código/logs ── */
code, pre {
    font-family: 'JetBrains Mono', monospace !important;
    background: var(--bg-secondary) !important;
    color: #A5F3FC !important;
    border-radius: 6px !important;
}

/* ── Alert blocks ── */
.stAlert {
    border-radius: 10px !important;
}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────

with st.sidebar:
    # Logo
    st.markdown("""
    <div class="berrymind-logo">
        <h1>🫐 BerryMind</h1>
        <p>Sistema IA para Arándanos</p>
        <p style="font-size:0.65rem; margin-top:2px; color:#4B5563;">Valle de Sotaquirá • Boyacá, Colombia</p>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    # Estado del sistema
    st.markdown("**🔌 Estado del Sistema**")

    # Intentar leer el estado del IoT simulator
    iot_file = ROOT / "modulo1_iot" / "latest_reading.json"
    iot_status = "Desconectado"
    iot_color  = "status-alert"

    if iot_file.exists():
        import json
        try:
            with open(iot_file) as f:
                iot_data = json.load(f)
            iot_status = iot_data.get("status", "NORMAL")
            iot_color  = {
                "NORMAL":   "status-ok",
                "ALERTA":   "status-alert",
                "CRÍTICO":  "status-critical",
            }.get(iot_status, "status-alert")
        except Exception:
            pass

    st.markdown(f"""
    <div style="margin: 8px 0;">
        <span style="color:#94A3B8; font-size:0.8rem;">IoT Simulator</span><br>
        <span class="status-badge {iot_color}">{iot_status}</span>
    </div>
    """, unsafe_allow_html=True)

    # Verificar ChromaDB
    chroma_dir = ROOT / "chroma_db"
    rag_status = "Listo" if chroma_dir.exists() and any(chroma_dir.iterdir()) else "Sin indexar"
    rag_color  = "status-ok" if rag_status == "Listo" else "status-alert"
    st.markdown(f"""
    <div style="margin: 8px 0;">
        <span style="color:#94A3B8; font-size:0.8rem;">Base de Conocimiento RAG</span><br>
        <span class="status-badge {rag_color}">{rag_status}</span>
    </div>
    """, unsafe_allow_html=True)

    # Verificar .env / API key
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
    api_key = os.getenv("GROQ_API_KEY", "")
    if api_key and api_key != "tu_api_key_aqui" and len(api_key) > 20:
        llm_status, llm_color = "Configurado", "status-ok"
    else:
        llm_status, llm_color = "Sin API Key", "status-critical"

    st.markdown(f"""
    <div style="margin: 8px 0;">
        <span style="color:#94A3B8; font-size:0.8rem;">Groq LLM (Llama 3)</span><br>
        <span class="status-badge {llm_color}">{llm_status}</span>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    # Info del proyecto
    st.markdown("""
    <div style="font-size:0.75rem; color:#4B5563; text-align:center; padding:10px 0;">
        <b style="color:#64748B;">BerryMind v1.0</b><br>
        Proyecto de Grado UPTC<br>
        Ingeniería Electrónica<br>
        <br>
        <div style="background: rgba(59,130,246,0.1); padding: 8px; border-radius: 6px; border: 1px solid rgba(59,130,246,0.2); margin-top:10px;">
            🛡️ <b>Protección de Datos</b><br>
            Cumple con la <b>Ley 1581 de 2012</b>.<br>
            Toda la información del predio y del productor es tratada de forma confidencial.
        </div>
        <br>
        Tecnologías:<br>
        LangGraph • Groq • ChromaDB<br>
        YOLOv8 • Streamlit • Python
    </div>
    """, unsafe_allow_html=True)

    if llm_status == "Sin API Key":
        st.warning("⚠️ Configura tu GROQ_API_KEY en el archivo `.env`")


# ─────────────────────────────────────────────────────────────────────────────
# PÁGINA PRINCIPAL (Landing)
# ─────────────────────────────────────────────────────────────────────────────

st.markdown("""
<div style="text-align:center; padding: 40px 0 20px 0;">
    <h1 style="
        font-size: 3rem;
        font-weight: 800;
        background: linear-gradient(135deg, #8B5CF6 0%, #3B82F6 50%, #10B981 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 8px;
    ">🫐 BerryMind</h1>
    <p style="font-size:1.1rem; color:#94A3B8; max-width:600px; margin:0 auto;">
        Sistema de Inteligencia Artificial para Monitoreo Inteligente de Arándanos<br>
        <span style="color:#64748B; font-size:0.9rem;">Valle de Sotaquirá, Boyacá, Colombia</span>
    </p>
</div>
""", unsafe_allow_html=True)

# Cards de las 3 vistas principales
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div class="berrymind-card" style="text-align:center; border-top: 3px solid #3B82F6;">
        <div style="font-size:2.5rem; margin-bottom:12px;">📡</div>
        <h3 style="color:#F1F5F9 !important; margin:0 0 8px 0;">Vista UMATA</h3>
        <p style="color:#94A3B8; font-size:0.85rem; margin:0;">
            Monitoreo en tiempo real de sensores IoT.<br>
            Temperatura, humedad, pH del suelo y más.
        </p>
        <br>
        <span style="color:#3B82F6; font-size:0.8rem;">→ Página 1</span>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="berrymind-card" style="text-align:center; border-top: 3px solid #8B5CF6;">
        <div style="font-size:2.5rem; margin-bottom:12px;">🤖</div>
        <h3 style="color:#F1F5F9 !important; margin:0 0 8px 0;">Vista de Campo</h3>
        <p style="color:#94A3B8; font-size:0.85rem; margin:0;">
            Chat inteligente con BerryMind.<br>
            Sube fotos de hojas para diagnóstico IA.
        </p>
        <br>
        <span style="color:#8B5CF6; font-size:0.8rem;">→ Página 2</span>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="berrymind-card" style="text-align:center; border-top: 3px solid #10B981;">
        <div style="font-size:2.5rem; margin-bottom:12px;">⚙️</div>
        <h3 style="color:#F1F5F9 !important; margin:0 0 8px 0;">Under the Hood</h3>
        <p style="color:#94A3B8; font-size:0.85rem; margin:0;">
            Vista técnica del flujo de agentes IA.<br>
            Para jurados y evaluadores.
        </p>
        <br>
        <span style="color:#10B981; font-size:0.8rem;">→ Página 3</span>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# Arquitectura del sistema
st.markdown("### Arquitectura del Sistema")

st.markdown("""
```
┌──────────────────────────────────────────────────────────────────┐
│                         BERRYMIND SYSTEM                         │
│                                                                  │
│  ┌─────────────┐    ┌──────────────┐    ┌────────────────────┐  │
│  │ IoT Sim     │    │ Visión IA    │    │ Cerebro LangGraph  │  │
│  │ (Flask:5001)│───▶│ YOLOv8+HSV  │───▶│ Supervisor Agent   │  │
│  │ 6 Sensores  │    │ 3 estados    │    │ ┌──────────────┐   │  │
│  └─────────────┘    └──────────────┘    │ │  RAG Agent   │   │  │
│                                         │ │  Agronomic   │   │  │
│  ┌─────────────────────────────────┐    │ │  Irrigation  │   │  │
│  │ ChromaDB (Local)                │───▶│ └──────────────┘   │  │
│  │ Manual Arándanos + Protocolos   │    │ Groq API (Llama 3) │  │
│  └─────────────────────────────────┘    └────────────────────┘  │
│                              │                                   │
│                              ▼                                   │
│                   ┌──────────────────┐                          │
│                   │ Dashboard        │                          │
│                   │ Streamlit :8501  │                          │
│                   └──────────────────┘                          │
└──────────────────────────────────────────────────────────────────┘
```
""")

# Instrucciones de inicio rápido
with st.expander(" Instrucciones de inicio rápido"):
    st.markdown("""
    ### 1. Configura tu API Key de Groq
    ```bash
    # Edita berrymind/.env y coloca tu key de https://console.groq.com/
    GROQ_API_KEY=gsk_tu_key_aqui
    ```

    ### 2. Instala las dependencias
    ```bash
    pip install -r requirements.txt
    ```

    ### 3. Indexa la base de conocimiento (RAG)
    ```bash
    python modulo3_cerebro/rag/ingestor.py
    ```

    ### 4. Inicia el simulador IoT (en otra terminal)
    ```bash
    python modulo1_iot/iot_simulator.py --server --mode normal
    # Para simular helada:
    python modulo1_iot/iot_simulator.py --server --mode helada
    ```

    ### 5. Ya puedes usar el dashboard
    Navega a las páginas desde el menú lateral izquierdo.
    """)
