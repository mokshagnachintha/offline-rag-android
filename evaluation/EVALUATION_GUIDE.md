# O-RAG Evaluation Suite - Complete Guide

**Last Updated**: April 2, 2026  
**Status**: All notebooks updated to use O-RAG system  

---

## 📓 Notebook Overview

### **CORE EVALUATION NOTEBOOKS** (NEW - Focus on O-RAG)

#### 1. **`7_rag_demo_interactive_queries.ipynb`** ⭐ START HERE
**Purpose**: Interactive demonstration of O-RAG with comprehensive query analysis

**What it does**:
- Initializes O-RAG system (Qwen 2.5-1.5B + Nomic embeddings)
- Executes 20 queries across 4 categories:
  - Factual queries
  - Reasoning queries
  - Multi-hop queries
  - Comparative queries
- Tracks metrics:
  - Query latency (milliseconds)
  - Memory delta (MB)
  - Retrieved documents count
  - Confidence scores
- Generates:
  - Performance graphs (latency distribution, confidence vs latency)
  - Detailed results table (query, response, time, docs)
  - Category-wise performance analysis
  - Percentile latency breakdown

**Output Files**:
- `rag_latency_analysis.png` - Performance visualization
- `rag_query_results_TIMESTAMP.csv` - Detailed results

**Best for**: Understanding O-RAG performance in real-world scenarios

---

#### 2. **`8_rag_systems_comparison.ipynb`** ⭐ COMPARE APPROACHES
**Purpose**: Side-by-side comparison of 3 RAG architectures

**Systems Compared**:
1. **O-RAG (Full-Featured)**
   - Context window: 512 tokens
   - Retrieved docs: 5
   - Best quality
   
2. **Dense Vector RAG**
   - Context window: 256 tokens
   - Retrieved docs: 3
   - Middle ground (speed vs quality)
   
3. **Mobile-Optimized RAG**
   - Context window: 128 tokens
   - Retrieved docs: 2
   - Fastest (for 4GB devices)

**What it does**:
- Executes 8 diverse test queries on all 3 systems
- Compares:
  - Query latency (ms)
  - Response length
  - Retrieved document count
  - Confidence scores
  - Success rate
- Generates:
  - Comparative visualizations (6 panels)
  - System performance table
  - Category-wise analysis
  - Speedup metrics

**Output Files**:
- `rag_systems_comparison.png` - Comparison charts
- `rag_systems_comparison_TIMESTAMP.csv` - Results
- HTML recommendation table

**Best for**: Choosing which RAG configuration for your use case

---

#### 3. **`0_benchmark_hf_quantized_enhanced.ipynb`** ⭐ MODEL EVALUATION
**Purpose**: Comprehensive benchmark of LLM and embedding models

**Models Tested**:

**LLM Models**:
- Qwen 3.5 (8-bit and 4-bit) ← NEW
- Qwen 2.5-1.5B (8-bit and 4-bit) ← CURRENT O-RAG
- Qwen 2.5-0.5B (4-bit) ← Mobile variant
- Gemma 2-2B (8-bit and 4-bit)

**Embedding Models**:
- Nomic Embed Text (Q4) ← CURRENT O-RAG
- Nomic Embed Text (F32)
- bge-small-en-v1.5 (Q4)
- E5-small (Q4)

**What it does**:
- Downloads models from HuggingFace Hub
- Benchmark each LLM on 5 test prompts:
  - Measures latency per model
  - Calculates throughput (tokens/sec)
  - Compares quantization impact (Q4 vs Q8)
- Profiles embedding models:
  - Latency per sentence
  - Throughput (sentences/sec)
  - Model size comparison
- Visualizes results:
  - Throughput vs size scatter
  - Latency comparison bar chart
  - Model size distribution
  - Quantization impact

**Output Files**:
- `llm_benchmark_results_TIMESTAMP.csv` - LLM results
- `embedding_benchmark_results_TIMESTAMP.csv` - Embedding results
- `llm_benchmark_comparison.png` - Visualization
- `benchmark_report_TIMESTAMP.txt` - Summary

**Best for**: Model selection and quantization analysis

---

### **EXISTING NOTEBOOKS** (Integration)

