"""
BerryMind — Agentes LangGraph (Arquitectura de 6 Agentes)
=========================================================
Implementación de los 6 agentes especializados según la arquitectura propuesta:
  1. SensorAgent:    Ingesta y normaliza datos IoT.
  2. VisionAgent:    Analiza imágenes de hojas (Sano/Alerta/Botrytis).
  3. ClimateAgent:   Consulta clima (IDEAM) y evalúa riesgos externos.
  4. AgronomicAgent: Genera recomendaciones técnicas usando RAG.
  5. IrrigationAgent: Emite comandos de riego y fertirriego.
  6. MonitorAgent:   Verifica ejecución y actualiza la memoria.
"""

import sys
import os
import json
import time
from pathlib import Path
from typing import Any, Optional

# Añadir raíz al path para imports relativos
ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))


# ─────────────────────────────────────────────────────────────────────────────
# CLIENTE LLM (Groq)
# ─────────────────────────────────────────────────────────────────────────────

def _get_llm():
    """Inicializa y retorna el LLM de Groq."""
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")

    api_key = os.getenv("GROQ_API_KEY", "")
    model   = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

    if not api_key or api_key == "tu_api_key_aqui":
        # Fallback para desarrollo si no hay API key
        return None

    from langchain_groq import ChatGroq
    return ChatGroq(api_key=api_key, model_name=model, temperature=0.2, max_tokens=1500)


# ─────────────────────────────────────────────────────────────────────────────
# 1. AGENTE SENSOR — Ingesta y normaliza datos
# ─────────────────────────────────────────────────────────────────────────────

def sensor_agent(state: dict) -> dict:
    """Procesa y valida los datos de los sensores IoT."""
    _log(state, "SensorAgent", "Ingestando lecturas de sensores...")
    
    sensor_data = state.get("sensor_data")
    if not sensor_data:
        # Intentar leer el último archivo generado por el simulador si no viene en el estado
        iot_file = ROOT / "modulo1_iot" / "latest_reading.json"
        if iot_file.exists():
            with open(iot_file, "r", encoding="utf-8") as f:
                sensor_data = json.load(f)
            state["sensor_data"] = sensor_data
    
    if sensor_data:
        status = sensor_data.get("status", "NORMAL")
        _log(state, "SensorAgent", f"Datos validados. Estado actual: {status}")
    else:
        _log(state, "SensorAgent", "No se detectaron datos de sensores activos.")
        
    return state


# ─────────────────────────────────────────────────────────────────────────────
# 2. AGENTE DE IMAGEN (Vision) — Análisis fitosanitario
# ─────────────────────────────────────────────────────────────────────────────

def vision_agent(state: dict) -> dict:
    """Analiza la imagen de la hoja si existe."""
    if not state.get("image_path"):
        return state

    from modulo2_vision.vision_agent import analyze_leaf
    _log(state, "VisionAgent", f"Analizando imagen: {state['image_path']}")
    
    try:
        result = analyze_leaf(state["image_path"])
        state["vision_result"] = result
        _log(state, "VisionAgent", f"Detección completada: {result['estado']} ({result['confianza']:.0%})")
    except Exception as e:
        _log(state, "VisionAgent", f"Error en análisis de imagen: {e}")
        
    return state


# ─────────────────────────────────────────────────────────────────────────────
# 3. AGENTE CLIMÁTICO — Consulta IDEAM y riesgos
# ─────────────────────────────────────────────────────────────────────────────

