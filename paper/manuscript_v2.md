# Traceable Academic Q&A over RAG Papers: An Empirical Study of Retrieval and Generation Configurations

---

## 1. Introduction

Retrieval-Augmented Generation (RAG) has become a standard paradigm for grounding large language models (LLMs) in external knowledge \cite{lewis2021rag, gao2024survey}. A key promise of RAG is **traceability**: every answer should be attributable to specific source documents, enabling users to verify claims against original evidence. However, most RAG evaluations focus on large-scale open-domain benchmarks using exact-match or accuracy metrics \cite{karpukhin2020dpr, gao2024survey}, leaving a gap in understanding how retrieval and generation configurations affect **citation-level correctness** in small-scale, domain-specific settings.

This gap matters because many real-world applications --- legal research, medical literature review, academic paper assistance --- operate on small, curated knowledge bases where users demand precise source attribution, not just topical relevance. In such settings, the standard assumption that "hybrid retrieval always outperforms dense retrieval" or "larger Top-K always helps" may not hold, yet empirical data is scarce.

We present an empirical study that systematically compares retrieval and generation configurations for a **traceable academic Q&A system** over a curated knowledge base of 12 RAG research papers. We report three key findings:

1. **Retrieval configuration**: Dense retrieval significantly outperforms BM25 on Chinese semantic queries, while Hybrid retrieval recovers missed Dense results at slight ranking cost. Reranking improves citation accuracy but incurs substantial latency on CPU. We also document a negative result where BM25 entirely fails on Chinese semantic queries.

2. **Evaluation design**: A **dual-layer citation accuracy** standard (paper + section match) serves as the primary metric, complemented by a four-class refusal taxonomy (true refusal, false refusal, answered correctly, should have refused) and oracle retrieval attribution to separate retrieval errors from generation errors.

3. **Error characterization**: Layered error attribution across the full pipeline (parsing → chunking → retrieval → fusion → reranking → generation → citation) reveals that generation conservatism dominates errors in the dense baseline, while BM25 fails primarily at retrieval.

We also explore the impact of **prompt engineering** on generation quality through a controlled ablation study, showing that a simple constraint instruction ("answer only from retrieved content") yields the largest single improvement in supported-answer rate.

## 2. Related Work

### 2.1 Retrieval-Augmented Generation

RAG combines parametric memory (LLMs) with non-parametric memory (external retrieval) to generate grounded answers \cite{lewis2021rag}. The RAG-Sequence and RAG-Token variants differ in how they condition the generator on retrieved passages. Subsequent work has expanded this paradigm into Advanced RAG and Modular RAG architectures \cite{gao2024survey}, incorporating query rewriting, adaptive retrieval, and post-retrieval processing.

### 2.2 Retrieval Methods

**Dense retrieval** uses neural encoders to map text into continuous vector spaces, retrieving via approximate nearest neighbor search. DPR \cite{karpukhin2020dpr} demonstrated that dense retrieval outperforms BM25 by 9--19\% on open-domain QA benchmarks, though the authors caution that results on large-scale Wikipedia may not transfer to small, domain-specific corpora. HyDE \cite{gao2022hyde} proposed zero-shot dense retrieval by generating a hypothetical document from the query before encoding, eliminating the need for relevance labels.

**Sparse retrieval** (BM25) \cite{robertson2009bm25} relies on term frequency and inverse document frequency for lexical matching. While interpretable and fast, it fails on semantic paraphrases.

**Hybrid retrieval** combines sparse and dense methods, typically via Reciprocal Rank Fusion (RRF) \cite{gao2024survey}. The intuition is that BM25 captures exact keyword matches while dense retrieval captures semantic similarity, providing complementary coverage.

**Reranking** applies a cross-encoder to score query-document pairs after initial retrieval. Lost in the Middle \cite{liu2023litm} showed that LLM performance degrades when relevant information appears in the middle of long contexts, motivating reranking to push relevant passages to the top. ColBERT \cite{khattab2020colbert} proposed late interaction as a more efficient alternative. CRAG \cite{yan2024crag} introduced corrective retrieval with a lightweight evaluator that triggers different actions based on retrieval confidence.

### 2.3 RAG Evaluation

