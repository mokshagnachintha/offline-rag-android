# Quantization Guide for O-RAG Models

This folder contains scripts for quantizing LLM and embedding models to run efficiently on 4GB mobile devices.

## Quick Start

### 1. Quantize Qwen 3.5 (or Qwen 2.5) Model

**Download and quantize in one command:**
```bash
python compressed/quantize_qwen35.py --download --format q4_k_m
```

**Quantize an existing model:**
```bash
python compressed/quantize_qwen35.py --input qwen2.5-7b-instruct-q8_0.gguf --format q4_k_m
```

**Just download (no quantization):**
```bash
python compressed/quantize_qwen35.py --download --no-quantize
```

### 2. View Available Quantization Formats

```bash
python compressed/quantize_qwen35.py --formats
```

Output:
```
📊 Available Quantization Formats:
======================================================================
  q3_k_m      Max compression (3-bit)                Quality: low
  q4_k_m      Balanced (4-bit) - RECOMMENDED        Quality: good
  q5_k_m      High quality (5-bit)                   Quality: high
  q6_k        Very high quality (6-bit)              Quality: very_high
  q8_0        Near-original (8-bit int)              Quality: max
======================================================================
```

## Quantization Formats Explained

### Q4_K_M (Recommended for 4GB Devices) ⭐
- **Size**: ~1.5-2GB for Qwen 7B model
- **Quality**: Good for RAG retrieval + chat
- **Speed**: Fast inference
- **Use Case**: Mobile deployment (4GB RAM minimum)

### Q5_K_M (High Quality)
- **Size**: ~2-3GB for Qwen 7B model
- **Quality**: Better than Q4_K_M
- **Speed**: Slightly slower than Q4_K_M
- **Use Case**: Desktop or 8GB+ devices

### Q3_K_M (Maximum Compression)
- **Size**: ~1GB for Qwen 7B model
- **Quality**: Lower quality, noticeable loss
- **Speed**: Fastest
- **Use Case**: Extreme compression on memory-limited devices

### Q6_K (Very High Quality)
- **Size**: ~3-4GB for Qwen 7B model
- **Quality**: Near original quality
- **Speed**: Slower
- **Use Case**: High-end devices or desktop

## Installation

### Prerequisites
```bash
# Core dependencies
pip install llama-cpp-python
pip install huggingface-hub

# Optional: for faster downloads
pip install requests tqdm
```

### Full Environment Setup
```bash
cd O-rag
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

pip install -r requirements.txt
pip install llama-cpp-python huggingface-hub
```

## Model Sources

### Qwen Models (HuggingFace)
- **Qwen 2.5 7B Instruct GGUF**: `Qwen/Qwen2.5-7B-Instruct-GGUF`
- **Qwen 2.5 1.5B Instruct GGUF**: `Qwen/Qwen2.5-1.5B-Instruct-GGUF`
- Available formats: q8_0 (base), q6_k, q5_k_m, q4_k_m, q3_k_m

### Nomic Embedding Models
- **Nomic Embed Text v1.5 GGUF**: `nomic-ai/nomic-embed-text-v1.5-GGUF`
- Best format for mobile: Q4_K_M

## Advanced Usage

### Custom Repository and File
```bash
python compressed/quantize_qwen35.py \
    --download \
    --repo "NousResearch/Qwen2-GGUF" \
    --file "qwen2-7b-instruct-q8_0.gguf" \
    --format q4_k_m \
    --output my_custom_qwen_q4.gguf
```

### Batch Processing
```bash
# Quantize with multiple formats
for format in q3_k_m q4_k_m q5_k_m q6_k; do
    python compressed/quantize_qwen35.py \
        --input qwen2.5-7b-instruct-q8_0.gguf \
        --format $format
done
```

## Performance Expectations

### On 4GB Mobile Device (Snapdragon 888)
| Format | Model Size | LLM Speed | Embedding Speed | Recommended |
|--------|-----------|-----------|-----------------|-------------|
| Q3_K_M | 1.0 GB    | 5 tok/s   | 100 embeddings/s | ⚠️ Slow    |
| Q4_K_M | 1.5-2GB   | 8-12 tok/s| 150 embeddings/s| ✅ **Best** |
| Q5_K_M | 2-3GB     | 10-15 tok/s| 180 embeddings/s| ⚠️ OOM risk|
| Q6_K   | 3-4GB     | 12-18 tok/s| 200 embeddings/s| ❌ OOM |

## Troubleshooting

### "llama-cpp-python not installed"
```bash
pip install llama-cpp-python --upgrade
```

### "huggingface_hub not installed"
```bash
pip install huggingface-hub
```

### OOM (Out of Memory) During Quantization
- Run on a Linux machine with 16GB+ RAM
- Use WSL2 on Windows
- Cloud options: Google Colab (free), Paperspace, Lambda Labs

### Quantization Too Slow
- Use fewer cores: Set `OMP_NUM_THREADS=4`
- Or use a faster CPU/SSD

### Model Not Found After Download
- Check your internet connection
- Increase timeout: `export HF_HUB_READ_TIMEOUT=600`
- Or manually download from HuggingFace web interface

## Integration with O-RAG

### Using Quantized Models in O-RAG

1. **Place quantized model in project root:**
```bash
cp qwen2.5-7b-instruct-Q4_K_M.gguf ./
cp nomic-embed-text-v1.5.Q4_K_M.gguf ./
```

2. **Update `main.py` or environment:**
```python
# main.py
from rag.llm import LlamaCppModel
from rag.downloader import download_model_with_fallback

llm = LlamaCppModel()
# Auto-loads from local or downloads
llm.load("qwen2.5-7b-instruct-q4_k_m.gguf")
```

3. **Run O-RAG:**
```bash
python main.py
```

## File Sizes Reference

### Qwen 7B Model (GGUF)
- Q8_0 (base): ~7.3 GB
- Q6_K: ~3.5 GB  
- Q5_K_M: ~2.7 GB
- Q4_K_M: ~2.0 GB ⭐
- Q3_K_M: ~1.3 GB

### Qwen 1.5B Model (GGUF)
- Q8_0 (base): ~1.6 GB
- Q6_K: ~0.8 GB
- Q5_K_M: ~0.65 GB
- Q4_K_M: ~0.5 GB ⭐
- Q3_K_M: ~0.35 GB

## See Also

- [compressed_qwen.py](compressed_qwen.py) - Legacy Qwen 2.5 quantization script
- [compressed_nomic.py](compressed_nomic.py) - Nomic embedding quantization
- [llama.cpp Quantization Docs](https://github.com/ggml-org/llama.cpp/blob/master/docs/quantization.md)
- [Qwen Model Card](https://huggingface.co/Qwen/Qwen2.5-7B-Instruct-GGUF)
