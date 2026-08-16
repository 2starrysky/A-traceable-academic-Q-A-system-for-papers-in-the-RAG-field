"""检索指标:Hit@K、MRR。

评估集每题的 gold 是相关 chunk_id 集合(可多个,跨章节题);无答案题 gold 为空,
不计入检索指标。输入为 chunk_id 字符串列表。
"""
from __future__ import annotations


def hit_at_k(retrieved_ids, gold_ids, k: int) -> bool:
    """gold 是否出现在 retrieved 前 k 位。gold 为空返回 False(不参与检索指标)。"""
    gold = set(gold_ids)
    if not gold:
        return False
    return bool(gold & set(retrieved_ids[:k]))


def mrr(retrieved_ids, gold_ids) -> float:
    """首个 gold 命中位置的倒数;未命中为 0。gold 为空返回 0。"""
    gold = set(gold_ids)
    for rank, cid in enumerate(retrieved_ids, 1):
        if cid in gold:
            return 1.0 / rank
    return 0.0


def evaluate_retrieval(predictions, golds, ks=(1, 3, 5)) -> dict:
    """批量检索指标汇总。

    predictions/golds 为等长列表(每个 query 的 retrieved ids / gold ids)。
    返回 {hit@{k}, mrr, n_queries, n_answered};无答案题(gold 空)不计入分子与分母。
    """
    n = len(predictions)
    if n == 0:
        return {f"hit@{k}": 0.0 for k in ks} | {"mrr": 0.0, "n_queries": 0, "n_answered": 0}

    hits = {f"hit@{k}": 0.0 for k in ks}
    mrr_sum = 0.0
    answered = 0
    for ret, gold in zip(predictions, golds):
        if not gold:
            continue
        answered += 1
        for k in ks:
            hits[f"hit@{k}"] += float(hit_at_k(ret, gold, k))
        mrr_sum += mrr(ret, gold)

    denom = answered or 1.0
    result = {f"hit@{k}": hits[f"hit@{k}"] / denom for k in ks}
    result["mrr"] = mrr_sum / denom
    result["n_queries"] = n
    result["n_answered"] = answered
    return result
