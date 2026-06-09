"""
BerryMind — Cerebro Principal (LangGraph)
==========================================
Define el grafo de agentes usando LangGraph StateGraph.

Flujo:
    entrada → supervisor → [rag | vision→agronomy | irrigation] → salida

Uso:
    from modulo3_cerebro.brain import run_berrymind
    result = run_berrymind(user_input="¿Qué hago si hay helada?")
    result = run_berrymind(image_path="hoja.jpg")
    result = run_berrymind(sensor_data={"status": "CRÍTICO", ...})
"""

import sys
import os
from pathlib import Path
from typing import TypedDict, Optional, Any

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")


# ─────────────────────────────────────────────────────────────────────────────
# ESTADO DEL GRAFO
# ─────────────────────────────────────────────────────────────────────────────

class BerryMindState(TypedDict, total=False):
    """Estado compartido entre todos los nodos del grafo."""
    # Entradas
    user_input:         Optional[str]       # Pregunta de texto del usuario
    image_path:         Optional[str]       # Ruta a imagen de hoja subida
    sensor_data:        Optional[dict]      # Datos del sensor IoT

    # Resultados intermedios
    vision_result:      Optional[dict]      # Resultado del análisis de visión
    climate_info:       Optional[dict]      # Info del Agente Climático
    rag_context:        Optional[str]       # Contexto recuperado por RAG
    irrigation_command: Optional[dict]      # Comando de riego generado
    session_history:    Optional[dict]      # Resumen del MonitorAgent

    # Salida final
    response:           Optional[str]       # Respuesta en lenguaje natural
    responder:          Optional[str]       # Nombre del agente que respondió

    # Trazabilidad (para "Under the Hood")
    agent_log:          Optional[list]      # Lista de eventos del flujo de agentes


# ─────────────────────────────────────────────────────────────────────────────
# NODOS DEL GRAFO
# ─────────────────────────────────────────────────────────────────────────────

def node_sensor(state: BerryMindState) -> BerryMindState:
    from modulo3_cerebro.agents.agents import sensor_agent
    return sensor_agent(state)

def node_vision(state: BerryMindState) -> BerryMindState:
    from modulo3_cerebro.agents.agents import vision_agent
    return vision_agent(state)

def node_climate(state: BerryMindState) -> BerryMindState:
    from modulo3_cerebro.agents.agents import climate_agent
    return climate_agent(state)

def node_agronomy(state: BerryMindState) -> BerryMindState:
    from modulo3_cerebro.agents.agents import agronomic_agent
    return agronomic_agent(state)

def node_irrigation(state: BerryMindState) -> BerryMindState:
    from modulo3_cerebro.agents.agents import irrigation_agent
    return irrigation_agent(state)

def node_monitor(state: BerryMindState) -> BerryMindState:
    from modulo3_cerebro.agents.agents import monitor_agent
    return monitor_agent(state)


# ─────────────────────────────────────────────────────────────────────────────
# CONSTRUCCIÓN DEL GRAFO
# ─────────────────────────────────────────────────────────────────────────────

def build_graph():
    """Construye un grafo optimizado y rápido (Flujo simplificado)."""
    from langgraph.graph import StateGraph, END

    graph = StateGraph(BerryMindState)

    # Nodos esenciales
    graph.add_node("perception", perception_node) # Combina Sensor + Visión + Clima
    graph.add_node("reasoning", reasoning_node)   # Combina Agronomía + Riego
    graph.add_node("output", node_monitor)       # Monitor y Memoria

    graph.set_entry_point("perception")
    graph.add_edge("perception", "reasoning")
    graph.add_edge("reasoning", "output")
    graph.add_edge("output", END)

    return graph.compile()

def perception_node(state: BerryMindState) -> BerryMindState:
    from modulo3_cerebro.agents.agents import sensor_agent, vision_agent, climate_agent
    state = sensor_agent(state)
    state = vision_agent(state)
    state = climate_agent(state)
    return state

def reasoning_node(state: BerryMindState) -> BerryMindState:
    from modulo3_cerebro.agents.agents import agronomic_agent, irrigation_agent
    state = agronomic_agent(state)
    state = irrigation_agent(state)
    return state


# Cache del grafo compilado
_compiled_graph = None

def get_graph():
    """Retorna el grafo compilado (con cache)."""
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_graph()
    return _compiled_graph


# ─────────────────────────────────────────────────────────────────────────────
# API PÚBLICA
# ─────────────────────────────────────────────────────────────────────────────

def run_berrymind(
    user_input:  Optional[str]  = None,
    image_path:  Optional[str]  = None,
    sensor_data: Optional[dict] = None,
) -> dict:
    """
    Punto de entrada principal para ejecutar el grafo BerryMind.

    Args:
        user_input:  Pregunta de texto
        image_path:  Ruta a imagen de hoja
        sensor_data: Datos del simulador IoT

    Returns:
        dict con "response", "responder", "agent_log" y resultados intermedios
    """
    initial_state: BerryMindState = {
        "user_input":   user_input,
        "image_path":   image_path,
        "sensor_data":  sensor_data,
        "agent_log":    [],
    }

    graph  = get_graph()
    result = graph.invoke(initial_state)
    return dict(result)


# ─────────────────────────────────────────────────────────────────────────────
# PUNTO DE ENTRADA PARA TESTS
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse, json

    parser = argparse.ArgumentParser(description="BerryMind Brain — Test del grafo LangGraph")
    parser.add_argument("--test",  action="store_true", help="Ejecutar tests predefinidos")
    parser.add_argument("--query", type=str, default=None, help="Hacer una consulta de texto")
    parser.add_argument("--image", type=str, default=None, help="Analizar una imagen")
    args = parser.parse_args()

    if args.query:
        print(f"\n🤔 Consulta: {args.query}")
        result = run_berrymind(user_input=args.query)
        print(f"\n💬 Respuesta ({result.get('responder')}):\n{result.get('response')}")

    elif args.image:
        print(f"\n📸 Analizando imagen: {args.image}")
        result = run_berrymind(image_path=args.image)
        print(f"\n💬 Respuesta ({result.get('responder')}):\n{result.get('response')}")

    elif args.test:
        print("=== TEST del Cerebro BerryMind ===\n")

        # Test 1: Pregunta RAG
        print("1️⃣  Test RAG: Pregunta sobre Botrytis")
        r = run_berrymind(user_input="¿Cómo trato la Botrytis en mis arándanos?")
        print(f"   Agente: {r.get('responder')}")
        print(f"   Respuesta: {str(r.get('response', ''))[:200]}...")
        print()

        # Test 2: Alerta IoT de helada
        print("2️⃣  Test Irrigation: Alerta de helada")
        sensor = {"status": "CRÍTICO", "mode": "helada", "temperatura": -1.5,
                  "humedad_suelo": 65, "alerts": [{"sensor": "temperatura", "level": "CRÍTICO"}]}
        r = run_berrymind(sensor_data=sensor)
        print(f"   Agente: {r.get('responder')}")
        cmd = r.get("irrigation_command", {})
        print(f"   Comando: {cmd.get('comando')} — Prioridad: {cmd.get('prioridad')}")
        print()

        print("✅ Tests completados. Log del flujo:")
        for entry in r.get("agent_log", []):
            print(f"   [{entry['timestamp']}] [{entry['agent']}] {entry['message']}")
    else:
        parser.print_help()
