"""
BerryMind — Agentes LangGraph
================================
Definición de todos los agentes del sistema BerryMind:
  - RAGAgent:        Responde preguntas con contexto de la base de conocimiento
  - AgronomicAgent:  Prescribe tratamientos tras análisis de imagen
  - IrrigationAgent: Responde a alertas IoT con comandos de riego
  - SupervisorAgent: Enruta el flujo según el tipo de entrada
"""

import sys
import os
import json
from pathlib import Path
from typing import Any

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
        raise ValueError(
            "GROQ_API_KEY no configurada. Edita el archivo berrymind/.env "
            "y coloca tu API key de https://console.groq.com/"
        )

    from langchain_groq import ChatGroq
    return ChatGroq(api_key=api_key, model_name=model, temperature=0.2, max_tokens=1500)


# ─────────────────────────────────────────────────────────────────────────────
# AGENTE RAG — Responde preguntas técnicas con contexto documental
# ─────────────────────────────────────────────────────────────────────────────

def rag_agent(state: dict) -> dict:
    """
    Consulta la base de conocimiento y usa el LLM para responder preguntas técnicas.
    Actualiza: state["response"], state["rag_context"], state["agent_log"]
    """
    from módulo3_cerebro.rag.retriever import build_context, search

    query = state.get("user_input", "")
    _log(state, "RAGAgent", f"Procesando consulta: '{query[:60]}...'")

    # Recuperar contexto relevante
    _log(state, "RAGAgent", "Buscando en ChromaDB...")
    context = build_context(query, k=3)
    raw_results = search(query, k=3)

    state["rag_context"] = {
        "context_text": context,
        "sources":      [r["source"] for r in raw_results],
        "scores":       [r["score"] for r in raw_results],
    }

    _log(state, "RAGAgent", f"Contexto recuperado de: {', '.join(set(r['source'] for r in raw_results))}")
    _log(state, "RAGAgent", "Llamando a Groq API (Llama 3)...")

    prompt = f"""Eres BerryMind, un asistente agronómico especializado en el cultivo de arándanos 
en el Valle de Sotaquirá, Boyacá, Colombia. Responde SIEMPRE en español, de forma clara, 
práctica y basada en el contexto proporcionado.

=== CONTEXTO DE LA BASE DE CONOCIMIENTO ===
{context}
===========================================

PREGUNTA DEL AGRÓNOMO/OPERARIO:
{query}

INSTRUCCIONES:
- Responde directamente a la pregunta
- Cita la fuente cuando sea posible (ej: "Según el Manual de Arándanos...")
- Si el contexto no tiene la respuesta, dilo claramente y da una recomendación general
- Mantén el tono profesional pero accesible
- Incluye acciones concretas cuando sea pertinente
"""

    try:
        llm       = _get_llm()
        response  = llm.invoke(prompt)
        answer    = response.content
        _log(state, "RAGAgent", "✅ Respuesta generada por LLM.")
    except Exception as e:
        answer = f"[Error LLM] {str(e)}\n\n**Respuesta sin LLM (usando contexto RAG):**\n{context[:500]}..."
        _log(state, "RAGAgent", f"❌ Error LLM: {e}")

    state["response"]   = answer
    state["responder"]  = "RAGAgent"
    return state


# ─────────────────────────────────────────────────────────────────────────────
# AGENTE AGRONÓMICO — Prescribe tratamientos según diagnóstico visual
# ─────────────────────────────────────────────────────────────────────────────