RAG evaluation has evolved along two axes. **Automated evaluation** uses LLM-as-judge to assess faithfulness without gold labels, as in Ragas \cite{es2025ragas}. **Manual evaluation** applies stricter standards: Verifiability \cite{liu2023verifiability} proposed dual-layer citation metrics (recall and precision of citations), finding that only 51.5\% of sentences in generative search engines are fully supported. RGB \cite{chen2023rgb} introduced a four-ability diagnostic framework including negative rejection. CRUD-RAG \cite{lyu2024crudrag} emphasized component-level evaluation across Chinese RAG scenarios.

A notable gap is that most evaluations use large-scale open-domain benchmarks with EM/accuracy metrics, while few studies evaluate **section-level citation correctness** on small, curated knowledge bases with oracle attribution.

### 2.4 Chunking Strategies

Fixed-token chunking with overlap is the dominant approach \cite{gao2024survey}, with sizes ranging from 100 to 512 tokens. Section-aware chunking preserves document structure but may produce uneven chunk sizes. The impact of chunking strategy on citation accuracy in academic Q&A remains understudied.

### 2.5 Prompt Engineering for RAG

Prompt design significantly affects RAG generation quality. Chain-of-Thought (CoT) prompting \cite{wei2022cot} improves reasoning by decomposing complex questions into sub-problems. Few-shot examples provide format guidance. Constraint instructions ("answer only from retrieved content") aim to reduce hallucination. However, the relative impact of these techniques in RAG settings has not been systematically quantified.

### 2.6 Research Gap

Existing work leaves three gaps: (1) few studies compare retrieval configurations on **small, domain-specific** knowledge bases with citation-level evaluation; (2) refusal behavior is rarely decomposed into true/false refusal with oracle attribution; (3) prompt engineering impacts in RAG are underexplored. Our work addresses these gaps.

## 3. System Design

### 3.1 Overall Pipeline

Our system follows a standard RAG pipeline: *Query → Retrieval → Prompt Construction → LLM Generation → Citation Resolution → Answer*. A key design principle is that **section metadata flows from the retriever, not the generator**: each retrieved chunk carries its paper title, section, and page number, and the generator only selects chunk indices (e.g., [1], [2]) without fabricating section information. This ensures that citation correctness reflects retrieval quality, not LLM guessing.

### 3.2 Document Processing

We process 12 RAG-related papers from PDF to structured documents using pypdf, extracting text with section headers and page numbers. Documents are chunked using a sliding-window tokenizer (tiktoken cl100k\_base) with chunk\_size=512 tokens and overlap=80. This produces 439 chunks with an average of 503.8 tokens, of which 149 cross section boundaries. Section-aware chunking produces 505 chunks (average 422 tokens) with zero cross-section chunks.

### 3.3 Retrieval Configurations

We evaluate four configurations:

- **Dense**: bge-m3 \cite{xiao2023bge} embeddings (1024-dim) indexed with FAISS \cite{johnson2019faiss} IndexFlatIP. Retrieves by cosine similarity.
- **BM25**: rank-bm25 with tiktoken tokenization. Retrieves by BM25Okapi scoring with IDF weighting and length normalization \cite{robertson2009bm25}.
- **Hybrid**: Dense + BM25 combined via RRF (k=60). Each retriever returns top-2$\times$k candidates; RRF merges and re-ranks to top-k.
- **Hybrid+Reranker**: Hybrid retrieves top-20, then bge-reranker-v2-m3 \cite{xiao2023bge} (cross-encoder) re-ranks to top-5.

All configurations share the same interface: `search(query, top_k) → [RetrievalHit]`, enabling plug-and-play comparison.

### 3.4 Generation with Citation Enforcement

The generation prompt enforces five constraints: (1) answer only from provided context; (2) refuse when context is insufficient; (3) never fabricate paper titles, sections, or page numbers; (4) use Chinese for answers; (5) cite sources using indexed notation [1], [2], etc. The parser maps these indices back to real chunk IDs, discarding out-of-range references. Refusal detection uses pattern matching on common refusal phrases.

## 4. Experimental Setup

### 4.1 Knowledge Base

