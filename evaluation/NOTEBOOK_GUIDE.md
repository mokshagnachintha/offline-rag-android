# O-RAG Evaluation Notebooks: Complete Guide

## 📁 Project Organization

**Clean structure with 4 core evaluation notebooks in logical order:**

```
evaluation/
├── 1_domain_comparison.ipynb              (Start here)
├── 2_variant_comparison.ipynb             (Then this)
├── 3_llm_based_evaluation.ipynb           (Then this)
├── 4_final_comparison.ipynb               (Finally this)
├── evaluation_results_comprehensive.csv   (Input data)
├── datasets/                              (Test data)
├── NOTEBOOK_GUIDE.md                      (This file)
└── *.png                                  (Generated visualizations)
```

## Overview

You have 4 comprehensive Jupyter notebooks that cover every aspect of the O-RAG system evaluation. Each notebook is designed to be self-contained and explanatory, following a logical progression for explaining the project.

**Total Evaluations:** 252 Q&A pairs × 7 retrieval variants × 3 domains

---

## 📚 Notebook Structure (Recommended Execution Order)

### 1️⃣ **Domain Comparison Notebook** (`1_domain_comparison.ipynb`)

**Purpose:** Analyze how different retrieval strategies perform within each domain

**What it covers:**
- 🏥 **Healthcare Domain** - All 7 variants compared (recall, precision, hit rate, latency)
- 💻 **Technical Domain** - All 7 variants compared
- 💰 **Financial Domain** - All 7 variants compared
- Cross-domain heatmap showing performance variation

**Key insights:**
- Which variants perform best per domain
- Domain-specific strengths and weaknesses
- Latency differences across variants
- Performance spread (best vs worst variant per domain)

**Audience:** Decision makers wanting domain-level analysis

**Run time:** ~30 seconds (all data pre-aggregated)

---

### 2️⃣ **Retrieval Variant Comparison Notebook** (`2_variant_comparison.ipynb`)

**Purpose:** Analyze how each retrieval strategy generalizes across all domains

**What it covers:**
- **BM25-only** - Performance across healthcare, technical, financial
- **Semantic-only** - Generalization analysis
- **TF-IDF-only** - Cross-domain consistency
- **Hybrid Balanced** (33/33/33) - Average performance
- **Hybrid Semantic-Heavy** (30/20/50) ⭐ - Production default
- **Hybrid BM25-Heavy** (50/20/30) - Technical optimization
- **Hybrid TF-IDF-Heavy** (30/50/20) - Lightweight option

**For each variant:**
- Performance table across all domains
- Best/worst domain for that variant
- Visualizations showing why certain domains suit certain variants
- Variance and consistency analysis

**Key insights:**
- Which variants generalize well vs domain-specific
- Recall degradation patterns
- Latency consistency across domains
- Global rankings with recommendations

**Audience:** ML engineers optimizing for robustness

**Run time:** ~2-3 minutes (generates 7 visualizations)

---

### 3️⃣ **LLM-Based Evaluation Notebook** (`3_llm_based_evaluation.ipynb`)

**Purpose:** Use Google Gemini LLM as an impartial judge to evaluate quality

**LLM Judge Metrics (0-10 scale):**
1. **Faithfulness** - Does answer stay grounded in context? (No hallucinations)
2. **Relevance** - Does answer address the question?
3. **Coherence** - Is answer logically structured and clear?
4. **Completeness** - Does answer cover all key aspects?

**What it covers:**
- Setup Google Gemini API integration
- Define 4 LLM evaluation functions
- Load test datasets
- Run comprehensive evaluations on top 3 variants
- Visualize LLM quality scores across variants/domains

**Data:**
- Top 3 performing variants: `hybrid_semantic_heavy`, `semantic_only`, `hybrid_bm25_heavy`
- 3 domains × 3 variants × 5 sample questions = 45 LLM evaluations per full run
- Can expand to full dataset (12 questions each = 108 evaluations)

**Key insights:**
- Which variants produce highest quality (faithful, relevant, coherent, complete) answers
- Domain-specific quality patterns
- LLM vs retrieval metrics correlation
- Hallucination detection and reasoning

**Audience:** Quality-focused teams, researchers

**Run time:** ~5-15 minutes (depends on API rate limiting)

**Requirements:** Google AI Studio API key (provided)

---

### 4️⃣ **Final Comparison Notebook** (`4_final_comparison.ipynb`)

**Purpose:** Synthesize all evaluation results and provide production recommendations

**What it covers:**
- Load and combine all evaluation data (retrieval + LLM metrics)
- Comprehensive summary table: all metrics integrated
- Best configurations by domain
- Global best configuration analysis
- Dashboard with 6 comparative visualizations:
  - Variant recall comparison
  - Domain performance
  - Quality-latency trade-off
  - Precision rankings
  - Hit-rate heatmap
  - Latency distributions

**Key outputs:**
- 🥇 **Primary recommendation**: Hybrid Semantic-Heavy (30/20/50)
- 🥈 **Speed-optimized**: Hybrid Balanced (33/33/33)
- 🥉 **Domain-specific tuning** suggestions
- Production deployment checklist
- Research paper takeaway

**Audience:** Decision makers, project leads, research authors

**Run time:** ~1-2 minutes

---

## 🚀 How to Run the Notebooks

### Sequential Execution (Recommended)

```bash
1. Run: 1_domain_comparison.ipynb
   └─ Understand how variants perform per domain

2. Run: 2_variant_comparison.ipynb
   └─ Understand how variants generalize

3. Run: 3_llm_based_evaluation.ipynb
   ⚠️  Takes longer; make sure you have the API key
   └─ Evaluate quality with LLM judge

4. Run: 4_final_comparison.ipynb
   └─ See all results integrated; get recommendations
```

