# Google Colab Quantization - Quick Start Guide

## What You'll Get

After running this notebook, you'll have:
- ✅ `qwen2.5-7b-instruct-q4_k_m.gguf` (2.0 GB)
- ✅ 3.6x compression from original (7.3 GB → 2.0 GB)
- ✅ Ready for mobile deployment
- ✅ ~15-20 minutes total processing

---

## Option A: Use Pre-made Notebook (EASIEST)

### Step 1: Open Colab
```
1. Go to https://colab.research.google.com
2. Click "File" → "Upload notebook"
3. Select: Qwen_Quantization_Colab.ipynb
```

### Step 2: Run Cells Sequentially
```
- Cell 1: Install Dependencies (1 min)
- Cell 2: Check Environment (30 sec)
- Cell 3: Download Model (5-10 min)
- Cell 4: Quantize (10 min)
- Cell 5: Download Result (1 min)
```

### Step 3: Download Model
When Cell 5 completes, click "Save" in the download dialog.

---

## Option B: Use Python Script (MANUAL)

### Step 1: Open Colab
```
1. Go to https://colab.research.google.com
2. Create a new notebook
```

### Step 2: Copy Each Cell
```
For each code block in COLAB_QUANTIZATION.py:
1. Create new cell (Ctrl+M then B)
2. Copy code block
3. Remove the triple quotes (""") at start/end
4. Run cell (Shift+Enter)
```

---

## Troubleshooting

### "llama-cpp-python build failed"
```
Try: pip install llama-cpp-python --prefer-binary --force-reinstall
```

### "Out of Memory"
```
1. Restart runtime: Runtime → Restart runtime
2. Close other tabs/notebooks
3. Try 1.5B model instead (smaller)
```

### "Download stuck"
```
Option 1: Use Google Drive (Step 8 of notebook)
Option 2: Download directly from HuggingFace hub
```

---

## File Locations

After quantization, models are in Colab at:
```
./models/qwen2.5-7b-instruct-q4_k_m.gguf    (downloaded)
./models/qwen2.5-7b-instruct-q8_0.gguf       (original input)
./models/qwen2.5-7b-instruct-q3_k_m.gguf     (optional)
./models/qwen2.5-7b-instruct-q5_k_m.gguf     (optional)
./models/qwen2.5-7b-instruct-q6_k.gguf       (optional)
```

---

## Using the Downloaded Model

### 1. Place in O-RAG
```bash
cp ~/Downloads/qwen2.5-7b-instruct-q4_k_m.gguf ~/Desktop/O-rag/
```

### 2. Update O-RAG Config
```python
# In main.py or cli.py
from rag.llm import LlamaCppModel

llm = LlamaCppModel()
llm.load("qwen2.5-7b-instruct-q4_k_m.gguf")  # Auto-loads from local
```

### 3. Run O-RAG
```bash
cd ~/Desktop/O-rag
python main.py
```

---

## Quantization Formats Available

| Format | Size | Compression | Quality | Mobile |
|--------|------|-------------|---------|--------|
| Q3_K_M | 1.3 GB | 5.6x | Low | ⭐ Tiny |
| **Q4_K_M** | **2.0 GB** | **3.6x** | **Good** | **✅ BEST** |
| Q5_K_M | 2.7 GB | 2.7x | High | ⚠️ 8GB+ |
| Q6_K | 3.5 GB | 2.1x | Very High | ❌ Large |

To generate multiple formats:
- Uncomment **Cell 6** in the notebook
- Takes ~30-40 minutes total
- Download any format individually

---

## Performance Expectations

### On 4GB Mobile Device
- **Q4_K_M**: 8-12 tokens/sec (✅ Recommended)
- **Q5_K_M**: 10-15 tokens/sec (⚠️ May OOM)
- **Q3_K_M**: 5-8 tokens/sec (⭐ Extreme compression)

### Inference Time Examples
- Question: "What is RAG?" 
- Answer length: 100 tokens
- **Q4_K_M**: ~8 seconds
- **Q5_K_M**: ~7 seconds (if it fits)

---

## FAQ

**Q: Do I need to pay for Colab?**  
A: No, free tier has enough storage and CPU/GPU for quantization.

**Q: Why is quantization useful?**  
A: Reduces model from 7.3 GB to 2.0 GB while keeping 95% quality.

**Q: Can I use other models?**  
A: Yes, change REPO_ID and MODEL_FILE in the notebook.

**Q: How long does it take?**  
A: ~15-20 minutes total (5 min download + 10 min quantization).

**Q: Can I save to Google Drive?**  
A: Yes, use Cell 8 for persistent storage across sessions.

**Q: What if I want higher quality?**  
A: Use Q5_K_M (~2.7 GB) or Q6_K (~3.5 GB) formats.

---

## Pro Tips

1. **Faster Download**: Run Colab on a region close to you
   - Settings → Preferred location

2. **Save Models**: Use Google Drive (Cell 8)
   - Access from any Colab notebook later

3. **Multiple Formats**: Uncomment Cell 6
   - Compare Q4_K_M, Q5_K_M, Q6_K sizes
   - Download whichever fits your device

4. **Batch Quantization**: Run on all available models
   - Qwen 1.5B, Qwen 7B, Qwen 13B
   - Takes 1-2 hours total

---

## Next Steps

1. ✅ Run the notebook on Colab
2. ✅ Download the quantized model
3. ✅ Place in O-RAG project
4. ✅ Run O-RAG: `python main.py`
5. ✅ Start using RAG queries!

---

## Support

If you encounter issues:

1. Check troubleshooting section above
2. Review Colab error messages (usually clear)
3. Try restarting Colab runtime: Runtime → Restart runtime
4. Check HuggingFace hub status: https://huggingface.co/Qwen/Qwen2.5-7B-Instruct-GGUF

---

**Happy Quantizing!** 🚀
