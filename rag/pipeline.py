"""
pipeline.py — Orchestrates the full RAG pipeline:
    ingest document → retrieve context → generate answer
"""
from __future__ import annotations

import os
import threading
from pathlib import Path
from typing import Callable, Optional

from .db       import init_db, insert_document, update_doc_chunk_count, get_conn
from .chunker  import process_document
from .db       import insert_chunks
from .retriever import HybridRetriever
from .llm      import llm, build_rag_prompt, build_direct_prompt, list_available_models
from .downloader import auto_download_default, model_dest_path, QWEN_MODEL, CLIP_MODEL
from .memory_manager import get_memory_manager, MemoryAwareRetriever
from .model_config import get_device_preset, model_is_multimodal, LLM_MODELS, EMBEDDING_MODELS


# Module-level retriever (shared across the whole app)
retriever = HybridRetriever(alpha=0.5)


# ------------------------------------------------------------------ #
#  Initialisation                                                      #
# ------------------------------------------------------------------ #

# Registered callbacks for auto-download progress UI
_auto_dl_progress_cb: Optional[Callable[[float, str], None]] = None
_auto_dl_done_cb:     Optional[Callable[[bool, str], None]]  = None


def register_auto_download_callbacks(
    on_progress: Optional[Callable[[float, str], None]],
    on_done:     Optional[Callable[[bool, str], None]],
) -> None:
    """
    Call from UI to receive auto-download / model-load progress events.
    If the model is already loaded by the time this is called, on_done
    fires immediately so the UI never gets stuck in the loading state.
    """
    global _auto_dl_progress_cb, _auto_dl_done_cb
    _auto_dl_progress_cb = on_progress
    _auto_dl_done_cb     = on_done

    # Race guard 1: LLM already loaded in this process
    if on_done and llm.is_loaded():
        on_done(True, "Models ready: Qwen + Nomic")
        return

    # Race guard 2: foreground service already has llama-server running —
    # skip extraction/download and connect immediately.
    import urllib.request
    try:
        with urllib.request.urlopen(
            "http://127.0.0.1:8082/health", timeout=1
        ) as r:
            if r.status == 200:
                llm._backend = "llama_server"  # mark as connected
                if on_done:
                    on_done(True, "Models ready: Qwen + Nomic (service)")
                return
    except Exception:
        pass


def init() -> None:
    """Call once at app start: set up DB, retriever, then auto-download default model."""
    init_db()
    retriever.reload()
    _start_auto_download()


def _start_auto_download() -> None:
    """Ensure Qwen + Nomic are on disk, then load Qwen and start Nomic server."""
    def _progress(frac: float, text: str):
        if _auto_dl_progress_cb:
            _auto_dl_progress_cb(frac, text)

    def _done(success: bool, _msg: str):
        """Called when BOTH models are ready on disk."""
        qwen_path  = model_dest_path(QWEN_MODEL["filename"])
        clip_path = model_dest_path(CLIP_MODEL["filename"])

        if not success:
            if _auto_dl_done_cb:
                _auto_dl_done_cb(False, _msg)
            return

        # ── Load Qwen for generation only — CLIP starts lazily on first PDF ─ #
        if not llm.is_loaded():
            load_model(
                qwen_path,
                on_progress=_progress,
                on_done=lambda ok, msg: (
                    _auto_dl_done_cb(ok, msg) if _auto_dl_done_cb else None
                ),
            )
        elif _auto_dl_done_cb:
            _auto_dl_done_cb(True, "Models ready: Qwen + CLIP")

    auto_download_default(on_progress=_progress, on_done=_done)


# ------------------------------------------------------------------ #
#  Document ingestion                                                  #
# ------------------------------------------------------------------ #