def climate_agent(state: dict) -> dict:
    """Consulta estaciones climáticas externas (IDEAM) vía mock de datos."""
    _log(state, "ClimateAgent", "Consultando estaciones IDEAM en Sotaquirá...")
    
    weather_file = ROOT / "modulo1_iot" / "weather_mock.json"
    external_data = {}
    
    if weather_file.exists():
        try:
            with open(weather_file, "r", encoding="utf-8") as f:
                external_data = json.load(f)
            _log(state, "ClimateAgent", f"Datos externos recuperados de Estación: {external_data.get('estacion')}")
        except Exception as e:
            _log(state, "ClimateAgent", f"Error al leer mock de clima: {e}")

    # Simulación de datos si no hay archivo
    sensor_data = state.get("sensor_data", {})
    temp_ext = sensor_data.get("temperatura", 12.0)
    hr_ext   = sensor_data.get("humedad_relativa", 75.0)
    
    # Lógica de predicción de helada combinada (Sensores + IDEAM)
    riesgo_helada = "Bajo"
    
    # Si hay alerta naranja o probabilidad alta en IDEAM
    prob_ideam = 0.0
    if external_data.get("pronostico"):
        # Tomar la probabilidad más alta de las próximas horas
        prob_ideam = max([p.get("prob_helada", 0) for p in external_data["pronostico"][:2]])

    if temp_ext < 3.0 or prob_ideam > 0.9:
        riesgo_helada = "Crítico (Inminente)"
    elif temp_ext < 5.0 or prob_ideam > 0.7:
        riesgo_helada = "Alto (Cielo despejado + baja humedad)"
    elif prob_ideam > 0.4:
        riesgo_helada = "Moderado (Atención nocturna)"
        
    climate_info = {
        "estacion": external_data.get("estacion", "Sotaquirá-Centro"),
        "riesgo_helada": riesgo_helada,
        "probabilidad_ideam": f"{prob_ideam:.0%}",
        "alerta_ideam": external_data.get("alertas_activas", [{}])[0].get("nivel", "NINGUNA"),
        "timestamp_ideam": time.strftime("%Y-%m-%dT%H:%M:%S")
    }
    
    state["climate_info"] = climate_info
    _log(state, "ClimateAgent", f"Riesgo de helada evaluado: {riesgo_helada} (IDEAM Prob: {prob_ideam:.0%})")
    
    return state


# ─────────────────────────────────────────────────────────────────────────────
# 4. AGENTE AGRONÓMICO — El Cerebro RAG
# ─────────────────────────────────────────────────────────────────────────────

def agronomic_agent(state: dict) -> dict:
    """Integra todo el conocimiento y genera la recomendación técnica."""
    from modulo3_cerebro.rag.retriever import build_context
    
    _log(state, "AgronomicAgent", "Iniciando razonamiento agronómico...")
    
    # Construir consulta para el RAG basada en las entradas
    queries = []
    if state.get("vision_result"):
        queries.append(f"tratamiento {state['vision_result']['estado']} arándanos")
    if state.get("sensor_data", {}).get("status") != "NORMAL":
        queries.append(f"manejo emergencia {state['sensor_data']['mode']} arándanos")
    if state.get("user_input"):
        queries.append(state["user_input"])
        
    query = " ".join(queries) if queries else "manejo general arándanos Sotaquirá"
    
    context = build_context(query, k=3)
    state["rag_context"] = context
    _log(state, "AgronomicAgent", "Contexto técnico recuperado de ChromaDB.")
    
    llm = _get_llm()
    if not llm:
        state["response"] = f"**[MODO DEMO - SIN API KEY]**\n\nContexto recuperado:\n{context[:300]}..."
        _log(state, "AgronomicAgent", "⚠️ Usando modo demo por falta de API Key.")
        return state

    prompt = f"""Eres BerryMind, el Agente Agronómico experto para el Valle de Sotaquirá.
    
DATOS ACTUALES:
- Sensores: {json.dumps(state.get('sensor_data', {}), indent=2)}
- Visión: {json.dumps(state.get('vision_result', {}), indent=2)}
- Clima: {json.dumps(state.get('climate_info', {}), indent=2)}

CONTEXTO TÉCNICO:
{context}

PREGUNTA/SOLICITUD:
{state.get('user_input', 'Generar reporte de estado actual.')}

INSTRUCCIONES:
1. Analiza los riesgos detectados.
2. Da una recomendación basada estrictamente en el contexto técnico.
3. Sé preciso con dosis y productos.
4. Responde en español con formato Markdown profesional.
"""
    
    try:
        response = llm.invoke(prompt)
        state["response"] = response.content
        _log(state, "AgronomicAgent", "✅ Recomendación generada exitosamente.")
    except Exception as e:
        state["response"] = f"Error al generar respuesta: {e}"
        _log(state, "AgronomicAgent", f"❌ Error LLM: {e}")
        
    return state


# ─────────────────────────────────────────────────────────────────────────────
# 5. AGENTE DE RIEGO — Ejecución de comandos
# ─────────────────────────────────────────────────────────────────────────────