def agronomic_agent(state: dict) -> dict:
    """
    Recibe el resultado del análisis de visión y genera una prescripción de tratamiento.
    Actualiza: state["response"], state["agent_log"]
    """
    from módulo3_cerebro.rag.retriever import build_context

    vision_result = state.get("vision_result", {})
    estado        = vision_result.get("estado", "Desconocido")
    confianza     = vision_result.get("confianza", 0.0)
    detalles      = vision_result.get("detalles", "")

    _log(state, "AgronomicAgent", f"Recibido diagnóstico visual: {estado} ({confianza:.0%})")

    # Buscar contexto relevante según el estado detectado
    query_map = {
        "Sano":     "manejo preventivo arándanos sanos monitoreo rutinario",
        "Alerta":   "clorosis amarillamiento arándanos deficiencia hierro pH suelo",
        "Botrytis": "Botrytis cinerea tratamiento fungicida arándanos control",
    }
    rag_query = query_map.get(estado, f"tratamiento {estado} arándanos")
    _log(state, "AgronomicAgent", f"Consultando RAG: '{rag_query}'")
    context = build_context(rag_query, k=3)

    _log(state, "AgronomicAgent", "Generando prescripción agronómica...")

    prompt = f"""Eres BerryMind, un agrónomo experto en arándanos del Valle de Sotaquirá.

El sistema de visión artificial ha analizado una hoja de arándano con el siguiente resultado:
- Estado detectado: **{estado}**
- Nivel de confianza: {confianza:.0%}
- Observación: {detalles}

=== INFORMACIÓN TÉCNICA DE REFERENCIA ===
{context}
=========================================

Genera una PRESCRIPCIÓN AGRONÓMICA COMPLETA que incluya:
1. **Diagnóstico confirmado**: Explica qué significa este estado para el cultivo
2. **Nivel de urgencia**: (Rutina / Moderado / Urgente / Crítico)
3. **Acciones inmediatas** (próximas 24 horas):
4. **Tratamiento recomendado** (si aplica: productos, dosis, método de aplicación):
5. **Medidas preventivas** para evitar recurrencia:
6. **Seguimiento**: ¿Cuándo y cómo evaluar si el tratamiento está funcionando?

Responde en español, con formato claro y accionable para un operario de campo.
"""

    try:
        llm      = _get_llm()
        response = llm.invoke(prompt)
        answer   = response.content
        _log(state, "AgronomicAgent", "✅ Prescripción generada.")
    except Exception as e:
        answer = (
            f"**Diagnóstico**: {estado} ({confianza:.0%} de confianza)\n\n"
            f"**Observación**: {detalles}\n\n"
            f"[Error al obtener prescripción detallada del LLM: {e}]"
        )
        _log(state, "AgronomicAgent", f"❌ Error LLM: {e}")

    state["response"]  = answer
    state["responder"] = "AgronomicAgent"
    return state


# ─────────────────────────────────────────────────────────────────────────────
# AGENTE DE RIEGO — Responde a alertas IoT con comandos de acción
# ─────────────────────────────────────────────────────────────────────────────

def irrigation_agent(state: dict) -> dict:
    """
    Analiza la alerta IoT y genera un comando de acción + explicación en lenguaje natural.
    Actualiza: state["response"], state["irrigation_command"], state["agent_log"]
    """
    from módulo3_cerebro.rag.retriever import build_context

    sensor_data = state.get("sensor_data", {})
    alerts      = sensor_data.get("alerts", [])
    mode        = sensor_data.get("mode", "normal")
    temp        = sensor_data.get("temperatura", "N/A")
    humidity    = sensor_data.get("humedad_suelo", "N/A")
    status      = sensor_data.get("status", "NORMAL")

    _log(state, "IrrigationAgent", f"Analizando alerta IoT: status={status}, modo={mode}, T={temp}°C")

    # Determinar tipo de alerta y construir comando
    irrigation_cmd = None
    alert_type     = "general"

    if mode == "helada" or (isinstance(temp, (int, float)) and temp <= 2):
        alert_type = "helada"
        irrigation_cmd = {
            "comando":   "abrir_valvulas",
            "zonas":     ["A1", "A2", "A3", "A4", "A5", "A6"],
            "modo":      "anti_helada",
            "prioridad": "CRÍTICA",
            "razon":     f"Temperatura crítica: {temp}°C",
            "duracion":  "hasta que T > 3°C y no haya hielo visible",
        }
    elif mode == "sequia" or (isinstance(humidity, (int, float)) and humidity < 40):
        alert_type = "sequia"
        irrigation_cmd = {
            "comando":   "riego_recuperacion",
            "zonas":     ["A1", "A2", "A3", "B1", "B2", "B3"],
            "modo":      "recuperacion_hidrica",
            "prioridad": "URGENTE",
            "razon":     f"Humedad de suelo crítica: {humidity}%",
            "duracion":  "45 minutos a dosis doble",
        }
    elif mode == "lluvia" or (isinstance(humidity, (int, float)) and humidity > 90):
        alert_type = "lluvia"
        irrigation_cmd = {
            "comando":   "cerrar_valvulas",
            "zonas":     ["todas"],
            "modo":      "pausa_lluvia",
            "prioridad": "NORMAL",
            "razon":     f"Humedad de suelo excesiva: {humidity}%",
            "duracion":  "hasta que humedad baje de 80%",
        }
    else:
        irrigation_cmd = {
            "comando":   "monitoreo_continuo",
            "zonas":     [],
            "prioridad": "INFO",
            "razon":     f"Alertas detectadas: {[a['sensor'] for a in alerts]}",
        }

    state["irrigation_command"] = irrigation_cmd
    _log(state, "IrrigationAgent", f"Comando generado: {irrigation_cmd['comando']} — {irrigation_cmd['prioridad']}")

    # Buscar contexto relevante
    query_map = {
        "helada":  "helada protección riego anti-helada arándanos temperatura crítica",
        "sequia":  "sequía estrés hídrico riego recuperación arándanos",
        "lluvia":  "lluvia excesiva encharcamiento Botrytis Phytophthora arándanos",
        "general": "alerta sensores monitoreo arándanos acción correctiva",
    }
    context = build_context(query_map[alert_type], k=2)
    _log(state, "IrrigationAgent", "Contexto RAG recuperado. Llamando a LLM...")

    prompt = f"""Eres BerryMind, el agente de control de riego y emergencias del cultivo de arándanos.

=== DATOS DEL SENSOR IoT ===
{json.dumps(sensor_data, indent=2, ensure_ascii=False, default=str)}

=== COMANDO A EJECUTAR ===
{json.dumps(irrigation_cmd, indent=2, ensure_ascii=False)}

=== INFORMACIÓN TÉCNICA ===
{context}
============================

Redacta un mensaje de alerta profesional para el operario que incluya:
1. **🚨 ALERTA**: Tipo y gravedad del evento detectado
2. **📊 Datos del sensor**: Resume los valores más críticos
3. **⚡ Acción tomada**: Explica la acción automática ejecutada y por qué
4. **👷 Qué debe hacer el operario ahora**: Instrucciones claras paso a paso
5. **⏱️ Seguimiento**: Cuándo volver a revisar y qué esperar

Sé directo y claro. El operario está en campo y necesita saber exactamente qué hacer.
Responde en español.
"""

    try:
        llm      = _get_llm()
        response = llm.invoke(prompt)
        answer   = response.content
        _log(state, "IrrigationAgent", "✅ Mensaje de alerta generado.")
    except Exception as e:
        cmd   = irrigation_cmd
        answer = (
            f"**🚨 ALERTA {cmd['prioridad']}**: {cmd['razon']}\n\n"
            f"**Acción automática**: {cmd['comando']} en zonas {cmd.get('zonas', [])}\n"
            f"**Duración**: {cmd.get('duracion', 'indefinida')}\n\n"
            f"[Error LLM: {e} — Siga el protocolo estándar del manual]"
        )
        _log(state, "IrrigationAgent", f"❌ Error LLM: {e}")

    state["response"]  = answer
    state["responder"] = "IrrigationAgent"
    return state