def ingest_document(
    file_path: str,
    on_done: Optional[Callable[[bool, str], None]] = None,
) -> None:
    """
    Ingest a .txt or .pdf file in a background thread.
    Starts the Nomic embedding server on first call (lazy start to save RAM).
    on_done(success: bool, message: str) is called on completion.
    """
    def _run():
        try:
            # Lazy-start CLIP server — only needed when indexing documents.
            # Starting it at app launch wastes ~300 MB RAM on devices that
            # never upload a PDF.
            import os
            clip_path = model_dest_path(CLIP_MODEL["filename"])
            if os.path.isfile(clip_path):
                from .llm import start_nomic_server, _probe_port, _NOMIC_PORT
                if not _probe_port(_NOMIC_PORT):
                    start_nomic_server(clip_path)

            name = Path(file_path).name
            doc_id = insert_document(name, file_path)
            chunks = process_document(file_path)
            insert_chunks(doc_id, chunks)
            update_doc_chunk_count(doc_id, len(chunks))
            retriever.reload()
            if on_done:
                on_done(True, f"Ingested '{name}' \u2014 {len(chunks)} chunks")
        except Exception as e:
            import traceback; traceback.print_exc()
            if on_done:
                on_done(False, f"Error: {e}")

    threading.Thread(target=_run, daemon=True).start()


# ------------------------------------------------------------------ #
#  Model management                                                    #
# ------------------------------------------------------------------ #

def load_model(
    model_path: str,
    on_progress: Optional[Callable[[float, str], None]] = None,
    on_done: Optional[Callable[[bool, str], None]] = None,
) -> None:
    """Load a GGUF model in a background thread, with live progress callbacks."""
    def _run():
        try:
            llm.load(model_path, on_progress=on_progress)
            if on_done:
                on_done(True, f"Model loaded: {Path(model_path).name}")
        except Exception as e:
            if on_done:
                on_done(False, f"Failed to load model: {e}")

    threading.Thread(target=_run, daemon=True).start()


def get_available_models() -> list[str]:
    return list_available_models()


def clear_all_documents() -> None:
    """Delete all ingested documents + chunks and reset the in-memory retriever."""
    with get_conn() as conn:
        # Delete chunks explicitly first (in case foreign_keys was OFF in old DBs)
        conn.execute("DELETE FROM chunks")
        conn.execute("DELETE FROM documents")
    retriever.reload()


def is_model_loaded() -> bool:
    return llm.is_loaded()


# ------------------------------------------------------------------ #
#  Query                                                               #
# ------------------------------------------------------------------ #

def chat_direct(
    question: str,
    history: list | None = None,
    summary: str = "",
    stream_cb: Optional[Callable[[str], None]] = None,
    on_done: Optional[Callable[[bool, str], None]] = None,
) -> None:
    """
    Chat directly with the LLM — no document retrieval.
    history: last 3 verbatim (user, assistant) turns.
    summary: compressed plain-text summary of older turns.
    """
    def _run():
        try:
            if not llm.is_loaded():
                if on_done:
                    on_done(False, "No LLM model loaded. Please load a GGUF model first.")
                return

            prompt = build_direct_prompt(question, history, summary)
            answer = llm.generate(prompt, stream_cb=stream_cb)
            answer = answer.strip()
            if on_done:
                on_done(True, answer)

        except Exception as e:
            if on_done:
                on_done(False, f"Error during inference: {e}")

    threading.Thread(target=_run, daemon=True).start()


def ask(
    question: str,
    stream_cb: Optional[Callable[[str], None]] = None,
    on_done: Optional[Callable[[bool, str], None]] = None,
) -> None:
    """
    Run a RAG query in a background thread with memory optimization.
    Automatically adjusts retrieval count based on device memory pressure.
    stream_cb: called with each new LLM token (for streaming UI)
    on_done  : called with (success, full_answer_or_error)
    """
    def _run():
        try:
            if retriever.is_empty():
                if on_done:
                    on_done(False, "No documents ingested yet.")
                return

            if not llm.is_loaded():
                if on_done:
                    on_done(False, "No LLM model loaded. Please load a GGUF model first.")
                return

            # Get memory-optimized retrieval limit
            memory_mgr = get_memory_manager()
            optimized_k = memory_mgr.get_max_retrieval_chunks()
            
            # Retrieve with memory optimization
            results = retriever.query(question, top_k=optimized_k)
            if not results:
                if on_done:
                    on_done(False, "No relevant context found.")
                return

            context_chunks = [text for text, _ in results]
            prompt = build_rag_prompt(context_chunks, question)

            answer = llm.generate(prompt, stream_cb=stream_cb)
            answer = answer.strip()

            if on_done:
                on_done(True, answer)

        except Exception as e:
            if on_done:
                on_done(False, f"Error during inference: {e}")

    threading.Thread(target=_run, daemon=True).start()


