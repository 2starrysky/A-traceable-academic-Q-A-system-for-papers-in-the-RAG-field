"""bm25 / fusion 测试:BM25 词面检索、RetrievalHit 还原、RRF 融合排序、merge top_k。

用确定性 tokenizer(小写 split)注入,不依赖 tiktoken 词表;快、无网络。
"""
from __future__ import annotations

from src.retrieval.bm25 import BM25Retriever
from src.retrieval.dense import RetrievalHit
from src.retrieval.fusion import merge_hits, reciprocal_rank_fusion


def _tok(text: str):
    return text.lower().split()


def mk_chunk(cid, text, paper_id="p1", section="2 Methods"):
    return {
        "chunk_id": cid, "paper_id": paper_id, "title": "Paper", "section": section,
        "sections": [section], "page_start": 3, "page_end": 3, "text": text,
        "source": "x", "chunking": "fixed", "token_count": len(_tok(text)),
    }


def test_bm25_lexical_match_ranks_highest():
    chunks = [
        mk_chunk("c1", "retrieval augmented generation for knowledge intensive nlp"),
        mk_chunk("c2", "baking a chocolate cake recipe"),
        mk_chunk("c3", "dense passage retrieval with vector similarity"),
    ]
    retriever = BM25Retriever.from_chunks(chunks)
    retriever._tokenize = _tok
    hits = retriever.search("retrieval augmented generation", top_k=3)
    assert hits[0].chunk_id == "c1"  # 词面重合最多
    # 命中返回 RetrievalHit 且字段完整
    h = hits[0]
    assert h.paper_id == "p1" and h.section == "2 Methods" and h.source == "x"


def test_bm25_topk_capped():
    chunks = [mk_chunk(f"c{i}", f"common prefix keyword {i}") for i in range(10)]
    retriever = BM25Retriever.from_chunks(chunks)
    retriever._tokenize = _tok
    assert len(retriever.search("common prefix keyword", top_k=5)) == 5


def test_bm25_miss_returns_something_sorted():
    chunks = [mk_chunk("c1", "the quick brown fox"), mk_chunk("c2", "jumps over lazy dog")]
    retriever = BM25Retriever.from_chunks(chunks)
    retriever._tokenize = _tok
    hits = retriever.search("completely unrelated query", top_k=2)
    assert len(hits) == 2
    scores = [h.score for h in hits]
    assert scores == sorted(scores, reverse=True)


def test_rrf_ranks_common_item_highest():
    a = ["x", "y", "z"]
    b = ["y", "x", "w"]
    ordered = reciprocal_rank_fusion([a, b])
    items = [it for it, _ in ordered]
    # 'x' 名次 1+2=3,'y' 名次 2+1=3,都靠前;但 x 第1实际更高
    assert items.index("x") < items.index("z")
    assert _score(ordered, "x") > _score(ordered, "z")


def _score(ordered, item):
    for it, s in ordered:
        if it == item:
            return s
    return 0.0


def test_merge_hits_rrf_preserves_metadata_and_caps():
    dense = [RetrievalHit(0.9, "a", "p1", "T", "s", ("s",), 3, 3, "text a", "src", "fixed", 5),
             RetrievalHit(0.8, "b", "p1", "T", "s", ("s",), 3, 3, "text b", "src", "fixed", 5)]
    bm25 = [RetrievalHit(5.0, "b", "p1", "T", "s", ("s",), 3, 3, "text b", "src", "fixed", 5),
            RetrievalHit(4.0, "c", "p1", "T", "s", ("s",), 3, 3, "text c", "src", "fixed", 5)]
    merged = merge_hits(dense, bm25, top_k=2)
    assert len(merged) == 2
    # b 在两个列表都出现(RRF 最高分),应排第一
    assert merged[0].chunk_id == "b"
    # 元数据保留(paper_id/section)
    assert merged[0].paper_id == "p1" and merged[0].text == "text b"
    # score 被覆写为融合分
    assert merged[0].score > merged[1].score


def test_merge_hits_single_source_fallback():
    only_bm25 = [RetrievalHit(3.0, "c", "p1", "T", "s", ("s",), 3, 3, "x", "src", "fixed", 5)]
    merged = merge_hits([], only_bm25, top_k=5)
    assert [h.chunk_id for h in merged] == ["c"]
