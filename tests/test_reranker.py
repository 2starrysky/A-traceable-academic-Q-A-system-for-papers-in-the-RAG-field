"""重排器测试:CrossEncoder 精排 + top_k 截断 + 元数据保留。

用确定性伪打分函数注入,不依赖模型下载/网络。
"""
from __future__ import annotations

import pytest

from src.retrieval.dense import RetrievalHit
from src.retrieval.reranker import Reranker, rerank_hits


def _mk(cid, text, score=0.0, **kw):
    return RetrievalHit(
        score=score, chunk_id=cid, paper_id=kw.get("paper_id", "p1"),
        title=kw.get("title", "T"), section=kw.get("section", "2 Methods"),
        sections=(kw.get("section", "2 Methods"),),
        page_start=kw.get("page_start", 3), page_end=kw.get("page_end", 3),
        text=text, source=kw.get("source", "x"),
        chunking="fixed", token_count=kw.get("token_count", 5),
    )


def test_rerank_orders_by_relevance_and_caps():
    """重排器按相关性分降序、保留 top_k;score 被覆写。"""
    # 伪打分:问题词出现在文本里 → 分高
    def fake(pairs):
        def s(q, t):
            return float(q.lower().split()[0] in t.lower())
        return [s(q, t) for (q, t) in pairs]

    hits = [
        _mk("c1", "baking a cake recipe", score=0.9),   # 无关
        _mk("c2", "retrieval augmented generation", score=0.5),  # 相关
    ]
    r = Reranker(fake)
    out = r.rerank("retrieval is key", hits, top_k=1)
    assert len(out) == 1
    assert out[0].chunk_id == "c2"
    assert out[0].score == pytest.approx(1.0)  # score 被覆写为重打分


def test_rerank_preserves_metadata():
    def fake(pairs):
        return [0.7] * len(pairs)

    src = _mk("c9", "some text", score=0.0, paper_id="my_paper", title="MyTitle",
              section="5 Experiments", source="src_url", token_count=42)
    r = Reranker(fake)
    out = r.rerank("any query", [src], top_k=1)
    h = out[0]
    assert h.chunk_id == "c9" and h.paper_id == "my_paper" and h.title == "MyTitle"
    assert h.section == "5 Experiments" and h.source == "src_url" and h.token_count == 42
    assert h.page_start == 3 and h.page_end == 3 and h.text == "some text"
    assert h.chunking == "fixed"


def test_rerank_empty_and_full_order():
    def fake(pairs):
        return [0.1, 0.9, 0.5, 0.7, 0.3]

    hits = [_mk(f"c{i}", f"t{i}", score=i) for i in range(5)]
    r = Reranker(fake)
    assert r.rerank("q", [], top_k=5) == []
    ordered = r.rerank("q", hits, top_k=5)
    assert len(ordered) == 5
    # 按伪分 0.1/0.9/0.5/0.7/0.3 → 降序:0.9(c1) 0.7(c3) 0.5(c2) 0.3(c4) 0.1(c0)
    assert [h.chunk_id for h in ordered] == ["c1", "c3", "c2", "c4", "c0"]


def test_rerank_moves_lower_ranked_hit_up():
    """粗排把对的 chunk 排到了后面,重排能把它提到前面——重排器的核心价值。"""
    # 粗排分数:c1 最高(但内容无关),c3 最低(但内容最相关)
    coarse = [
        _mk("c1", "cake recipe dessert", score=0.95),
        _mk("c2", "some unrelated text", score=0.7),
        _mk("c3", "retrieval augmented generation", score=0.4),
    ]
    def fake(pairs):
        def s(q, t):
            return float(q.lower().split()[0] in t.lower())
        return [s(q, t) for (q, t) in pairs]
    r = Reranker(fake)
    out = r.rerank("retrieval works", coarse, top_k=3)
    # 重排后 c3(含 retrieval)应升到最前
    assert out[0].chunk_id == "c3"
    # 原粗排第一 c1 应被降到后面
    assert [h.chunk_id for h in out].index("c1") > 0


def test_module_rerank_hits_convenience():
    def fake(pairs):
        return [0.5, 0.8]
    hits = [_mk("c1", "a"), _mk("c2", "b")]
    r = Reranker(fake)
    out = rerank_hits("q", hits, r, top_k=2)
    assert out[0].chunk_id == "c2"