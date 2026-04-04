"""
BerryMind — RAG Retriever
==========================
Función de búsqueda semántica en ChromaDB para recuperar
contexto relevante antes de llamar al LLM.

Uso como modulo:
    from modulo3_cerebro.rag.retriever import search, get_collection_stats
    results = search("¿Cómo tratar la Botrytis en arándanos?", k=3)
"""

import sys
from pathlib import Path
from typing import Optional

BASE_DIR   = Path(__file__).parent.parent.parent
CHROMA_DIR = BASE_DIR / "chroma_db"

# Cache de cliente/colección
_client     = None
_collection = None
_embed_model = None


def _init():
    """Inicializa ChromaDB y el modelo de embeddings (lazy loading)."""
    global _client, _collection, _embed_model

    if _collection is not None:
        return True

    if not CHROMA_DIR.exists():
        print("[RAG Retriever] ⚠️  ChromaDB no encontrado. Ejecuta primero: python ingestor.py")
        return False

    try:
        import chromadb
        from sentence_transformers import SentenceTransformer

        _client     = chromadb.PersistentClient(path=str(CHROMA_DIR))
        _collection = _client.get_or_create_collection("berrymind_kb")

        if _embed_model is None:
            _embed_model = SentenceTransformer(
                "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
                device="cpu"
            )
        return True

    except Exception as e:
        print(f"[RAG Retriever] Error al inicializar: {e}")
        return False


def search(query: str, k: int = 3, min_score: float = 0.3) -> list[dict]:
    """
    Busca los k fragmentos más relevantes para la consulta dada.

    Args:
        query:     Pregunta o consulta del usuario
        k:         Número máximo de resultados a retornar
        min_score: Score mínimo de similitud (0.0 – 1.0)

    Returns:
        Lista de dicts con "text", "source", "score" y metadatos
    """
    if not _init():
        return []

    try:
        query_embedding = _embed_model.encode([query], convert_to_list=True)[0]
        results = _collection.query(
            query_embeddings=[query_embedding],
            n_results=min(k, _collection.count()),
            include=["documents", "metadatas", "distances"],
        )

        formatted = []
        for i, doc in enumerate(results["documents"][0]):
            distance = results["distances"][0][i]
            score    = 1.0 - distance   # convertir distancia coseno a similitud

            if score < min_score:
                continue

            formatted.append({
                "text":     doc,
                "source":   results["metadatas"][0][i].get("source", "desconocido"),
                "score":    round(score, 3),
                "chunk_id": results["ids"][0][i] if results.get("ids") else "",
            })

        return sorted(formatted, key=lambda x: x["score"], reverse=True)

    except Exception as e:
        print(f"[RAG Retriever] Error en búsqueda: {e}")
        return []


def build_context(query: str, k: int = 3) -> str:
    """
    Construye el bloque de contexto RAG para inyectar en el prompt del LLM.

    Returns:
        String con el contexto formateado, listo para incluir en el prompt.
    """
    results = search(query, k=k)

    if not results:
        return "No se encontró información relevante en la base de conocimiento."

    context_parts = []
    for i, r in enumerate(results, 1):
        context_parts.append(
            f"[Fragmento {i} — Fuente: {r['source']} (relevancia: {r['score']:.0%})]\n"
            f"{r['text']}"
        )

    return "\n\n---\n\n".join(context_parts)


def get_collection_stats() -> dict:
    """Retorna estadísticas del vectorstore."""
    if not _init():
        return {"error": "ChromaDB no disponible"}

    count = _collection.count()
    return {
        "total_chunks": count,
        "chroma_path":  str(CHROMA_DIR),
        "status":       "ready" if count > 0 else "empty",
    }


if __name__ == "__main__":
    # Test rápido del retriever
    print("=== Test del RAG Retriever ===\n")
    stats = get_collection_stats()
    print(f"Stats: {stats}\n")

    test_queries = [
        "¿Cómo tratar la Botrytis cinerea en arándanos?",
        "¿Qué hago si hay helada en el cultivo?",
        "¿Cuál es el pH óptimo del suelo para arándanos?",
    ]

    for query in test_queries:
        print(f"📝 Consulta: {query}")
        results = search(query, k=2)
        for r in results:
            print(f"   📄 [{r['score']:.0%}] {r['source']}: {r['text'][:120]}...")
        print()