# ─────────────────────────────────────────────────────────────────── #
#  Device Configuration and Multimodal Support (Qwen 3.5 + CLIP)      #
# ─────────────────────────────────────────────────────────────────── #

def configure_rag_for_device(device_preset: str = "4gb-mobile") -> dict:
    """
    Auto-configure RAG system for current device.
    
    Returns: {
        'llm': model_key,
        'embedding': model_key,
        'multimodal': bool,
    }
    """
    # Import downloader dynamically to avoid circular imports
    from .downloader import download_model_with_fallback
    
    # Get recommended models
    preset = get_device_preset(device_preset)
    
    print(f"[pipeline] Configuring for device preset: {device_preset}")
    print(f"  LLM: {preset['llm']}")
    print(f"  Embedding: {preset['embedding']}")
    
    # Get model keys with fallback (no actual download)
    actual_llm = download_model_with_fallback(preset['llm'], model_type="llm")
    actual_embedding = download_model_with_fallback(preset['embedding'], model_type="embedding")
    
    # Load models from disk if they exist
    llm_path = model_dest_path(LLM_MODELS[actual_llm]["filename"])
    embedding_path = model_dest_path(EMBEDDING_MODELS[actual_embedding]["filename"])
    
    print(f"[pipeline] Using LLM: {actual_llm}")
    print(f"[pipeline] Using Embedding: {actual_embedding}")
    
    # Only load if models already exist on disk
    if os.path.exists(llm_path):
        print(f"[pipeline] Loading LLM: {llm_path}")
        llm.load(llm_path)
    else:
        print(f"[pipeline] LLM not found: {llm_path}")
    
    if os.path.exists(embedding_path):
        print(f"[pipeline] Embedding model ready: {embedding_path}")
    
    retriever._embedding_model_key = actual_embedding
    
    return {
        'llm': actual_llm,
        'embedding': actual_embedding,
        'multimodal': model_is_multimodal(actual_embedding),
    }


def ask_multimodal(
    question: str,
    stream_cb: Optional[Callable[[str], None]] = None,
    on_done: Optional[Callable[[bool, str], None]] = None,
) -> None:
    """
    Query RAG with multimodal support (text + images).
    Runs in background thread.
    """
    def _run():
        try:
            if not llm.is_loaded():
                if on_done:
                    on_done(False, "LLM not loaded")
                return
            
            # Multimodal retrieval
            results = retriever.query_multimodal(question, include_images=True, top_k=5)
            
            # Build prompt with text + image captions
            context_chunks = [text for text, _ in results['chunks']]
            image_captions = [img.get('caption', 'Unknown') for img in results['images']]
            
            prompt = build_rag_prompt_multimodal(
                context_chunks,
                image_captions,
                question
            )
            
            answer = llm.generate(prompt, stream_cb=stream_cb)
            if on_done:
                on_done(True, answer)
        except Exception as e:
            if on_done:
                on_done(False, f"Error: {e}")
    
    threading.Thread(target=_run, daemon=True).start()


def build_rag_prompt_multimodal(
    chunks: list[str],
    image_captions: list[str],
    question: str,
) -> str:
    """Build prompt including image context."""
    context = "\n".join(chunks)
    if image_captions:
        vision_context = "\n".join([f"[Image: {c}]" for c in image_captions])
        return f"{context}\n\nVisual content:\n{vision_context}\n\nQuestion: {question}"
    return f"{context}\n\nQuestion: {question}"


def get_rag_configuration() -> dict:
    """Get current RAG setup information."""
    return {
        'llm_loaded': llm.is_loaded(),
        'llm_backend': llm._backend if hasattr(llm, '_backend') else 'unknown',
        'retriever_ready': not retriever.is_empty(),
        'multimodal_supported': hasattr(retriever, 'query_multimodal'),
    }
