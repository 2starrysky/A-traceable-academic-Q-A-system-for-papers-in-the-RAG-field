"""错误分析:归纳失败模式,为改进提供依据。

错误分类体系 (Day 16 plan):
    source_missing          -- 知识库未收录该论文/该章节(paper_id 在任何 chunk 中都未出现)
    parsing_error           -- PDF 解析失败导致关键内容缺失(无法从评估数据自动检测,留作扩展)
    chunking_error          -- gold 论文被检到但相关段落被切块边界拆散(同论文不同 chunk)
    dense_retrieval_error   -- dense 检索未召回 gold chunk
    bm25_error              -- BM25 检索未召回 gold chunk
    fusion_error            -- 混合检索融合策略未能保留 gold chunk
    reranking_error         -- 重排器将 gold chunk 从粗排 Top-K 中推出
    generation_error        -- 有证据却误拒 / 无证据却乱答(should_have_refused)
    citation_error          -- 有证据但引用了错误 chunk
    evaluation_label_error  -- oracle 也拒答但 gold 标注为 answerable → 标签可能有误
    correct                 -- 无错误

对外接口:
- classify_errors(records, questions, experiment_type) -> list[dict]
- compute_error_distribution(error_records) -> dict
- per_question_type_errors(error_records) -> dict
- write_error_report(error_records, experiment_name, output_path) -> str
"""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from typing import Any


# ---------------------------------------------------------------------------
# Error taxonomy constants
# ---------------------------------------------------------------------------

RETRIEVAL_ERROR_MAP: dict[str, str] = {
    "dense": "dense_retrieval_error",
    "bm25": "bm25_error",
    "hybrid": "fusion_error",
    "hybrid_rerank": "reranking_error",
    "retrieval_only": "dense_retrieval_error",
}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _get_retrieved_list(record: dict) -> list[dict]:
    """Extract the retrieved-hits list, handling real-wrapped and flat formats."""
    if "real" in record:
        return record["real"].get("retrieved", [])
    return record.get("retrieved", [])


def _gold_chunk_in_top_k(retrieved: list[dict], gold_ids: set[str]) -> bool:
    """Check whether any gold chunk_id appears in the retrieved list."""
    if not gold_ids:
        return False
    retrieved_ids = {h.get("chunk_id", "") for h in retrieved}
    return bool(retrieved_ids & gold_ids)


def _gold_paper_in_retrieved(retrieved: list[dict], gold_paper: str) -> bool:
    """Check whether any retrieved chunk belongs to the gold paper."""
    if not gold_paper:
        return False
    return any(h.get("paper_id", "") == gold_paper for h in retrieved)


def _classify_retrieval_error(
    experiment_type: str,
    gold_ids: set[str],
    retrieved: list[dict],
    rerank_info: dict | None,
    paper_hit: bool,
) -> tuple[str, str]:
    """Return (error_type, error_detail) for a retrieval failure.

    Distinguishes between experiment types and uses rerank diagnostics
    when available (E4 hybrid_rerank).
    """
    if experiment_type == "dense":
        return "dense_retrieval_error", "gold_not_in_top_k"

    if experiment_type == "bm25":
        return "bm25_error", "gold_not_in_top_k"

    if experiment_type == "hybrid":
        if paper_hit:
            return "fusion_error", "paper_retrieved_but_rrf_pushed_out"
        return "dense_retrieval_error", "neither_dense_nor_bm25_found"

    if experiment_type == "hybrid_rerank":
        # Distinguish: was the gold chunk in coarse retrieval?
        if rerank_info:
            coarse_ids = set(rerank_info.get("coarse_retrieved", []))
            coarse_gold = bool(coarse_ids & gold_ids) if gold_ids else False
            if coarse_gold:
                return "reranking_error", "gold_in_coarse_but_reranker_pushed_out"
        # Gold paper found in coarse but specific chunk missed
        if paper_hit:
            return "reranking_error", "paper_in_coarse_but_rrf_pushed_out"
        return "fusion_error", "gold_not_in_coarse_top_k"

    # Default (retrieval_only or unknown)
    if experiment_type == "retrieval_only":
        # E5: records lack paper_id, paper_hit is always False.
        # Failure in a chunk ablation means the chunking strategy was wrong.
        return "chunking_error", "gold_chunk_not_in_top_k"
    # For generation experiments without paper_id in retrieved hits,
    # paper_hit is always False — don't misclassify as source_missing.
    # Only call source_missing if records actually have paper_id.
    has_paper_id_in_hits = any("paper_id" in h for h in retrieved)
    if has_paper_id_in_hits and not paper_hit and gold_ids:
        return "source_missing", "gold_paper_not_in_any_retrieved_chunk"
    return "dense_retrieval_error", "gold_not_in_top_k"