| Notebook | Purpose | Updated | O-RAG Integration |
|----------|---------|---------|-------------------|
| `1_embedding_comparison.ipynb` | Compare embedding methods | ✅ | Uses Nomic embeddings |
| `2_domain_comparison.ipynb` | Domain-specific evaluation | ✅ | Uses O-RAG pipeline |
| `3_research_grade_evaluation.ipynb` | Academic-quality metrics | ✅ | Uses O-RAG system |
| `5_mobile_rag_feasibility.ipynb` | Mobile constraints analysis | ✅ | Tests 4GB optimization |
| `6_rag_industry_eval.ipynb` | Industry benchmarks | ✅ | Uses current models |
| `9_advanced_orag_analysis.ipynb` | Advanced metrics | ✅ | Phase D analysis |
| `10_phase2_multimodal_testing.ipynb` | Multimodal capabilities | ✅ | Image document support |
| `11_phase3_memory_optimization_testing.ipynb` | Memory profiling | ✅ | Phase D memory mgr |
| `12_phase4_integration_testing.ipynb` | Full integration test | ✅ | All phases tested |

---

## 🚀 Quick Start Guide

### **For First-Time Users**
1. ▶️ Run `7_rag_demo_interactive_queries.ipynb`
   - See O-RAG in action
   - Understand performance characteristics
   
2. ▶️ Run `8_rag_systems_comparison.ipynb`
   - Compare different configurations
   - Choose best setup for your needs

3. ▶️ Run `0_benchmark_hf_quantized_enhanced.ipynb`
   - Analyze LLM/embedding models
   - Understand quantization impact

---

### **For Model Selection**
1. Start with `0_benchmark_hf_quantized_enhanced.ipynb`
   - Benchmark all available models
   - Compare quantization (Q4 vs Q8)
   - Check model sizes

2. Review throughput vs latency trade-offs
   - Qwen 3.5 (Q4): Best quality, moderate speed
   - Qwen 2.5-1.5B (Q4): Current balance
   - Qwen 2.5-0.5B (Q4): Fastest for mobile

---

### **For Performance Analysis**
1. Run `7_rag_demo_interactive_queries.ipynb`
   - Get detailed latency breakdown
   - See percentile latencies (P50, P75, P90, P95, P99)
   - Identify performance patterns

---

### **For Device Optimization (4GB Android)**
1. Run `8_rag_systems_comparison.ipynb`
   - Compare with Mobile-Optimized RAG
   - See memory usage patterns
   - Evaluate speed-quality tradeoff

---

## 📊 Metrics Explained

| Metric | Definition | Target |
|--------|-----------|--------|
| **Latency (ms)** | Time to generate response | <500ms |
| **Throughput (tokens/sec)** | Generation speed | >20 tokens/sec |
| **Confidence** | Model's certainty (0-1) | >0.7 |
| **Retrieved Docs** | Documents matched | 3-5 ideal |
| **Memory Delta** | RAM used per query | <50MB |
| **Success Rate** | % of successful queries | >95% |

---

## 🎯 O-RAG Current Configuration

```yaml
LLM:
  Model: Qwen 2.5-1.5B
  Quantization: Q4 (4-bit)
  Context Window: 512 tokens
  Max Output: 256 tokens
  Size: ~900 MB

Embeddings:
  Model: Nomic Embed Text v1.5
  Quantization: Q4 (4-bit)
  Dimensions: 768
  Size: ~200 MB

Memory Management:
  Strategy: Pressure-based (Phase D)
  Thresholds:
    NORMAL: >400 MB free
    CAUTION: 200-400 MB free
    CRITICAL: <200 MB free
  
  Optimization:
    NORMAL: Context 512, Docs 5, Size 80w
    CAUTION: Context 256, Docs 3, Size 64w
    CRITICAL: Context 128, Docs 2, Size 48w

Target Device:
  RAM: 4GB minimum
  Android: 8.0+ (API 26+)
  Architecture: arm64-v8a
```

---

## 📈 Expected Performance

| Query Type | Latency | Confidence | Docs |
|------------|---------|-----------|------|
| Factual | 150-250ms | 0.80-0.95 | 5 |
| Reasoning | 250-350ms | 0.70-0.85 | 5 |
| Multi-hop | 300-500ms | 0.65-0.80 | 4-5 |
| Comparative | 200-400ms | 0.75-0.90 | 4-5 |

