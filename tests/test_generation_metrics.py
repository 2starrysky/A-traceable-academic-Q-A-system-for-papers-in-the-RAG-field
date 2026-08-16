"""生成指标测试:双层引用判定、章节前缀匹配、拒答四分类、指标汇总。确定性用例。"""
from __future__ import annotations

import pytest

from src.evaluation.generation_metrics import (
    citation_correct, classify_refusal, compute_generation_metrics, section_match,
)
from src.retrieval.dense import RetrievalHit


def cit(chunk_id="c1", paper_id="rag_lewis2021", section="2 Methods") -> RetrievalHit:
    return RetrievalHit(
        score=0.9, chunk_id=chunk_id, paper_id=paper_id, title="T", section=section,
        sections=(section,), page_start=3, page_end=3, text="x", source="s",
        chunking="fixed", token_count=5,
    )


def test_section_match_prefix():
    assert section_match("2.4 Training", "2 Methods") is True  # 章节号前缀 2
    assert section_match("5.2 Ablation", "5 Experiments") is True
    assert section_match("2.4 Training", "4 Results") is False
    assert section_match("1 Introduction", "1 Introduction") is True  # 字符串相等


def test_section_match_roman():
    assert section_match("II. OVERVIEW", "II Overview") is True  # 罗马数字前缀
    assert section_match("I Introduction", "II Overview") is False


def test_section_match_no_number_falls_back_to_exact():
    assert section_match("References", "References") is True
    assert section_match("References", "Acknowledgements") is False


def test_citation_correct_exact_chunk_match():
    # 引用精确命中标注相关 chunk → 必然论文+章节对
    c = cit(chunk_id="gold1", paper_id="rag_lewis2021", section="2 Methods")
    assert citation_correct(c, "rag_lewis2021", ["gold1"], ["2 Methods"]) is True


def test_citation_correct_paper_and_section_prefix():
    c = cit(chunk_id="c9", paper_id="rag_lewis2021", section="2.4 Training")
    assert citation_correct(c, "rag_lewis2021", ["gold1"], ["2 Methods"]) is True


def test_citation_correct_wrong_section():
    c = cit(chunk_id="c9", paper_id="rag_lewis2021", section="4 Results")
    assert citation_correct(c, "rag_lewis2021", ["gold1"], ["2 Methods"]) is False


def test_citation_correct_wrong_paper():
    c = cit(chunk_id="c9", paper_id="dpr", section="2 Methods")
    assert citation_correct(c, "rag_lewis2021", ["gold1"], ["2 Methods"]) is False


def test_classify_refusal_four_ways():
    assert classify_refusal(True, False) == "true_refusal"    # 无答案+拒答=正确
    assert classify_refusal(True, True) == "false_refusal"    # 有答案+拒答=检索失败
    assert classify_refusal(False, True) == "answered_ok"     # 有答案+作答
    assert classify_refusal(False, False) == "should_have_refused"  # 无答案但作答=错误


def test_compute_generation_metrics():
    records = [
        # 3 个可答题:1 作答+引用正确,1 作答+引用错误,1 误拒答
        {"answerable": True, "refused": False, "citation_correct": True, "latency": 1.0},
        {"answerable": True, "refused": False, "citation_correct": False, "latency": 2.0},
        {"answerable": True, "refused": True, "citation_correct": False, "latency": 0.5},
        # 2 个无答案题:1 真拒答,1 应拒未拒
        {"answerable": False, "refused": True, "latency": 0.5},
        {"answerable": False, "refused": False, "latency": 0.5},
    ]
    m = compute_generation_metrics(records)
    assert m["n_answerable"] == 3 and m["n_unanswerable"] == 2
    # 引用正确率分母=作答的 2 题,分子=1
    assert m["citation_accuracy"] == 0.5
    assert m["true_refusal_rate"] == 0.5
    assert m["false_refusal_rate"] == 1 / 3
    assert m["should_have_refused"] == 1
    assert m["avg_latency"] == pytest.approx(0.9)  # (1+2+0.5+0.5+0.5)/5
