# Review Round 1 (Day 19) — Simulated Peer Review

> Reviewer type: Methodology-focused + Full paper review
> Paper: "Traceable Academic Q&A over RAG Papers: An Empirical Study of Retrieval and Generation Configurations"
> Version reviewed: manuscript.md (v1, 3538 words)

---

## 1. Citation Authenticity ✅ PASS

All 11 citations in the manuscript map to real, published papers in references.bib. No fabricated references. No orphan citations in bib (6 entries exist but are not cited — see citation_audit.md for details).

**Action needed**: Add 5 missing citations (gao2022hyde, izacard2020fid, yan2024crag, xiao2023bge, johnson2019faiss) to manuscript body. This is a minor fix, not a rejection issue.

---

## 2. Do Citations Support Claims? ✅ PASS

Every major empirical claim is bound to either:
- Experimental data (Tables 1-5, "As shown in Table X")
- Published literature (proper \cite{} reference)

Spot-checked 9 key claims (see citation_audit.md Section 2). All verified. No unsupported claims found.

---

## 3. Method-Code Consistency ⚠️ MINOR ISSUES

Based on code review of src/retrieval/, src/generation/, src/ingestion/, and src/pipeline.py:

| Paper Claim | Code Reality | Severity |
|---|---|---|
| "BM25 with tiktoken tokenization" | BM25 uses rank_bm25.BM25Okapi + tiktoken cl100k_base | ✅ Consistent |
| "FAISS IndexFlatIP" | dense.py uses faiss.IndexFlatIP with normalize_embeddings=True | ✅ Consistent |
| "Hybrid: each retriever returns top-10" | run_experiment.py uses top_k*2=10 for E3 (top_k=5) | ✅ Consistent |
| "bge-reranker-v2-m3 cross-encoder" | reranker.py uses SentenceTransformer('BAAI/bge-reranker-v2-m3') | ✅ Consistent |
| "temperature=0.2" | generator.py uses model parameter, configs set 0.2 | ✅ Consistent |
| "chunk_size=512, overlap=80" | splitter.py split_fixed(512, 80) | ✅ Consistent |
| "citation parser discards out-of-range [n]" | generator.py _parse_citations checks 1<=n<=len(hits) | ✅ Consistent |
| "BM25 is described as 'term frequency scoring'" | Actually BM25Okapi = TF-IDF with length normalization. Wording is imprecise. | ⚠️ LOW: Should say "BM25Okapi scoring" not "term frequency scoring" |
| "Hybrid top-10 is fixed design" | Actually top_k*2 parameterized (10 = 2×5). Accurate for E3 but parameterized. | ⚠️ LOW: Minor wording precision |

**Verdict**: No HIGH or MEDIUM severity discrepancies. Two LOW-severity wording imprecisions that should be fixed for accuracy but do not affect conclusions.

---

## 4. Table Data vs Raw Results ✅ PASS

| Table | Source File | Status |
|---|---|---|
| Table 1 (E1-E4 main) | final_results.csv | ✅ All 32 values match (rounded to 3 decimals) |
| Table 2 (E5 chunk) | final_results.csv | ✅ All values match |
| Table 3a (E6 retrieval) | final_results.csv | ✅ All values match |
| Table 3b (E6 generation) | final_results.csv | ✅ All values match |
| Table 4 (E7 prompt) | system_comparison_e7.csv + raw E7.1/E7.2 JSON | ✅ All values match |
| Table 5 (Error) | error_analysis.md | ✅ All values match |

**No data fabrication detected.**

---

## 5. Innovation Claims ⚠️ MINOR OVERSTATEMENT

**ISSUE**: The Introduction states "We present an empirical study..." which is appropriately modest. However, the contribution framing could be more precise.

**Current wording**: "Our study makes three contributions: (1) Experimental... (2) Evaluation... (3) Analytical..."

**Concern**: The term "contribution" in academic context can imply novelty beyond what this paper delivers. The novelty_audit.md correctly identifies this as "experimental + evaluation + analytical" type, not algorithmic.

**Recommendation**: Replace "contributions" with "we report" or "we present findings" to avoid implying novelty claims. The novelty_audit.md anti-overselling checklist (rule 1: no "first/initial") is followed — no "first" claims found. ✅

**Severity**: LOW — wording adjustment, not a factual error.

---

## 6. Baseline Fairness ✅ PASS

- All experiments use the same 50-question evaluation set (human-verified)
- E1-E6 share frozen variables (bge-m3, DeepSeek, fixed prompt, 512/80 chunking except E5)
- Control variable method is correctly applied: one variable changed at a time
- E7 reuses E4 retrieval results (frozen retrieval, only prompt varies)

**No unfair baseline comparisons detected.**

---

## 7. Data Leakage ✅ PASS

- Evaluation set (questions.jsonl) is separate from knowledge base (documents.jsonl)
- Few-shot examples in E7 are hand-crafted general RAG examples, NOT drawn from the 12-paper knowledge base (acknowledged in Limitations as "example domain shift")
- No training/fine-tuning performed — all models used in inference mode
- Oracle retrieval uses gold chunk IDs from evaluation set, but this is explicitly a diagnostic tool, not a system component

**No data leakage detected.**

---

## 8. Reproducibility ⚠️ MOSTLY PASS

**Strengths**:
- All experiment configs record git commit hash (config.json in each experiment directory)
- Evaluation set version recorded
- Model names and parameters specified (bge-m3, deepseek-chat, bge-reranker-v2-m3)
- Chunks and indices reproducible from documented parameters

**Weaknesses**:
- No random seed explicitly reported (though temperature=0.1/0.2 provides some determinism)
- E7 LLM-as-judge is inherently non-deterministic (~5% variance acknowledged in Limitations)
- DeepSeek API may produce slightly different results across runs

**Verdict**: Reproducibility is acceptable for a workshop-style report. Noted in Limitations.

---

## Overall Assessment

| Criterion | Verdict |
|---|---|
| Citation Authenticity | ✅ PASS |
| Claim-Citation Binding | ✅ PASS |
| Method-Code Consistency | ⚠️ 2 LOW wording fixes |
| Data Consistency | ✅ PASS |
| Innovation Claims | ⚠️ 1 LOW wording adjustment |
| Baseline Fairness | ✅ PASS |
| Data Leakage | ✅ PASS |
| Reproducibility | ⚠️ PASS with caveats |

**Recommendation**: ACCEPT with minor revisions. No rejection-level issues. All changes required are LOW-severity wording improvements.

### Required Revisions
1. Add 5 missing citations (gao2022hyde, izacard2020fid, yan2024crag, xiao2023bge, johnson2019faiss)
2. Fix "term frequency scoring" → "BM25Okapi scoring" in §3.3
3. Clarify "top-10" as "top-2×k" parameterized in §3.3
4. Soften "contributions" wording in Introduction