**Mobile (4GB Device)**:
- All queries slightly slower due to memory pressure
- Context window may reduce from 512→256→128
- Same quality, different speed-quality tradeoff

---

## 🔧 How to Run Notebooks

### **Basic**
```python
# In Jupyter
jupyter notebook

# Select notebook and run all cells (Ctrl+A, Ctrl+Enter)
```

### **With Environment**
```bash
# Activate venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# Install requirements
pip install -r requirements.txt

# Run Jupyter
jupyter notebook evaluation/
```

### **Key Parameters to Adjust**

In `7_rag_demo_interactive_queries.ipynb`:
```python
context_window=512      # Reduce for 4GB: 256 or 128
max_tokens=256          # Output size
top_k=5                 # Retrieved documents
temperature=0.7         # 0=deterministic, 1=creative
```

In `8_rag_systems_comparison.ipynb`:
- Already has 3 presets
- Can add custom configurations

In `0_benchmark_hf_quantized_enhanced.ipynb`:
- Add new models to `LLM_MODELS` list
- Add new embeddings to `EMBEDDING_MODELS` list
- Adjust `test_prompts` for your domain

---

## 📁 Output Files

### **Generated During Runs**

```
evaluation/
├── rag_latency_analysis.png
│   └── Performance graphs (notebook 7)
├── rag_systems_comparison.png
│   └── Comparison charts (notebook 8)
├── llm_benchmark_comparison.png
│   └── Model comparison (notebook 0)
├── rag_query_results_TIMESTAMP.csv
│   └── Detailed query results (notebook 7)
├── rag_systems_comparison_TIMESTAMP.csv
│   └── System comparison results (notebook 8)
├── llm_benchmark_results_TIMESTAMP.csv
│   └── LLM benchmark data (notebook 0)
├── embedding_benchmark_results_TIMESTAMP.csv
│   └── Embedding benchmark data (notebook 0)
└── benchmark_report_TIMESTAMP.txt
    └── Summary report (notebook 0)
```

---

## ❓ FAQ

### **Q: Which notebook should I run first?**
A: Start with `7_rag_demo_interactive_queries.ipynb` to see O-RAG in action.

### **Q: How often should I run benchmarks?**
A: After model updates or before deployment. Regular runs (weekly) for performance tracking.

### **Q: Can I modify queries or test cases?**
A: Yes! All QUERY_SETS and test_prompts are easily customizable.

### **Q: How do I compare against other RAG systems?**
A: Use `8_rag_systems_comparison.ipynb` - it's designed for this.

### **Q: What if a model fails to download?**
A: Check internet connection. Models are auto-downloaded from HuggingFace Hub on first run.

### **Q: Can I use these on 4GB devices?**
A: Yes! Notebook 8 has a Mobile-Optimized configuration preset.

### **Q: How do I export results for reporting?**
A: All notebooks export CSV files. Use pandas to read and create custom reports.

---

## 🔗 Integration Map

```
Core O-RAG System
        ↓
    ┌───┴───┐
    ↓       ↓
 Notebook 7  Notebook 8 ← Compare configurations
 (Demo)      (Comparison)
    ↓            ↓
 Performance    Which RAG?
 Analysis       (Speed/Quality)
    
        ↓
  Notebook 0
  (Model Selection)
    ↓
 Which LLM?
 Which Embeddings?
```

---

## 📝 Notes for Development

- **Phase A (Analytics)**: Used in all notebooks via HealthMonitor
- **Phase B (Download)**: Assumed models already available
- **Phase C (UI)**: Not visible in notebooks (uses Kivy UI)
- **Phase D (Memory Mgr)**: Tested in notebooks 7 & 8 for pressure handling
- **Phase E (Build)**: Notebooks validate for APK inclusion

All notebooks are compatible with the O-RAG Pipeline class and integrate through `rag/pipeline.py`.

---

## 🎓 Learning Outcomes

After running all notebooks, you'll understand:

✅ How O-RAG performs on real queries  
✅ Why certain configuration choices matter  
✅ How quantization affects speed vs quality  
✅ How memory constraints impact 4GB devices  
✅ Which models are best for your use case  
✅ How to benchmark custom RAG systems  
✅ How to optimize for your constraints  
✅ How to compare different architectures  

---

**Let's evaluate! 🚀**
