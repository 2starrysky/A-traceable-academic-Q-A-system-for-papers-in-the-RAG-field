"""混合检索融合:Reciprocal Rank Fusion(RRF)。

RRF 对每个候选在多个排序列表中的名次取倒数求和,不依赖分数尺度,适合融合 Dense 与
BM25 两类异构分数。k 为平滑常数(标准取 60)。
"""
from __future__ import annotations

from src.retrieval.dense import RetrievalHit


def reciprocal_rank_fusion(ranked_lists: list[list], k: int = 60) -> list[tuple]:
    """对多个 item 排序列表做 RRF,返回按融合分降序的 [(item, score)]。

    ranked_lists: list[list],每个是已排序的 item 列表(越靠前 rank 越小)。
    score = Σ over lists of 1/(rank + k);item 在某个列表里第 r 位 → 贡献 1/(r+k)。
    """
    acc: dict = {}
    for lst in ranked_lists:
        for rank, item in enumerate(lst, 1):
            acc[item] = acc.get(item, 0.0) + 1.0 / (rank + k)
    ordered = sorted(acc.items(), key=lambda kv: kv[1], reverse=True)
    return ordered


def merge_hits(dense_hits: list[RetrievalHit], bm25_hits: list[RetrievalHit],
               top_k: int = 5, k: int = 60, weights=None) -> list[RetrievalHit]:
    """RRF 融合 Dense 与 BM25 命中,按融合分选 top_k,保留原 hit 元数据。

    weights 为兼容配置保留(可选);RRF 标准实现不依赖权重,默认等权。score 覆写为融合分。
    """
    if not dense_hits:
        return bm25_hits[:top_k]
    if not bm25_hits:
        return dense_hits[:top_k]
    dense_item = [h.chunk_id for h in dense_hits]
    bm25_item = [h.chunk_id for h in bm25_hits]
    ordered = reciprocal_rank_fusion([dense_item, bm25_item], k=k)
    score_map = {h.chunk_id: h for h in dense_hits + bm25_hits}
    merged: list[RetrievalHit] = []
    for cid, fuse_score in ordered[:top_k]:
        base = score_map.get(cid)
        if base is not None:
            import dataclasses
            merged.append(dataclasses.replace(base, score=float(fuse_score)))
    return merged