# ─────────────────────────────────────────────────────────────────────────────
# AGENTE SUPERVISOR — Enruta el flujo según el tipo de entrada
# ─────────────────────────────────────────────────────────────────────────────

def supervisor_agent(state: dict) -> dict:
    """
    Analiza el estado actual y decide a qué agente enviar el flujo.
    Actualiza: state["next_agent"], state["agent_log"]
    """
    _log(state, "Supervisor", "Analizando tipo de entrada...")

    # Prioridad 1: Alerta IoT crítica
    sensor_data = state.get("sensor_data", {})
    if sensor_data and sensor_data.get("status") in ("ALERTA", "CRÍTICO"):
        _log(state, "Supervisor", f"→ Alerta IoT detectada (status={sensor_data['status']}). Enrutando a IrrigationAgent.")
        state["next_agent"] = "irrigation"
        return state

    # Prioridad 2: Imagen de hoja subida
    if state.get("image_path"):
        _log(state, "Supervisor", "→ Imagen detectada. Enrutando a VisionAgent → AgronomicAgent.")
        state["next_agent"] = "vision"
        return state

    # Prioridad 3: Pregunta de texto
    if state.get("user_input"):
        _log(state, "Supervisor", "→ Consulta de texto. Enrutando a RAGAgent.")
        state["next_agent"] = "rag"
        return state

    # Default
    _log(state, "Supervisor", "→ Sin entrada reconocida. Respuesta de bienvenida.")
    state["next_agent"] = "none"
    state["response"]   = (
        "¡Hola! Soy **BerryMind** 🫐, tu asistente inteligente para el cultivo de arándanos.\n\n"
        "Puedes:\n"
        "- 📸 **Subir una foto** de una hoja para diagnóstico fitosanitario\n"
        "- 💬 **Escribir una pregunta** sobre el cultivo (riego, enfermedades, nutrición)\n"
        "- 🌡️ **Monitorear sensores** en la pestaña UMATA para ver el estado del campo en tiempo real"
    )
    return state


# ─────────────────────────────────────────────────────────────────────────────
# UTILIDAD: log de agente
# ─────────────────────────────────────────────────────────────────────────────

def _log(state: dict, agent_name: str, message: str):
    """Añade un registro al log de agentes para el "Under the Hood"."""
    import time
    if "agent_log" not in state:
        state["agent_log"] = []

    entry = {
        "agent":     agent_name,
        "message":   message,
        "timestamp": time.strftime("%H:%M:%S"),
    }
    state["agent_log"].append(entry)
    print(f"[{agent_name}] {message}")
