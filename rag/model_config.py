"""
Model configuration for Qwen 3.5 + Multimodal Embeddings support.
Supports model selection, device profiles, auto-fallback chains.
"""

LLM_MODELS = {
    "qwen2.5-1.5b-q4": {
        "label": "Qwen 2.5-1.5B Q4 (1.1 GB) [Current Default]",
        "repo_id": "Qwen/Qwen2.5-1.5B-Instruct-GGUF",
        "filename": "qwen2.5-1.5b-instruct-q4_k_m.gguf",
        "size_mb": 1120,
        "context_window": 512,
        "parameters": "1.5B",
        "is_fallback": False,
    },
    "qwen3.5-1b-q4": {
        "label": "Qwen 3.5 1B Q4 (1.5 GB) [NEW - Better Reasoning]",
        "repo_id": "Qwen/Qwen3.5-1B-Instruct-GGUF",  # Or 2.5-3B as proxy
        "filename": "qwen3.5-1b-instruct-q4_k_m.gguf",
        "size_mb": 1536,
        "context_window": 32768,
        "parameters": "1B",
        "is_fallback": False,
    },
}

EMBEDDING_MODELS = {
    "nomic-q4": {
        "label": "Nomic Embed Text Q4 (80 MB) [Text Only]",
        "repo_id": "nomic-ai/nomic-embed-text-v1.5-GGUF",
        "filename": "nomic-embed-text-v1.5.Q4_K_M.gguf",
        "size_mb": 80,
        "dimensions": 768,
        "multimodal": False,
    },
    "clip-vit-b-q4": {
        "label": "CLIP ViT-B Q4 (350 MB) [Multimodal]",
        "repo_id": "Xenova/clip-vit-base-patch32-ggml",
        "filename": "clip-vit-base-q4_k_m.gguf",
        "size_mb": 350,
        "dimensions": 512,
        "multimodal": True,
    },
}

DEVICE_PRESETS = {
    "4gb-mobile": {
        "llm": "qwen2.5-1.5b-q4",
        "embedding": "nomic-q4",
        "max_context": 512,
    },
    "4gb-mobile-qwen35": {
        "llm": "qwen3.5-1b-q4",
        "embedding": "nomic-q4",
        "max_context": 512,  # Practical limit despite 32K
    },
    "6gb-mobile": {
        "llm": "qwen2.5-1.5b-q4",
        "embedding": "clip-vit-b-q4",
        "max_context": 1024,
    },
}


def get_device_preset(device_class: str) -> dict:
    """Get recommended model setup for device."""
    return DEVICE_PRESETS.get(device_class, DEVICE_PRESETS["4gb-mobile"])


def model_is_multimodal(model_key: str) -> bool:
    """Check if embedding supports multimodal (text + images)."""
    model = EMBEDDING_MODELS.get(model_key, {})
    return model.get("multimodal", False)
