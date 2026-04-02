# O-RAG Comprehensive Evaluation Suite

## Project Overview

This directory contains the complete evaluation framework for the **O-RAG (Offline RAG)** system, measuring retrieval quality across multiple domains and retrieval strategies.

**Scope:** 
- 252 Q&A evaluations
- 7 retrieval variants (BM25, Semantic, TF-IDF, 4× Hybrid)
- 3 domains (Healthcare, Technical, Financial)
- 12 questions per domain per variant

---

## 🚀 Quick Start - Recommended Execution Order

Run the notebooks in numerical sequence to understand the full evaluation pipeline:

### 1️⃣ **Start Here: Domain Comparison** 
📄 [1_domain_comparison.ipynb](1_domain_comparison.ipynb)

**What it shows:**
- Performance of all 7 variants within each domain
- Domain-specific best practices
- Cross-domain performance heatmap
- Identifies which variants excel in healthcare vs. technical vs. financial contexts

**Key outputs:**
- `healthcare_variant_comparison.png`
- `technical_variant_comparison.png`
- `financial_variant_comparison.png`
- `domain_variant_heatmap.png`

**Runtime:** ~30 seconds

---

### 2️⃣ **Then: Variant Comparison**
📄 [2_variant_comparison.ipynb](2_variant_comparison.ipynb)

**What it shows:**
- How each retrieval strategy generalizes across domains
- Variant-specific strengths and weaknesses
- Global rankings and recommendations
- Latency consistency analysis

**Key outputs:**
- `variant_bm25_only.png` through `variant_tfidf_only.png` (7 files)
- `all_variants_comparison.png`

**Runtime:** ~2-3 minutes

---

### 3️⃣ **Next: LLM-Based Quality Evaluation**
📄 [3_llm_based_evaluation.ipynb](3_llm_based_evaluation.ipynb)

**What it shows:**
- LLM-as-Judge evaluation using Google Gemini
- 4 quality metrics: Faithfulness, Relevance, Coherence, Completeness
- How LLM scores correlate with retrieval metrics
- Quality assessment for top variants

**Key outputs:**
- `llm_evaluation_results.csv`
- `llm_evaluation_results.png`

**Runtime:** ~10-15 minutes (includes API calls)

**⚠️ Prerequisite:** Google AI Studio API key (embedded in notebook)

---

### 4️⃣ **Finally: Comprehensive Summary**
📄 [4_final_comparison.ipynb](4_final_comparison.ipynb)

**What it shows:**
- Integrated analysis: retrieval metrics + LLM scores
- Best variant-domain combinations
- 6-panel dashboard: recall, latency, precision, quality trade-offs
- Production deployment recommendations
- Deployment checklist and research paper takeaways

**Key outputs:**
- `final_comparison_dashboard.png`
- `PRODUCTION_DEPLOYMENT_GUIDE.txt`

**Runtime:** ~1-2 minutes

---

## 📊 Key Findings Summary

### Best Overall Configuration
**Hybrid Semantic-Heavy (30% BM25 + 20% TF-IDF + 50% Semantic)**
- ⭐ Production default
- Recall: 0.872 | Precision: 0.676 | Hit Rate: 1.00
- Latency: 30.9ms

### Best Per Domain
| Domain | Best Variant | Recall | Latency |
|--------|--------------|--------|---------|
| Healthcare | Hybrid Semantic-Heavy | 0.882 | 28.7ms |
| Technical | Semantic-only | 0.904 | 36.1ms |
| Financial | Hybrid Semantic-Heavy | 0.901 | 33.1ms |

### Alternatives
- **Speed-optimized:** Hybrid Balanced (0.840 recall, 27.4ms)
- **Precision-first:** Semantic-only (0.834 recall, best precision on technical)

---

## 📁 File Structure

```
evaluation/
├── README.md                                    (This file)
├── NOTEBOOK_GUIDE.md                            (Detailed notebook guide)
│
├── 1_domain_comparison.ipynb                    (Notebook 1)
├── 2_variant_comparison.ipynb                   (Notebook 2)
├── 3_llm_based_evaluation.ipynb                 (Notebook 3)
├── 4_final_comparison.ipynb                     (Notebook 4)
│
├── evaluation_results_comprehensive.csv         (252 evaluation results)
├── datasets/                                    (Test datasets)
│   ├── healthcare_qa.txt
│   ├── healthcare_qa_reference.json
│   ├── technical_qa.txt
│   ├── technical_qa_reference.json
│   ├── financial_qa.txt
│   └── financial_qa_reference.json
│
├── config_variants.py                           (Variant configurations)
├── eval_utils.py                                (Evaluation utilities)
├── run_comprehensive_evaluation.py              (Evaluation runner)
│
└── *.png                                        (Generated visualizations)
```

---

## 💡 Usage Guide

### For Research Paper
1. Run notebooks 1-4 in sequence
2. Use PNGs as figures for methods/results sections
3. Reference composite scores and rankings from findings
4. Include deployment recommendations from Notebook 4

### For Presentations
1. Start with Notebook 4 (final summary + dashboard)
2. Then go back to Notebooks 1-2 for detailed comparisons
3. Use PNG outputs directly in slides
4. Reference specific domain/variant tables

### For Development
1. Modify `config_variants.py` to test new retrieval strategies
2. Re-run `run_comprehensive_evaluation.py` to generate new baseline
3. Execute notebooks to visualize changes
4. Use Notebook 3 to evaluate LLM quality improvements

---

## ⚙️ Technical Details

### Metrics Computed
**Retrieval Quality:**
- Context Recall (what % of relevant context was retrieved)
- Context Precision (what % of retrieved context was relevant)
- Hit Rate (was relevant document in top-k)
- Mean Reciprocal Rank (MRR, ranking quality)
- NDCG@5 (normalized discounted cumulative gain)

**Generation Quality (LLM):**
- Faithfulness (grounded in context, no hallucinations)
- Relevance (answers the question)
- Coherence (logically structured)
- Completeness (covers key aspects)

**Performance:**
- Latency: retrieve, generate, end-to-end
- All metrics averaged across 12 Q&A pairs per domain/variant

### Environment
- Python 3.9+
- Jupyter Notebook/Lab
- pandas, matplotlib, seaborn, plotly
- google-generativeai (for Notebook 3)

---

## 🔧 Customization

### Change Retrieval Variants
Edit `config_variants.py` to adjust weights (BM25/TF-IDF/Semantic percentages)

### Add New Domains
Create new dataset JSON files in `datasets/` following the pattern:
```
domain_qa.txt              (Q&A pairs, one per line)
domain_qa_reference.json   (Ground truth context/answers)
```

### Run Full Evaluation
```bash
python run_comprehensive_evaluation.py
```

---

## 📖 Additional Resources

- **NOTEBOOK_GUIDE.md** - Detailed explanation of each notebook
- **PRODUCTION_DEPLOYMENT_GUIDE.txt** - Generated in Notebook 4 with deployment checklist
- **evaluation_results_comprehensive.csv** - Raw evaluation data

---

## 🎯 Next Steps

1. ✅ **Execute Notebooks:** Run 1→2→3→4 in sequence
2. 📊 **Review Findings:** Check PRODUCTION_DEPLOYMENT_GUIDE.txt
3. 📝 **Document Results:** Use PNGs and tables for documentation
4. 🚀 **Deploy:** Follow deployment checklist from Notebook 4

---

**Created:** April 1, 2026  
**Evaluation Dataset:** 252 evaluations × 7 variants × 3 domains  
**Status:** ✅ Complete and ready for analysis
