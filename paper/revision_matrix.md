# Revision Matrix (Day 19)

> Tracks every finding from citation_audit.md and review_round_1.md, its fix action, and status.

| # | Source | Finding | Severity | Action | Status |
|---|--------|---------|----------|--------|--------|
| 1 | citation_audit | Missing cite: gao2022hyde (HyDE) | MEDIUM | Add \cite{gao2022hyde} in §2.2 or §4.1 | ✅ Fixed |
| 2 | citation_audit | Missing cite: izacard2020fid (FiD) | MEDIUM | Add \cite{izacard2020fid} in §2.2 or §5.3 | ✅ Fixed |
| 3 | citation_audit | Missing cite: yan2024crag (CRAG) | MEDIUM | Add \cite{yan2024crag} in §2.2 | ✅ Fixed |
| 4 | citation_audit | Missing cite: xiao2023bge (BGE) | MEDIUM | Add \cite{xiao2023bge} in §3.3 | ✅ Fixed |
| 5 | citation_audit | Missing cite: johnson2019faiss (FAISS) | LOW | Add \cite{johnson2019faiss} in §3.3 | ✅ Fixed |
| 6 | review §3 | "term frequency scoring" imprecise for BM25Okapi | LOW | Change to "BM25Okapi scoring with IDF and length normalization" | ✅ Fixed |
| 7 | review §3 | "top-10" not explained as parameterized | LOW | Clarify "top-2×k candidates per retriever" | ✅ Fixed |
| 8 | review §5 | "contributions" wording could imply overstatement | LOW | Soften to "we report three key findings" or similar | ✅ Fixed |

**All 8 findings fixed in manuscript_v2.md.**
