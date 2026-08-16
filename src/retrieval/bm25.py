"""BM25 稀疏检索(rank_bm25)。与 Dense 共用 RetrievalHit/search 接口。

语料从 chunk 记录构建,用 tiktoken cl100k_base 切词(与 embedding 侧 token 统一);
search(query, top_k) 返回 list[RetrievalHit],可直接被 run_experiment 复用。
"""
from __future__ import annotations

from src.retrieval.dense import RetrievalHit

_META_KEYS = (
    "chunk_id", "paper_id", "title", "section", "sections", "page_start",
    "page_end", "text", "source", "chunking", "token_count",
)


def _tokenize(text: str):
    import tiktoken
    enc = tiktoken.get_encoding("cl100k_base")
    return enc.encode(text)


class BM25Retriever:
    def __init__(self, bm25, metas: list[dict], tokenizer=None):
        self._bm25 = bm25
        self._metas = metas  # 与语料顺序一致
        self._tokenize = tokenizer or _tokenize

    @classmethod
    def from_chunks(cls, chunks: list[dict]) -> "BM25Retriever":
        from rank_bm25 import BM25Okapi
        corpus = [_tokenize(c["text"]) for c in chunks]
        bm25 = BM25Okapi(corpus)
        metas = [{k: c.get(k) for k in _META_KEYS} for c in chunks]
        return cls(bm25, metas)

    def search(self, query: str, top_k: int = 5) -> list[RetrievalHit]:
        if not self._metas:
            return []
        q_tok = self._tokenize(query)
        scores = self._bm25.get_scores(q_tok)
        # 按 BM25 分数降序取 top_k
        order = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
        hits: list[RetrievalHit] = []
        for i in order:
            m = self._metas[i]
            hits.append(RetrievalHit(
                score=float(scores[i]), chunk_id=m["chunk_id"], paper_id=m["paper_id"],
                title=m["title"], section=m["section"], sections=tuple(m["sections"] or []),
                page_start=m["page_start"], page_end=m["page_end"], text=m["text"],
                source=m["source"], chunking=m["chunking"], token_count=m["token_count"],
            ))
        return hits
