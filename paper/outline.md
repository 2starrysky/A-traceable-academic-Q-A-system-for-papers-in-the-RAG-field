# Paper Outline

## Title
Traceable Academic Q&A over RAG Papers: An Empirical Study of Retrieval and Generation Configurations

## Structure

### 1. Introduction (~300 words)
- Background: RAG widely used, but citation-level accuracy understudied
- Gap: existing eval = large-scale Wikipedia + EM; missing = small domain KB + section-level citation + oracle attribution
- Three contributions (from novelty_audit C1/C2/C3)
- Paper roadmap

### 2. Related Work (~400 words)
- 2.1 RAG Systems: Lewis 2020, Gao 2024 survey
- 2.2 Retrieval: DPR, BM25, Hybrid/RRF, Reranker/ColBERT
- 2.3 RAG Evaluation: Ragas, Verifiability, RGB, CRUD-RAG
- 2.4 Chunking: fixed vs section-aware
- 2.5 Prompt Engineering: CoT, few-shot, constraint
- 2.6 Research Gap → this paper's position

### 3. System Design (~400 words)
- 3.1 Pipeline: Query → Retrieval → Prompt → LLM → Citation Resolution
- 3.2 Document Processing: 12 PDFs → chunks (fixed 512/80)
- 3.3 Retrieval Configurations: Dense/BM25/Hybrid/Reranker
- 3.4 Generation with Citation Enforcement
- **Data source**: src/ingestion/, src/retrieval/, src/generation/, src/pipeline.py

### 4. Experimental Setup (~300 words)
- 4.1 Knowledge Base (12 papers from literature_matrix.csv)
- 4.2 Evaluation Set (50 questions, 5 types)
- 4.3 Metrics (Hit@K, MRR, Citation Accuracy, Refusal Classification)
- 4.4 Oracle Retrieval for Attribution
- 4.5 Experiment Matrix (Table: E1-E7) + Frozen Variables
- **Data source**: research/scope/, data/evaluation/questions.jsonl, final_results.csv

### 5. Results (~600 words)
- 5.1 RQ1: E1-E4 comparison (Table 1: full metrics)
  - Dense >> BM25; Hybrid recall+rank tradeoff; Reranker cost-benefit
  - Oracle attribution: gap = retrieval contribution
- 5.2 RQ2: E5 chunk ablation (Table 2: 3 strategies)
  - 512/80 best overall; section-aware clean but weaker retrieval
- 5.3 RQ3: E6 Top-K ablation (Tables 3a/3b)
  - Retrieval saturates at k=5; generation improves to k=8; no LitM degradation
- 5.4 E7 Prompt Engineering (Table 4: key sub-experiments)
  - Constraint instruction highest leverage (+26pp); combo >> single
- **Data source**: outputs/experiments/final_results.csv, outputs/system_comparison_e7.csv

### 6. Error Analysis (~300 words)
- 6.1 Error Taxonomy (10 types)
- 6.2 Per-Experiment Distribution (Table 5: E1-E4)
  - BM25 systemic failure; generation conservatism dominant in E1
- 6.3 Typical Cases (3 examples)
- **Data source**: research/error_analysis.md, outputs/error_analysis.json

### 7. Discussion (~200 words)
- 7.1 Practical implications (4 recommendations)
- 7.2 Prompt engineering value quantification

### 8. Limitations (~150 words)
- Small KB (12 papers), single LLM, LLM-judge variance, example domain shift, no GPU, 50 questions

### 9. Conclusion (~150 words)
- Answer RQ1-RQ3
- Summarize contributions
- Future work

### Abstract (~150 words, written last)
- Problem → Method → Key findings → Contributions

## References
- 12 knowledge base papers + supporting methods (BM25, FAISS, SBERT, BGE, CoT)
- Total ~17 entries in references.bib

## Figures
- paper/figures/01_hit_k_comparison.png — RQ1 Hit@K bar chart
- paper/figures/05_error_distribution.png — Error type distribution
- paper/figures/06_topk_ablation.png — RQ3 Top-K results
- paper/figures/fig7_prompt_ablation.png — E7 prompt comparison
- paper/figures/fig8_prompt_heatmap.png — E7 strategy × question type heatmap

## Word Count Target
- Total: ~3000-4000 words (8-10 pages with tables/figures)