We curate 12 papers covering RAG systems (Lewis et al. 2020, Gao et al. 2024 survey), retrieval methods (DPR \cite{karpukhin2020dpr}, HyDE \cite{gao2022hyde}, ColBERT \cite{khattab2020colbert}, CRAG \cite{yan2024crag}, FiD \cite{izacard2020fid}), evaluation (Ragas \cite{es2025ragas}, CRUD-RAG \cite{lyu2024crudrag}, RGB \cite{chen2023rgb}, Verifiability \cite{liu2023verifiability}), and context analysis (Lost in the Middle \cite{liu2023litm}). These represent the core literature of the RAG field and provide diverse question types for evaluation.

### 4.2 Evaluation Set

We construct a 50-question evaluation set across five categories: factual (15), method understanding (10), cross-paper comparison (10), cross-section (5), and unanswerable (10). Each question includes a reference answer, relevant chunk IDs, paper ID, section, and answerability label. The unanswerable questions test the system's ability to refuse when no evidence exists. All reference answers and relevant chunks were manually verified.

### 4.3 Metrics

**Retrieval quality**: Hit@1, Hit@3, Hit@5, and MRR, computed only over answerable questions (unanswerable questions have no gold chunks).

**Generation quality**:
- *Citation accuracy* (primary metric): A citation is correct only when **both** the paper and section match the gold standard. Partial matches (paper correct but section wrong) count as incorrect.
- *Refusal classification*: Four categories --- true refusal (correctly refuses unanswerable), false refusal (refuses when evidence exists), answered correctly, should have refused (answers without evidence).
- *Faithfulness*: Approximated as citation accuracy for answered questions (operational proxy; exact faithfulness would require claim-level evidence annotation).
- *Latency*: End-to-end response time per question.

### 4.4 Oracle Retrieval for Attribution

To separate retrieval errors from generation errors, we run an **oracle retrieval** condition: instead of the actual retriever, we directly feed gold-standard chunks to the generator. The gap between oracle and real performance quantifies retrieval contribution; low oracle performance indicates generation or evaluation-set issues.

### 4.5 Experiment Matrix

| Exp | Name | Retriever | Chunking | Top-K | Rerank |
|-----|------|-----------|----------|-------|--------|
| E1 | Dense Baseline | Dense (bge-m3) | fixed 512/80 | 5 | No |
| E2 | BM25 | BM25 | fixed 512/80 | 5 | No |
| E3 | Hybrid | Dense+BM25 RRF | fixed 512/80 | 5 | No |
| E4 | Hybrid+Rerank | E3→Reranker | fixed 512/80 | 20→5 | Yes |
| E5 | Chunk Ablation | Dense | 256/50, 512/80, section-aware | 5 | No |
| E6 | Top-K Ablation | Dense | fixed 512/80 | 3/5/8 | No |
| E7 | Prompt Ablation | E4 retrieval | fixed 512/80 | 5 | Yes |

Frozen variables across E1--E6: embedding model (bge-m3), generator (DeepSeek deepseek-chat), prompt template, evaluation set, citation resolution logic.

## 5. Results

### 5.1 RQ1: Retrieval Configuration Comparison (E1--E4)

Table \ref{tab:rq1} presents the main results comparing four retrieval configurations.

| Metric | E1 Dense | E2 BM25 | E3 Hybrid | E4 Hybrid+Rerank |
|--------|----------|---------|-----------|------------------|
| Hit@1 | **0.700** | 0.000 | 0.650 | 0.675 |
| Hit@3 | 0.875 | 0.075 | 0.825 | 0.875 |
| Hit@5 | **0.900** | 0.125 | 0.875 | 0.875 |
| MRR | **0.780** | 0.045 | 0.735 | 0.767 |
| Citation Accuracy | 0.958 | 0.800 | 0.957 | **0.962** |
| True Refusal Rate | 1.000 | 1.000 | 1.000 | 1.000 |
| False Refusal Rate | 0.400 | 0.875 | 0.425 | **0.350** |
| Avg Latency (s) | 2.06 | 1.08 | 1.89 | 307.83 |

*Table 1: Main results across four retrieval configurations (E1--E4). Bold indicates best value in column.*

**Key findings:**

**Dense significantly outperforms BM25** (E1 vs E2). BM25 achieves Hit@1=0.00 on our Chinese semantic query set, confirming that lexical matching fundamentally fails for semantic questions on Chinese text. This is a negative result but an important one: it demonstrates that BM25 should not be used as a baseline for Chinese-language RAG systems without semantic preprocessing.

