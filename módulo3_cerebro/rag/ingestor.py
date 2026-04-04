"""
BerryMind — RAG Ingestor
=========================
Carga documentos de la base de conocimiento (Markdown/PDF),
los convierte en chunks, genera embeddings y los guarda en ChromaDB.

Uso:
    python ingestor.py              # Ingerir todos los documentos
    python ingestor.py --rebuild    # Borrar y reconstruir el vectorstore
"""

import os
import sys
import argparse
import shutil
from pathlib import Path
from datetime import datetime

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR     = Path(__file__).parent.parent.parent  # raíz de berrymind/
KB_DIR       = BASE_DIR / "módulo3_cerebro" / "knowledge_base"
CHROMA_DIR   = BASE_DIR / "chroma_db"


def _check_deps():
    """Verifica que las dependencias estén instaladas."""
    missing = []
    try:
        import chromadb
    except ImportError:
        missing.append("chromadb")
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        missing.append("sentence-transformers")
    if missing:
        print(f"[RAG] Instala las dependencias faltantes: pip install {' '.join(missing)}")
        sys.exit(1)


def _load_documents() -> list[dict]:
    """
    Carga todos los documentos de la base de conocimiento.
    Soporta .md, .txt y .pdf (con pypdf).
    """
    docs = []

    for ext in ["*.md", "*.txt"]:
        for file_path in sorted(KB_DIR.glob(ext)):
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            docs.append({
                "content":  content,
                "source":   file_path.name,
                "type":     "markdown" if file_path.suffix == ".md" else "text",
            })
            print(f"[RAG] Cargado: {file_path.name} ({len(content)} chars)")

    for file_path in sorted(KB_DIR.glob("*.pdf")):
        try:
            from pypdf import PdfReader
            reader = PdfReader(str(file_path))
            content = "\n".join(page.extract_text() or "" for page in reader.pages)
            docs.append({
                "content": content,
                "source":  file_path.name,
                "type":    "pdf",
            })
            print(f"[RAG] PDF cargado: {file_path.name} ({len(content)} chars)")
        except Exception as e:
            print(f"[RAG] Error leyendo PDF {file_path.name}: {e}")

    if not docs:
        print(f"[RAG] ⚠️  No se encontraron documentos en: {KB_DIR}")
    return docs


def _split_into_chunks(text: str, chunk_size: int = 600, overlap: int = 100) -> list[str]:
    """
    Divide el texto en chunks con overlap para mantener contexto entre fragmentos.
    Intenta respetar saltos de párrafo.
    """
    paragraphs = text.split("\n\n")
    chunks = []
    current_chunk = ""

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        # Si el párrafo cabe en el chunk actual, añadirlo
        if len(current_chunk) + len(para) + 2 <= chunk_size:
            current_chunk += ("\n\n" if current_chunk else "") + para
        else:
            # Guardar chunk actual si tiene contenido suficiente
            if len(current_chunk) > 50:
                chunks.append(current_chunk.strip())

            # Iniciar nuevo chunk con overlap del anterior
            if current_chunk and overlap > 0:
                # Tomar las últimas palabras del chunk anterior como contexto
                words = current_chunk.split()
                overlap_text = " ".join(words[-overlap//5:]) if len(words) > overlap//5 else ""
                current_chunk = overlap_text + ("\n\n" if overlap_text else "") + para
            else:
                current_chunk = para

    if current_chunk.strip() and len(current_chunk.strip()) > 50:
        chunks.append(current_chunk.strip())

    return chunks


def build_vectorstore(rebuild: bool = False):
    """
    Construye o actualiza el vectorstore ChromaDB con los documentos de knowledge_base.
    """
    _check_deps()

    import chromadb
    from sentence_transformers import SentenceTransformer

    if rebuild and CHROMA_DIR.exists():
        print(f"[RAG] Eliminando vectorstore existente: {CHROMA_DIR}")
        shutil.rmtree(CHROMA_DIR)

    CHROMA_DIR.mkdir(exist_ok=True)

    # Inicializar ChromaDB persistente
    client     = chromadb.PersistentClient(path=str(CHROMA_DIR))
    collection = client.get_or_create_collection(
        name="berrymind_kb",
        metadata={"hnsw:space": "cosine", "description": "BerryMind Knowledge Base"}
    )

    # Cargar modelo de embeddings (local, sin GPU)
    print("[RAG] Cargando modelo de embeddings (paciencia, primera vez tarda ~30s)...")
    embed_model = SentenceTransformer(
        "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        device="cpu"
    )
    print("[RAG] Modelo de embeddings listo.")

    # Cargar y procesar documentos
    documents = _load_documents()
    if not documents:
        print("[RAG] No hay documentos para indexar.")
        return

    all_chunks = []
    all_ids    = []
    all_metas  = []

    for doc in documents:
        chunks = _split_into_chunks(doc["content"])
        print(f"[RAG] '{doc['source']}' dividido en {len(chunks)} chunks.")

        for i, chunk in enumerate(chunks):
            chunk_id = f"{doc['source']}_chunk_{i:03d}"
            # Saltar chunks ya existentes
            if not rebuild:
                existing = collection.get(ids=[chunk_id])
                if existing["ids"]:
                    continue
            all_chunks.append(chunk)
            all_ids.append(chunk_id)
            all_metas.append({
                "source":    doc["source"],
                "type":      doc["type"],
                "chunk_idx": i,
                "timestamp": datetime.now().isoformat(),
            })

    if not all_chunks:
        print("[RAG] ✅ Vectorstore ya está actualizado, no hay nuevos chunks.")
        return

    # Generar embeddings en batch
    print(f"[RAG] Generando embeddings para {len(all_chunks)} chunks...")
    embeddings = embed_model.encode(
        all_chunks,
        batch_size=16,
        show_progress_bar=True,
        convert_to_list=True,
    )

    # Añadir a ChromaDB en batches de 100
    batch_size = 100
    for i in range(0, len(all_chunks), batch_size):
        collection.add(
            documents=all_chunks[i:i+batch_size],
            embeddings=embeddings[i:i+batch_size],
            ids=all_ids[i:i+batch_size],
            metadatas=all_metas[i:i+batch_size],
        )

    total = collection.count()
    print(f"\n[RAG] ✅ Vectorstore construido exitosamente.")
    print(f"[RAG]    Documentos indexados: {len(documents)}")
    print(f"[RAG]    Total de chunks en ChromaDB: {total}")
    print(f"[RAG]    Ubicación: {CHROMA_DIR}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="BerryMind RAG Ingestor")
    parser.add_argument("--rebuild", action="store_true",
                        help="Borrar y reconstruir el vectorstore desde cero")
    args = parser.parse_args()
    build_vectorstore(rebuild=args.rebuild)
