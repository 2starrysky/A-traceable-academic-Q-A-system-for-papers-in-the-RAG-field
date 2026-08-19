"""重排器:用 CrossEncoder(bge-reranker)对粗排候选集做精排。

粗排(Dense/BM25 的 RRF 融合)快但粗糙——它只按单向量相似度打分,没看"问题和段落的整体
对应关系"。重排器把"问题 + 每个候选段落"当成一个**配对**喂给一个更强的模型,得到更
细粒度的相关性分数,再重新排序、只留 top_k 个。

比喻:粗排像图书馆管理员"快速扫标题挑书"(快但可能挑错),重排像"把书翻开仔细读内
容、再挑最贴切的那本"(慢但准)。两者配合 = 召回(粗) + 排序(精)。

encode_fn 可注入(测试用伪打分,生产用 sentence-transformers 的 CrossEncoder)。
分数是相对值(越高越相关),不是 0~1 的概率。
"""
from __future__ import annotations

from pathlib import Path

import dataclasses

from src.retrieval.dense import RetrievalHit


_META_KEYS = (
    "chunk_id", "paper_id", "title", "section", "sections", "page_start",
    "page_end", "text", "source", "chunking", "token_count",
)


def _prepare_model(model_name: str) -> str:
    """返回实际加载的模型路径/名称。

    若 model_name 本身或本机 data/models/<短名>/ 已是本地模型目录(含 config.json),
    则强制 local_files_only 走本地加载,避免镜像站/网络问题导致下载失败;否则原样返回
    (走 HuggingFace 下载)。与 dense.py 的离线加载策略一致。
    """
    p = Path(model_name)
    if (p / "config.json").exists():
        return str(p.resolve())
    cand = Path("data") / "models" / p.name
    if (cand / "config.json").exists():
        return str(cand.resolve())
    return model_name


class Reranker:
    """封装一个重打分函数 + max_seq_length;生产用 CrossEncoder,测试注入伪函数。

    rerank(query, hits, top_k) 对每个 (query, hit.text) 配对打分,按分数降序取 top_k,
    返回新的 list[RetrievalHit](score 被覆写为重打分,其余元数据原样保留)。
    """

    def __init__(self, predict_fn, max_seq_length: int = 512):
        """predict_fn(pairs: list[tuple[str,str]]) -> list[float],每对一个相关性分。"""
        self._predict = predict_fn
        self.max_seq_length = int(max_seq_length)

    @classmethod
    def from_model_name(cls, model_name: str = "BAAI/bge-reranker-v2-m3",
                        local_files_only: bool = False) -> "Reranker":
        """加载 CrossEncoder 模型构造重排器。local_files_only=True 时仅从本地读取。"""
        from sentence_transformers import CrossEncoder
        mpath = _prepare_model(model_name)
        model = CrossEncoder(mpath, max_length=512, local_files_only=local_files_only)
        return cls(
            lambda pairs: model.predict(pairs, show_progress_bar=False).tolist(),
            max_seq_length=int(model.max_length) if hasattr(model, "max_length") else 512,
        )

    def _score_all(self, query: str, hits: list[RetrievalHit]) -> list[float]:
        if not hits:
            return []
        pairs = [(query, h.text) for h in hits]
        scores = self._predict(pairs)
        return [float(s) for s in scores]

    def rerank(self, query: str, hits: list[RetrievalHit], top_k: int = 5) -> list[RetrievalHit]:
        """对候选集 (query, hits) 重打分并返回按重打分降序的 top_k。

        score 被覆写为重打分(浮点);其余元数据原样保留。空候选返回空列表。
        """
        if not hits:
            return []
        scores = self._score_all(query, hits)
        combined = sorted(zip(hits, scores), key=lambda p: p[1], reverse=True)
        out: list[RetrievalHit] = []
        for hit, s in combined[:top_k]:
            out.append(dataclasses.replace(hit, score=s))
        return out


def rerank_hits(query: str, hits: list[RetrievalHit], reranker: Reranker,
                top_k: int = 5) -> list[RetrievalHit]:
    """模块级便利函数:对候选集重打分取 top_k。"""
    return reranker.rerank(query, hits, top_k=top_k)