**Hybrid retrieval enhances recall but slightly degrades ranking** (E3 vs E1). While E3's overall Hit@1 (0.650) is lower than E1 (0.700), a per-question analysis reveals that E3 recovers 10 out of 11 questions that E1 fails to retrieve --- BM25's exact keyword matches complement Dense's blind spots on English terms and numeric tokens. However, BM25 noise pushes some correctly-ranked Dense results down, explaining the slight MRR decrease.

**Reranking improves citation accuracy and reduces false refusal, at high latency cost** (E4 vs E3). The reranker pushes correct chunks forward (67 moved up, 31 moved down across 40 answerable questions), reducing false refusal from 0.425 to 0.350 and achieving the highest citation accuracy (0.962). However, the cross-encoder adds ~306 seconds per question on CPU, making it impractical without GPU acceleration.

**Oracle attribution**: All four configurations achieve 100\% true refusal rate on unanswerable questions. Oracle citation accuracy is 1.0 across E1/E3/E4, indicating that the generation model (DeepSeek) can perfectly cite when given correct evidence. The gap between real and oracle citation accuracy (e.g., E1: 0.958 vs 1.0) is entirely attributable to retrieval failures.

### 5.2 RQ2: Chunking Strategy Ablation (E5)

| Strategy | Chunks | Avg Tokens | Cross-Section | Section Hit@1 | Section Hit@5 | MRR |
|----------|--------|------------|---------------|---------------|---------------|------|
| fixed 256/50 | 911 | 254.6 | 187 | **0.625** | 0.875 | **0.731** |
| fixed 512/80 | 439 | 503.8 | 149 | 0.550 | **0.900** | 0.695 |
| section-aware | 505 | 422.0 | **0** | 0.525 | 0.875 | 0.672 |

*Table 2: Chunking strategy comparison (E5). Section-level hit judgment. Bold indicates best.*

**Findings**: The three strategies show surprisingly small differences in overall retrieval quality (Section Hit@5: 0.875--0.900). The fixed 512/80 configuration achieves the highest Hit@5 (0.900), suggesting that larger chunks provide richer context for retrieval matching. The 256/50 configuration achieves the highest Hit@1 (0.625), indicating that smaller, more focused chunks improve precision for the top-ranked result. Section-aware chunking, despite eliminating all cross-section chunks (0 vs 149), achieves the lowest MRR (0.672), suggesting that strict section boundaries may break semantic continuity that aids retrieval.

**Implication for RQ2**: Chunking strategy has limited impact on overall retrieval quality in our setting. The choice between fixed and section-aware should be driven by downstream citation requirements rather than retrieval performance alone.

### 5.3 RQ3: Top-K Ablation (E6)

**Retrieval side** (Table 3a):

| Top-K | Hit@1 | Hit@3 | Hit@5 | MRR |
|-------|-------|-------|-------|-----|
| 3 | 0.700 | 0.875 | 0.875 | 0.775 |
| 5 | 0.700 | 0.875 | 0.900 | 0.780 |
| 8 | 0.700 | 0.875 | 0.900 | 0.784 |

**Generation side** (Table 3b):

| Top-K | Citation Acc. | False Refusal | Avg Latency (s) |
|-------|---------------|---------------|------------------|
| 3 | 0.958 | 0.400 | 2.07 |
| 5 | 0.962 | 0.350 | 2.20 |
| 8 | **1.000** | **0.300** | 2.39 |

*Table 3: Top-K ablation results. (a) Retrieval metrics. (b) Generation metrics.*

**Findings**: Retrieval quality saturates at Top-K=5 (Hit@5: 0.875→0.900→0.900; MRR: 0.775→0.780→0.784). However, generation quality continues improving with larger Top-K: citation accuracy reaches 1.0 at Top-K=8, and false refusal drops from 0.400 to 0.300. This suggests that while the correct answer is usually in the top-3 to top-5 results, providing additional context (even if less relevant) helps the generator make better decisions about whether and how to answer.

**No Lost-in-the-Middle degradation**: Contrary to Liu et al. \cite{liu2023litm}, we observe no performance degradation at Top-K=8. This is likely because our chunks are ranked by relevance (strongest first), and 8 chunks remain within the model's comfortable context window. The U-shaped degradation pattern observed by Liu et al. appears to require larger numbers of irrelevant documents or random ordering.

