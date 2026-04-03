"""
Model configuration for Qwen 3.5 + Multimodal Embeddings support.
Supports model selection, device profiles, auto-fallback chains.
"""

LLM_MODELS = {
    "qwen3.5-1b-q4": {
        "label": "Qwen 3.5 1B Q4 (1.5 GB) [UPGRADED]",
        "repo_id": "Qwen/Qwen3.5-1B-Instruct-GGUF",
        "filename": "Qwen3.5-1B-Instruct-Q4_K_M.gguf",
        "size_mb": 1536,
        "context_window": 32768,
        "parameters": "1B",
        "is_fallback": False,
    },
}

EMBEDDING_MODELS = {
    "uae-small-v1": {
        "label": "UAE-Small-v1 (50 MB) [UPGRADED - MTEB 0.91]",
        "repo_id": "WhereIsAI/UAE-Large-V1",
        "filename": "ggml-model-q4_k_m.gguf",
        "size_mb": 50,
        "dimensions": 1024,
        "multimodal": False,
    },
}

DEVICE_PRESETS = {
    "4gb-mobile": {
        "llm": "qwen3.5-1b-q4",
        "embedding": "uae-small-v1",
        "max_context": 512,  # Practical limit on 4GB device
    },
}


def get_device_preset(device_class: str) -> dict:
    """Get recommended model setup for device."""
    return DEVICE_PRESETS.get(device_class, DEVICE_PRESETS["4gb-mobile"])


def model_is_multimodal(model_key: str) -> bool:
    """Check if embedding supports multimodal (text + images)."""
    model = EMBEDDING_MODELS.get(model_key, {})
    return model.get("multimodal", False)
