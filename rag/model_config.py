"""
Model configuration for Qwen 3.5 + Multimodal Embeddings support.
Supports model selection, device profiles, auto-fallback chains.
"""

LLM_MODELS = {
    "qwen2.5-3b-q4": {
        "label": "Qwen 3.5 2B Q4 (1.3 GB) [Personal Repo]",
        "repo_id": "mokshagna21/orag-qwen-3.5-2b-gguf",
        "filename": "Qwen_Qwen3.5-2B-Q4_K_M.gguf",
        "size_mb": 1280,
        "context_window": 32768,
        "parameters": "2B",
        "is_fallback": False,
    },
}

EMBEDDING_MODELS = {
    "clip-vit-b32": {
        "label": "CLIP ViT-B32 Multimodal (330 MB) [Text + Image]",
        "repo_id": "Xenova/clip-vit-base-patch32-ggml",
        "filename": "ggml-model-q4_k_m.gguf",
        "size_mb": 330,
        "dimensions": 512,
        "multimodal": True,
    },
}

DEVICE_PRESETS = {
    "4gb-mobile": {
        "llm": "qwen2.5-3b-q4",
        "embedding": "clip-vit-b32",
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