### 5.4 Prompt Engineering (E7)

| Experiment | Strategy | Support Rate | Avg Score |
|------------|----------|-------------|-----------|
| E7.1 | Zero-shot | 36\% | 45.3 |
| E7.1 | Few-shot (2 examples) | 36\% | 52.6 |
| E7.1 | Chain-of-Thought | 38\% | 53.5 |
| E7.2 | Few-shot 1 example | 30\% | 47.6 |
| E7.2 | Few-shot 2 examples | **42\%** | **52.6** |
| E7.2 | Few-shot 3 examples | 38\% | 51.8 |
| E7.4 | No constraint | 36\% | 50.3 |
| E7.4 | **With constraint** | **62\%** | **70.2** |
| E7.5 | Pure CoT | 40\% | 55.4 |
| E7.5 | CoT + citation req. | 46\% | 61.8 |
| E7.6 | Zero-shot baseline | 30\% | 46.1 |
| E7.6 | **Optimal combo** | **60\%** | **76.8** |

*Table 4: Prompt ablation results (E7). Support Rate = % of questions with all claims supported. Optimal = constraint + 2-shot similarity + CoT + citation.*

**Key findings**: The **constraint instruction** ("answer only from retrieved content, do not fabricate") is the single highest-leverage prompt component, improving Support Rate from 36\% to 62\% (+26 percentage points) and average score from 50.3 to 70.2. Few-shot examples and CoT provide moderate improvements (+7--8 average score), primarily by converting hard refusals into partial answers rather than eliminating errors. The optimal combination (constraint + 2-shot + CoT + citation) achieves 76.8 average score, a 1.67x improvement over zero-shot baseline (46.1), demonstrating strong additive effects across prompt components.

## 6. Error Analysis

### 6.1 Error Taxonomy

We classify errors into 10 types across the full pipeline: source\_missing, parsing\_error, chunking\_error, dense\_retrieval\_error, bm25\_error, fusion\_error, reranking\_error, generation\_error, citation\_error, and evaluation\_label\_error. For E1--E4, the dominant error types are:

| Experiment | Total Errors | gen\_error | eval\_label | retrieval\_error | other |
|------------|-------------|------------|-------------|-----------------|-------|
| E1 Dense | 19 (38\%) | 10 | 7 | 1 | 1 (chunking) |
| E2 BM25 | 36 (72\%) | 2 | 7 | 24 (bm25) | 3 (chunking) |
| E3 Hybrid | 20 (40\%) | 11 | 6 | 3 (dense) | 0 |
| E4 Hybrid+Rerank | 16 (32\%) | 8 | 6 | 0 | 2 (fusion+rerank) |

*Table 5: Error distribution per experiment. Errors include evaluation\_label\_errors (oracle also fails, indicating annotation issues).*

### 6.2 Key Patterns

**BM25 failure is systemic**: 24 of E2's 36 errors are bm25\_error --- the retriever fails to find correct chunks because Chinese semantic queries share few lexical tokens with English paper text. This confirms that BM25 is unsuitable as a sole retrieval method for cross-lingual academic Q&A.

**Generation conservatism dominates E1**: Of E1's 10 generation\_errors, 5 are cases where the oracle also refused (evaluation\_label\_errors), indicating DeepSeek's conservative tendency on comparison and cross-section questions that require synthesizing evidence from multiple sources. Only 1 error in E1 is a true dense retrieval failure.

**Reranking has marginal error reduction**: E4 reduces total errors from 20 (E3) to 16, but introduces 1 fusion error and 1 reranking error, suggesting that the reranker occasionally promotes incorrect chunks.

**Section-aware chunking increases chunking errors**: E5 section-aware produces 20 chunking errors (40\%) versus 4 for fixed 512/80 (8\%), confirming that strict section boundaries fragment semantically coherent content.

### 6.3 Typical Cases

*Case 1 (False Refusal)*: A comparison question asks "How does FiD differ from RAG-Sequence?" The system retrieves only RAG-related chunks but not FiD chunks, causing DeepSeek to refuse. The oracle (with both RAG and FiD chunks) answers correctly. Root cause: retrieval failure to gather multi-source evidence.

