"""
BerryMind — Cerebro Principal (LangGraph)
==========================================
Define el grafo de agentes usando LangGraph StateGraph.

Flujo:
    entrada → supervisor → [rag | vision→agronomy | irrigation] → salida

Uso:
    from módulo3_cerebro.brain import run_berrymind
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

    # Decisión del supervisor
    next_agent:         Optional[str]       # "rag" | "vision" | "irrigation" | "none"

    # Resultados intermedios
    vision_result:      Optional[dict]      # Resultado del análisis de visión
    rag_context:        Optional[dict]      # Contexto recuperado por RAG
    irrigation_command: Optional[dict]      # Comando de riego generado

    # Salida final
    response:           Optional[str]       # Respuesta en lenguaje natural
    responder:          Optional[str]       # Nombre del agente que respondió

    # Trazabilidad (para "Under the Hood")
    agent_log:          Optional[list]      # Lista de eventos del flujo de agentes


# ─────────────────────────────────────────────────────────────────────────────
# NODOS DEL GRAFO
# ─────────────────────────────────────────────────────────────────────────────

def node_supervisor(state: BerryMindState) -> BerryMindState:
    from módulo3_cerebro.agents.agents import supervisor_agent
    return supervisor_agent(state)


def node_vision(state: BerryMindState) -> BerryMindState:
    """Nodo de visión: analiza la imagen de hoja."""
    from módulo2_vision.vision_agent import analyze_leaf
    from módulo3_cerebro.agents.agents import _log

    _log(state, "VisionNode", f"Analizando imagen: {state.get('image_path')}")
    try:
        result = analyze_leaf(state["image_path"])
        state["vision_result"] = result
        _log(state, "VisionNode", f"✅ Resultado: {result['estado']} ({result['confianza']:.0%})")
    except Exception as e:
        state["vision_result"] = {
            "estado": "Error", "confianza": 0.0,
            "detalles": f"Error al analizar imagen: {e}"
        }
        _log(state, "VisionNode", f"❌ Error: {e}")
    return state


def node_agronomy(state: BerryMindState) -> BerryMindState:
    from módulo3_cerebro.agents.agents import agronomic_agent
    return agronomic_agent(state)


def node_rag(state: BerryMindState) -> BerryMindState:
    from módulo3_cerebro.agents.agents import rag_agent
    return rag_agent(state)


def node_irrigation(state: BerryMindState) -> BerryMindState:
    from módulo3_cerebro.agents.agents import irrigation_agent
    return irrigation_agent(state)


def node_output(state: BerryMindState) -> BerryMindState:
    """Nodo final: formatea y registra la respuesta."""
    from módulo3_cerebro.agents.agents import _log
    _log(state, "OutputNode", f"Respuesta lista. Agente: {state.get('responder', 'N/A')}")
    return state


# ─────────────────────────────────────────────────────────────────────────────
# FUNCIÓN DE ENRUTAMIENTO (Router)
# ─────────────────────────────────────────────────────────────────────────────

def route_from_supervisor(state: BerryMindState) -> str:
    """Determina el siguiente nodo basado en la decisión del supervisor."""
    next_agent = state.get("next_agent", "none")
    route_map  = {
        "rag":        "rag",
        "vision":     "vision",
        "irrigation": "irrigation",
        "none":       "output",
    }
    return route_map.get(next_agent, "output")


def route_from_vision(state: BerryMindState) -> str:
    """Después de visión, siempre va a agronomy."""
    return "agronomy"


# ─────────────────────────────────────────────────────────────────────────────
# CONSTRUCCIÓN DEL GRAFO
# ─────────────────────────────────────────────────────────────────────────────

def build_graph():
    """Construye y compila el grafo LangGraph de BerryMind."""
    from langgraph.graph import StateGraph, END

    graph = StateGraph(BerryMindState)

    # Agregar nodos
    graph.add_node("supervisor",  node_supervisor)
    graph.add_node("rag",         node_rag)
    graph.add_node("vision",      node_vision)
    graph.add_node("agronomy",    node_agronomy)
    graph.add_node("irrigation",  node_irrigation)
    graph.add_node("output",      node_output)

    # Definir punto de entrada
    graph.set_entry_point("supervisor")

    # Arista condicional desde supervisor
    graph.add_conditional_edges(
        "supervisor",
        route_from_supervisor,
        {
            "rag":        "rag",
            "vision":     "vision",
            "irrigation": "irrigation",
            "output":     "output",
        }
    )

    # Arista condicional desde vision → agronomy
    graph.add_conditional_edges(
        "vision",
        route_from_vision,
        {"agronomy": "agronomy"}
    )

    # Aristas simples al nodo de salida
    graph.add_edge("rag",        "output")
    graph.add_edge("agronomy",   "output")
    graph.add_edge("irrigation", "output")
    graph.add_edge("output",     END)

    return graph.compile()


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