# ---------------------------------------------------------------------------
# Core classifier
# ---------------------------------------------------------------------------

def classify_errors(
    per_question_records: list[dict],
    questions: list[dict],
    experiment_type: str,
) -> list[dict]:
    """Classify errors for each question in an experiment.

    Parameters
    ----------
    per_question_records:
        Per-question output from one experiment (per_question.jsonl lines).
    questions:
        Gold question definitions (questions.jsonl lines), each with at least
        ``id``, ``type``, ``answerable``, ``relevant_chunk_ids``.
    experiment_type:
        One of ``"dense"``, ``"bm25"``, ``"hybrid"``, ``"hybrid_rerank"``,
        ``"retrieval_only"``.

    Returns
    -------
    list[dict]
        Per-question error classification dicts with keys:
        ``id``, ``type``, ``answerable``, ``error_type``, ``error_detail``,
        ``gold_retrieved`` (bool -- gold paper found in retrieved),
        ``gold_chunk_in_top_k`` (bool -- exact gold chunk_id in retrieved),
        ``refusal_class``, ``oracle_refusal_class``,
        ``relevant_chunks`` (list), ``retrieved_chunks`` (list).
    """
    q_map: dict[str, dict] = {q["id"]: q for q in questions}
    is_retrieval_only = experiment_type == "retrieval_only"
    results: list[dict] = []

    for rec in per_question_records:
        qid = rec.get("id", "")
        gold = q_map.get(qid, {})

        # --- Gold question metadata ---
        answerable = gold.get("answerable", rec.get("answerable", True))
        qtype = gold.get("type", rec.get("type", "unknown"))
        gold_paper: str = gold.get("paper_id", "")
        gold_section: str = gold.get("section", "")
        gold_ids: set[str] = set(gold.get("relevant_chunk_ids") or [])

        # --- Extract record fields (handles real-wrapped and flat formats) ---
        real = rec.get("real") or {}
        oracle = rec.get("oracle") or None
        retrieved = _get_retrieved_list(rec)

        if not is_retrieval_only:
            refused: bool | None = real.get("refused") if real else rec.get("refused")
            citation_correct: bool | None = real.get("citation_correct") if real else None
            refusal_class: str | None = real.get("refusal_class") if real else rec.get("refusal_class")
        else:
            # retrieval_only: top-level fields, no citation analysis
            refused = rec.get("refused")
            citation_correct = None
            refusal_class = rec.get("refusal_class")

        # --- Oracle diagnostics ---
        oracle_refusal_class: str | None = None
        oracle_cc: bool | None = None
        if oracle:
            oracle_refusal_class = oracle.get("refusal_class")
            oracle_cc = oracle.get("citation_correct")

        # --- Rerank info (E4 only) ---
        rerank_info: dict | None = rec.get("rerank")

        # --- Retrieval-level checks ---
        gold_chunk_hit = _gold_chunk_in_top_k(retrieved, gold_ids)
        paper_hit = _gold_paper_in_retrieved(retrieved, gold_paper)

        # ==================================================================
        # Classification logic
        # ==================================================================
        error_type = "correct"
        error_detail = ""

        # -- Unanswerable questions --
        if not answerable:
            if refused is True:
                # true_refusal: correct
                error_type = "correct"
                error_detail = "true_refusal"
            elif refused is False:
                # should_have_refused: answered when shouldn't
                error_type = "generation_error"
                error_detail = "should_have_refused"
            else:
                # retrieval_only or missing data: no generation to evaluate
                error_type = "correct"
                error_detail = "retrieval_only_unanswerable"

        # -- Answerable questions --
        else:
            # evaluation_label_error: oracle also refuses for answerable question
            # This can happen regardless of whether gold was retrieved
            if oracle and oracle.get("refused") is True:
                error_type = "evaluation_label_error"
                error_detail = "oracle_also_refused_for_answerable"

            elif refusal_class == "false_refusal":
                # Answerable but model refused → where did it fail?
                if gold_chunk_hit:
                    # Gold was in top-K but model still refused
                    error_type = "generation_error"
                    error_detail = "refused_despite_evidence"

                elif paper_hit and oracle_cc:
                    # Paper found, oracle would cite correctly, but specific
                    # chunk missing → chunking split problem
                    error_type = "chunking_error"
                    error_detail = (
                        "gold_paper_retrieved_but_specific_chunk_missing_"
                        "oracle_cites_correctly"
                    )

                else:
                    # Gold not in top-K → retrieval error
                    error_type, error_detail = _classify_retrieval_error(
                        experiment_type, gold_ids, retrieved,
                        rerank_info, paper_hit,
                    )

            elif refusal_class == "answered_ok":
                if citation_correct is True:
                    # Answered correctly with correct citation
                    error_type = "correct"
                    error_detail = "answered_correctly"

                elif citation_correct is False:
                    if gold_chunk_hit:
                        # Had the gold chunk but cited wrong
                        error_type = "citation_error"
                        error_detail = "gold_retrieved_but_cited_wrong"

                    elif paper_hit and oracle_cc:
                        # Same paper retrieved, oracle would cite correctly,
                        # but specific chunk missing → chunking issue
                        error_type = "chunking_error"
                        error_detail = (
                            "gold_paper_retrieved_cited_wrong_"
                            "oracle_cites_correctly_chunking_split"
                        )

                    elif paper_hit:
                        # Paper retrieved but both model and oracle cite wrong
                        # (or oracle data unavailable) → generation hallucinated
                        error_type = "generation_error"
                        error_detail = "hallucinated_without_evidence"

                    elif not paper_hit and gold_ids:
                        # Gold paper not in results at all → hallucinated citation
                        error_type = "generation_error"
                        error_detail = "hallucinated_citation_paper_missing"

                    else:
                        error_type = "generation_error"
                        error_detail = "cited_wrong"

            elif refusal_class == "should_have_refused":
                # Unanswerable question answered anyway
                error_type = "generation_error"
                error_detail = "should_have_refused"

            else:
                # No generation data (retrieval_only or missing fields)
                if gold_chunk_hit:
                    error_type = "correct"
                    error_detail = "gold_in_retrieved"
                else:
                    error_type, error_detail = _classify_retrieval_error(
                        experiment_type, gold_ids, retrieved,
                        rerank_info, paper_hit,
                    )

        # --- Build output record ---
        results.append({
            "id": qid,
            "type": qtype,
            "answerable": answerable,
            "error_type": error_type,
            "error_detail": error_detail,
            "gold_retrieved": paper_hit,
            "gold_chunk_in_top_k": gold_chunk_hit,
            "refusal_class": refusal_class,
            "oracle_refusal_class": oracle_refusal_class,
            "relevant_chunks": sorted(gold_ids),
            "retrieved_chunks": [h.get("chunk_id", "") for h in retrieved],
        })

    return results