### Independent Execution

Each notebook can run standalone:
- **1, 2, 4** require only the CSV: `evaluation_results_comprehensive.csv`
- **3** requires additional Google API key and dataset JSON files

### Partial Execution

All notebooks support running individual cells or sections independently.

---

## 📊 Data Files Generated

After running the notebooks, you'll have:

**Notebooks 1-2 Output:**
- `healthcare_variant_comparison.png`
- `technical_variant_comparison.png`
- `financial_variant_comparison.png`
- `domain_variant_heatmap.png`
- `all_variants_comparison.png`
- 7 variant-specific PNG files: `variant_bm25_only.png`, `variant_semantic_only.png`, etc.

**Notebook 3 Output:**
- `llm_evaluation_results.csv` - LLM scores for all evaluations
- `llm_evaluation_results.png` - Quality metrics visualization

**Notebook 4 Output:**
- `final_comparison_dashboard.png` - Comprehensive comparison figure
- `PRODUCTION_DEPLOYMENT_GUIDE.txt` - Deployment recommendations

---

## 💡 Key Findings Summary

### Best Overall Configuration
**Hybrid Semantic-Heavy (30% BM25 + 20% TF-IDF + 50% Semantic)**
- Recall: 0.83 | Precision: 0.63 | Hit Rate: 0.95
- Latency: ~30ms | Consistency: Excellent across domains

### Domain-Specific Best
- **Healthcare**: Hybrid Semantic-Heavy (Recall: 0.88)
- **Technical**: Semantic-only (Recall: 0.84)
- **Financial**: Hybrid Semantic-Heavy (Recall: 0.90)

### Fastest Option
**Hybrid Balanced (33/33/33)**
- Latency: ~26ms (4ms faster than semantic-heavy)
- Recall: 0.81 (only 2% lower)
- Best for edge/mobile deployment

### Worst Performers
- BM25-only: 10-15% recall degradation
- TF-IDF-only: Similar limitations
- Avoid unless computational resources are severely constrained

---

## 🔧 Customization Guide

### Want to Modify Evaluation?

**Add more domains:**
1. Create new dataset files in `evaluation/datasets/`
2. Follow the `healthcare_qa.txt` and `healthcare_qa_reference.json` pattern
3. The notebooks will auto-discover and include them

**Change which variants are evaluated:**
1. Edit `TOP_VARIANTS` list in notebook 2 or 3
2. Modify weight parameters in `config_variants.py`
3. Re-run evaluation scripts

**Adjust LLM judgment criteria:**
1. Edit evaluation function prompts in notebook 3
2. Change scoring scale (currently 0-10)
3. Add new evaluation metrics

**Custom visualizations:**
1. All data is in pandas DataFrames
2. Create new matplotlib/plotly figures from the aggregate data
3. Examples provided in all 4 notebooks

---

## 📝 For Research Paper

### Recommended Sections

**Methods:**
- Use figures from notebooks 1-2 (methodology is clear)
- Reference evaluation metrics from notebook 4

**Results:**
- Main figure: `final_comparison_dashboard.png`
- Supporting figures: Domain heatmaps, variant comparisons
- Table: `final_comparison.ipynb` comprehensive results table

**Discussion:**
- Cite findings from `PRODUCTION_DEPLOYMENT_GUIDE.txt`
- Reference LLM evaluation metrics (notebook 3) for quality insights

**Reproduce:**
- All code is documented and commented
- Run notebooks 1-4 in sequence to regenerate all results
- Ensure `evaluation_results_comprehensive.csv` is present

---

## ⏱️ Execution Times

| Notebook | Time | Dependencies |
|----------|------|--------------|
| 1 - Domain Comparison | 30 sec | CSV only |
| 2 - Variant Comparison | 2-3 min | CSV only |
| 3 - LLM Evaluation | 5-15 min | CSV + API key + datasets |
| 4 - Final Comparison | 1-2 min | CSV (+ LLM results if available) |
| **Total** | **~10-25 min** | Depends on LLM run |

---

## ❓ FAQ

**Q: Can I skip notebook 3?**
A: Yes! Notebooks 1, 2, 4 work without it. Notebook 4 will show only retrieval metrics.

**Q: Do I need the API key for all notebooks?**
A: Only notebook 3 needs the Google API key. Provide it when running.

**Q: Can I share these notebooks?**
A: Yes! Replace the API key with a placeholder `YOUR_API_KEY_HERE` before sharing.

**Q: Which notebook should I show first?**
A: Show **notebook 4** (Final Comparison) for quick summary, then drill down with 1-3.

**Q: Why are some variants slow?**
A: Semantic-only is slower due to embedding computation. Hybrid variants add overhead but improve accuracy.

**Q: Can I use different domains?**
A: Yes! Add datasets following the pattern in `evaluation/datasets/` folder.

---

## 📞 Support

If results look unexpected:

1. **Check data exists**: `evaluation_results_comprehensive.csv`
2. **Verify aggregation**: Run the `df_agg` commands in notebooks
3. **Debug LLM**: Ensure API key is correct and rate limits not exceeded
4. **Regenerate baselines**: Run `generate_research_paper.py` if data is corrupted

---

**Created:** April 1, 2026  
**Evaluation Dataset:** 252 Q&A pairs | 7 retrieval variants | 3 domains
**Total Notebooks:** 4 comprehensive Jupyter notebooks for full transparency and explanation
