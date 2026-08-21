# Citation Audit Report (Day 19)

## 1. Citation Completeness

### All citations in manuscript → bib mapping

| Citation Key | In Bib? | Context Accuracy |
|---|---|---|
| chen2023rgb | ✅ | ✅ Correct: cited for four-ability diagnostic framework and negative rejection |
| es2025ragas | ✅ | ✅ Correct: cited for reference-free LLM-judge evaluation |
| gao2024survey | ✅ | ✅ Correct: cited for RAG architectures, hybrid retrieval, chunking survey |
| karpukhin2020dpr | ✅ | ✅ Correct: cited for dense retrieval superiority over BM25 (9-19%) |
| khattab2020colbert | ✅ | ✅ Correct: cited for late interaction reranking |
| lewis2021rag | ✅ | ✅ Correct: cited as RAG origin paper |
| liu2023litm | ✅ | ✅ Correct: cited for lost-in-the-middle phenomenon and position effects |
| liu2023verifiability | ✅ | ✅ Correct: cited for dual-layer citation metrics |
| lyu2024crudrag | ✅ | ✅ Correct: cited for component-level evaluation |
| robertson2009bm25 | ✅ | ✅ Correct: cited for BM25 background |
| wei2022cot | ✅ | ✅ Correct: cited for Chain-of-Thought prompting |

**Result**: 11/11 citations in manuscript are present in bib and accurately described. ✅ No orphan citations.

### Bib entries NOT cited in manuscript

| Bib Key | Paper | Recommendation |
|---|---|---|
| gao2022hyde | HyDE (Gao et al. 2022) | **SHOULD CITE**: Knowledge base member, mentioned in Section 4.1 but not cited. Add to Related Work §2.2 or §4.1. |
| izacard2020fid | FiD (Izacard et al. 2020) | **SHOULD CITE**: Referenced in Section 5.3 "Contrary to FiD" but not formally cited. Add to §2.2 or §5.3. |
| yan2024crag | CRAG (Yan et al. 2024) | **SHOULD CITE**: Knowledge base member, mentioned in Section 4.1 but not cited. Add to Related Work §2.2. |
| xiao2023bge | BGE (Xiao et al. 2023) | **SHOULD CITE**: Used as embedding model (bge-m3) throughout. Add to §3.3. |
| johnson2019faiss | FAISS (Johnson et al. 2019) | **SHOULD CITE**: Used as vector index in §3.3. Add to §3.3. |
| reimers2019sbert | Sentence-BERT | **OPTIONAL**: Background for bi-encoder approach. Can add to §2.2 if space permits. |

**Action Required**: Add 5 missing citations (gao2022hyde, izacard2020fid, yan2024crag, xiao2023bge, johnson2019faiss) to manuscript.

## 2. Claim-Citation Binding

Every major claim in the manuscript is bound to either experimental data ("As shown in Table X") or a citation. Verified:

| Claim | Evidence Source | Status |
|---|---|---|
| Dense outperforms BM25 by 9-19% | Karpukhin 2020 §5.1 | ✅ |
| BM25 Hit@1=0.00 on Chinese queries | E2 experiment | ✅ |
| Hybrid recovers 10/11 E1 failures | E3 per-question analysis | ✅ |
| Reranker improves citation accuracy | E4 vs E3 | ✅ |
| Lost in the Middle U-shaped curve | Liu 2023 | ✅ |
| No LitM degradation at K=8 | E6 results | ✅ |
| Constraint instruction +26pp | E7.4 results | ✅ |
| Only 51.5% sentences fully supported | Verifiability paper | ✅ |
| Faithfulness = reference-free LLM judge | Ragas paper | ✅ |

## 3. Summary

- **Citation completeness**: 5 entries need to be added to manuscript (see Section 1)
- **Citation accuracy**: All existing citations are correctly attributed ✅
- **Claim binding**: All major claims have evidence sources ✅
- **No fabricated references** ✅