# ---------------------------------------------------------------------------
# Aggregation helpers
# ---------------------------------------------------------------------------

def compute_error_distribution(error_records: list[dict]) -> dict[str, Any]:
    """Aggregate error type counts across all questions.

    Parameters
    ----------
    error_records:
        Output of :func:`classify_errors`.

    Returns
    -------
    dict
        Keys: each error_type string with its count, plus ``total_questions``,
        ``total_errors``, ``error_rate``.
    """
    n = len(error_records)
    err_counts = Counter(r["error_type"] for r in error_records if r["error_type"] != "correct")
    n_errors = sum(err_counts.values())
    return {
        **dict(err_counts),
        "total_questions": n,
        "total_errors": n_errors,
        "error_rate": round(n_errors / n, 4) if n else 0.0,
    }


def per_question_type_errors(error_records: list[dict]) -> dict[str, dict[str, int]]:
    """Error distribution broken down by question type (fact/method/comparison/cross).

    Parameters
    ----------
    error_records:
        Output of :func:`classify_errors`.

    Returns
    -------
    dict
        ``{question_type: {error_type: count, ...}, ...}``
    """
    by_type: dict[str, Counter] = defaultdict(Counter)
    for rec in error_records:
        by_type[rec["type"]][rec["error_type"]] += 1
    return {k: dict(v) for k, v in by_type.items()}


# ---------------------------------------------------------------------------
# Report writer
# ---------------------------------------------------------------------------

def write_error_report(
    error_records: list[dict],
    experiment_name: str,
    output_path: str,
) -> str:
    """Write detailed per-question error analysis to JSON.

    The report contains:
    - ``experiment_name``
    - ``summary``: output of :func:`compute_error_distribution`
    - ``by_question_type``: output of :func:`per_question_type_errors`
    - ``details``: the full per-question ``error_records``

    Parameters
    ----------
    error_records:
        Output of :func:`classify_errors`.
    experiment_name:
        Human-readable experiment label (e.g. ``"E01_dense"``).
    output_path:
        Destination ``.json`` file path.

    Returns
    -------
    str
        The ``output_path`` (for convenience).
    """
    report = {
        "experiment_name": experiment_name,
        "summary": compute_error_distribution(error_records),
        "by_question_type": per_question_type_errors(error_records),
        "details": error_records,
    }
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    return output_path
