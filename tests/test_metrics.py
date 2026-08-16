"""检索指标测试:Hit@K、MRR、批量汇总。确定性用例,不依赖真实检索。"""
from __future__ import annotations

from src.evaluation.retrieval_metrics import evaluate_retrieval, hit_at_k, mrr


def test_hit_at_k_true_first():
    assert hit_at_k(["c1", "c2", "c3"], ["c1"], 1) is True
    assert hit_at_k(["c1", "c2", "c3"], ["c1"], 3) is True


def test_hit_at_k_gold_late():
    assert hit_at_k(["c1", "c2", "c3"], ["c3"], 1) is False
    assert hit_at_k(["c1", "c2", "c3"], ["c3"], 3) is True


def test_hit_at_k_miss():
    assert hit_at_k(["c1", "c2"], ["c9"], 5) is False


def test_hit_at_k_empty_gold():
    assert hit_at_k(["c1", "c2"], [], 5) is False


def test_mrr_first():
    assert mrr(["c1", "c2"], ["c1"]) == 1.0


def test_mrr_second():
    assert mrr(["c1", "c2", "c3"], ["c2"]) == 0.5


def test_mrr_multi_gold_takes_first_hit():
    assert mrr(["c1", "c2", "c3"], ["c3", "c2"]) == 0.5  # 位置 2 的 c2 先命中


def test_mrr_miss_zero():
    assert mrr(["c1", "c2"], ["c9"]) == 0.0


def test_mrr_empty_gold_zero():
    assert mrr(["c1", "c2"], []) == 0.0


def test_evaluate_retrieval_aggregates():
    preds = [["c1", "c2", "c3"], ["x1", "x2", "c3"], ["a1", "b1"]]
    golds = [["c1"], ["c3"], ["z9"]]  # query3 gold 未命中
    r = evaluate_retrieval(preds, golds, ks=(1, 3, 5))
    assert r["n_queries"] == 3
    assert r["n_answered"] == 3
    assert r["hit@1"] == 1 / 3  # 仅 query1 首位命中
    assert r["hit@3"] == 2 / 3  # query1/query2 命中,query3 未命中
    assert r["hit@5"] == 2 / 3
    assert r["mrr"] == (1.0 + 1 / 3 + 0.0) / 3


def test_evaluate_retrieval_skips_unanswerable():
    """gold 空(无答案题)不计入分子与分母。"""
    preds = [["c1", "c2"], ["x1", "x2"]]
    golds = [["c1"], []]  # query2 无答案
    r = evaluate_retrieval(preds, golds, ks=(1, 5))
    assert r["n_answered"] == 1
    assert r["hit@1"] == 1.0
    assert r["mrr"] == 1.0


def test_evaluate_retrieval_empty_input():
    r = evaluate_retrieval([], [], ks=(1, 3, 5))
    assert r["n_queries"] == 0
    assert r["n_answered"] == 0
    assert r["mrr"] == 0.0
    assert r["hit@3"] == 0.0