def irrigation_agent(state: dict) -> dict:
    """Determina si se requieren acciones físicas en el sistema de riego y fertirriego."""
    _log(state, "IrrigationAgent", "Evaluando requerimientos de riego y nutrición...")
    
    sensor_data = state.get("sensor_data", {})
    climate_info = state.get("climate_info", {})
    
    ph   = sensor_data.get("ph_suelo", 5.0)
    ce   = sensor_data.get("conductividad", 1.0)
    h_s  = sensor_data.get("humedad_suelo", 80)
    
    command = None
    
    # 1. Prioridad Crítica: Anti-helada
    if climate_info.get("riesgo_helada") == "Crítico (Inminente)":
        command = {
            "accion": "ACTIVAR_RIEGO_ANTIHELADA",
            "zonas": "A1-A6 (Bloque Total)",
            "prioridad": "CRÍTICA",
            "duracion": "Mientras T < 2°C",
            "mensaje": "Iniciando aspersión térmica para proteger flores y frutos."
        }
    
    # 2. Fertirriego: Ajuste de pH y Conductividad (Nutrición)
    elif ph > 5.8 or ce < 0.8:
        # Arándanos prefieren pH 4.5 - 5.5
        tipo_mezcla = "Ácida (Ajuste pH)" if ph > 5.8 else "Nutricional (Subir CE)"
        command = {
            "accion": "ACTIVAR_FERTIRRIEGO",
            "zonas": "Lote B (Biloxi)",
            "prioridad": "MEDIA",
            "mezcla": tipo_mezcla,
            "duracion": "15 minutos",
            "mensaje": f"Ajuste de nutrición detectado: pH={ph}, CE={ce}."
        }
    
    # 3. Riego Hídrico: Por baja humedad
    elif h_s < 45:
        command = {
            "accion": "ACTIVAR_RIEGO_GOTEO",
            "zonas": "Todo el predio",
            "prioridad": "ALTA",
            "duracion": "30 minutos",
            "mensaje": "Déficit hídrico detectado por sensores de suelo."
        }
    
    state["irrigation_command"] = command
    if command:
        _log(state, "IrrigationAgent", f"Comando emitido: {command['accion']} en {command['zonas']}")
    else:
        _log(state, "IrrigationAgent", "Condiciones óptimas. No se requiere riego.")
        
    return state


# ─────────────────────────────────────────────────────────────────────────────
# 6. AGENTE MONITOR — Verificación y Memoria
# ─────────────────────────────────────────────────────────────────────────────

def monitor_agent(state: dict) -> dict:
    """Verifica el flujo, guarda en memoria persistente y envía alertas simuladas."""
    _log(state, "MonitorAgent", "Verificando integridad del ciclo y persistiendo memoria...")
    
    # 1. Enviar Alerta WhatsApp (Capa 4) si hay eventos importantes
    from modulo3_cerebro.agents.whatsapp_sim import send_whatsapp_alert, format_whatsapp_message
    
    whatsapp_msg = format_whatsapp_message(state)
    priority = "ALTA" if state.get("irrigation_command") or (state.get("vision_result", {}).get("estado") == "Botrytis") else "NORMAL"
    
    send_whatsapp_alert(whatsapp_msg, priority=priority)
    state["whatsapp_preview"] = whatsapp_msg

    # 2. Preparar entrada de historial
    history_entry = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "status_final": "EXITOSO" if state.get("response") else "INCOMPLETO",
        "input": state.get("user_input") or "Auto-monitoreo",
        "agentes_activos": [log["agent"] for log in state.get("agent_log", [])],
        "alerta_emitida": True if state.get("irrigation_command") else False,
        "vision_detectada": state.get("vision_result", {}).get("estado", "N/A"),
        "comando_riego": state.get("irrigation_command", {}).get("accion", "NINGUNO")
    }
    
    # Persistencia en archivo JSON (Capa 3 - Memoria)
    log_dir = ROOT / "logs"
    log_dir.mkdir(exist_ok=True)
    history_file = log_dir / "history.json"
    
    try:
        history = []
        if history_file.exists():
            with open(history_file, "r", encoding="utf-8") as f:
                history = json.load(f)
        
        history.append(history_entry)
        # Mantener solo los últimos 100 registros
        if len(history) > 100:
            history = history[-100:]
            
        with open(history_file, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
        
        _log(state, "MonitorAgent", "Historial persistido en logs/history.json")
    except Exception as e:
        _log(state, "MonitorAgent", f"Error al guardar memoria: {e}")

    state["session_history"] = history_entry
    state["responder"] = "BerryMind (Multi-Agente)"
    
    _log(state, "MonitorAgent", "Ciclo completado. Sistema en espera.")
    return state


# ─────────────────────────────────────────────────────────────────────────────
# UTILIDAD: log de agente
# ─────────────────────────────────────────────────────────────────────────────

def _log(state: dict, agent_name: str, message: str):
    """Añade un registro al log de agentes."""
    if "agent_log" not in state:
        state["agent_log"] = []

    entry = {
        "agent":     agent_name,
        "message":   message,
        "timestamp": time.strftime("%H:%M:%S"),
    }
    state["agent_log"].append(entry)
    print(f"[{agent_name}] {message}")