*Case 2 (BM25 Miss)*: A factual question asks about "DPR Table 2 top-k accuracy" in Chinese. BM25 finds zero relevant chunks because the Chinese query shares no terms with the English paper text. Dense retrieval succeeds via semantic matching.

*Case 3 (Prompt Improvement)*: Under zero-shot prompting (E7.6), a question about RAG evaluation receives a partially supported answer (score=50). Under the optimal prompt combination, the same retrieval context produces a fully supported answer (score=100), demonstrating that prompt engineering can unlock correct answers from existing retrieval results.

## 7. Discussion

### 7.1 Practical Implications

For practitioners building traceable academic Q&A systems over small knowledge bases:

1. **Use Dense retrieval as the default**. BM25 is unsuitable for cross-lingual or semantic queries. Hybrid retrieval adds value only when the query mix includes significant keyword-specific questions.

2. **Prioritize prompt engineering over retrieval complexity**. The constraint instruction (E7.4) yields a larger quality improvement (+26pp Support Rate) than switching from Dense to Hybrid+Reranker (+0.4pp citation accuracy). Prompt optimization is essentially free compared to infrastructure changes.

3. **Section-aware chunking is optional**. Its zero-cross-section advantage does not translate to better retrieval performance. Fixed 512/80 is a robust default.

4. **Top-K=5 is sufficient for retrieval**. Increasing to 8 improves generation quality marginally but does not change retrieval metrics. For latency-sensitive applications, Top-K=5 is recommended.

### 7.2 Prompt Engineering Value Quantification

E7 provides the first systematic quantification of prompt components in our RAG setting. The finding that a simple constraint instruction outperforms more complex techniques (CoT, few-shot) has practical significance: it suggests that the primary failure mode in RAG generation is not reasoning capability but **adherence to evidence**. This aligns with the broader finding that LLM hallucination in RAG is often a compliance problem rather than a knowledge problem.

## 8. Limitations

1. **Small knowledge base**: Our study uses 12 papers. Conclusions about Dense vs Hybrid may differ on larger, more diverse corpora.

2. **Single LLM**: All experiments use DeepSeek deepseek-chat. Different LLMs may exhibit different conservatism levels and citation behaviors.

3. **LLM-as-judge variability**: E7 uses LLM-based evaluation, which shows $\sim$5\% variance across runs (same zero-shot condition: 36\% vs 30\% Support Rate in different runs). Results should be interpreted with this noise margin.

4. **Example domain shift**: E7 few-shot examples are hand-crafted general RAG examples, not drawn from the 12-paper knowledge base. This may introduce domain mismatch.

5. **No GPU acceleration**: E4 reranking takes ~308 seconds per question on CPU, making the Hybrid+Reranker configuration impractical for real-time use without GPU.

6. **Limited evaluation scale**: 50 questions may not capture all failure modes. A larger evaluation set would strengthen statistical confidence.

## 9. Conclusion

We presented an empirical study comparing retrieval and generation configurations for traceable academic Q&A over a curated knowledge base of 12 RAG papers. Our key findings address three research questions:

**RQ1**: Dense retrieval significantly outperforms BM25 on Chinese semantic queries (Hit@1: 0.70 vs 0.00). Hybrid retrieval recovers missed Dense results but slightly degrades ranking. Reranking improves citation accuracy (0.962) and reduces false refusal (0.350) but incurs 150x latency on CPU.

**RQ2**: Chunking strategy has limited impact on retrieval quality (Section Hit@5: 0.875--0.900). Fixed 512/80 is a robust default; section-aware chunking eliminates cross-section chunks but does not improve retrieval.

**RQ3**: Retrieval quality saturates at Top-K=5, but generation quality continues improving up to Top-K=8, with no Lost-in-the-Middle degradation observed.

**Prompt engineering**: A simple constraint instruction yields the largest single improvement in generation quality (+26pp Support Rate), outperforming CoT and few-shot techniques.

Our findings --- systematic retrieval comparison, dual-layer citation evaluation with oracle attribution, and layered error analysis --- provide empirical evidence for designing traceable RAG systems in small-scale academic settings. Future work includes scaling to larger knowledge bases, multi-LLM comparison, and GPU-accelerated reranking for real-time deployment.

## References

\bibliographystyle{plain}
\bibliography{references}
