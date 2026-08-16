"""稠密向量检索:embedding(bge-m3)+ FAISS 精确内积索引,含构建/保存/加载/Top-K 检索。

设计:编码函数可注入(生产用 sentence-transformers 的 bge-m3,测试用伪编码);索引与元数据
分开保存(FAISS 不存 chunk 元数据):index.faiss 存向量,meta.jsonl 存与向量顺序一致的
chunk 完整记录,config.json 记复现所需参数。向量归一化后用内积(IndexFlatIP)等价余弦相似度。
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np


@dataclass(frozen=True)
class RetrievalHit:
    """一次检索命中:chunk 全量元数据 + 相似度分数(可溯源定位信息齐备)。"""
    score: float
    chunk_id: str
    paper_id: str
    title: str
    section: str
    sections: tuple[str, ...]
    page_start: int
    page_end: int
    text: str
    source: str
    chunking: str
    token_count: int

    def as_dict(self) -> dict:
        d = {
            "score": self.score,
            "chunk_id": self.chunk_id,
            "paper_id": self.paper_id,
            "title": self.title,
            "section": self.section,
            "sections": list(self.sections),
            "page_start": self.page_start,
            "page_end": self.page_end,
            "text": self.text,
            "source": self.source,
            "chunking": self.chunking,
            "token_count": self.token_count,
        }
        return d


_META_KEYS = (
    "chunk_id", "paper_id", "title", "section", "sections",
    "page_start", "page_end", "text", "source", "chunking", "token_count",
)


def _as_hit(meta: dict, score: float) -> RetrievalHit:
    m = {k: meta.get(k) for k in _META_KEYS}
    m["sections"] = tuple(m.get("sections") or [])
    return RetrievalHit(score=score, **m)


def _records_from_jsonl(path: str | Path) -> list[dict]:
    """读 chunk JSONL(每行一个 chunk 记录),返回 dict 列表。"""
    records: list[dict] = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def build_index(records: list[dict], encode_fn, dim: int, batch_size: int = 32):
    """批量编码 chunk 文本并构建 FAISS 索引。

    encode_fn(texts, batch_size) -> 形状 (n, dim) 的 float32 向量矩阵(已归一化)。
    返回 (index, metas):metas 与向量行序一一对应。
    """
    if not records:
        raise ValueError("没有可索引的 chunk 记录")
    texts = [r["text"] for r in records]
    vecs = np.asarray(encode_fn(texts, batch_size=batch_size), dtype="float32")
    if vecs.ndim == 1:
        vecs = vecs.reshape(1, -1)
    if vecs.shape[1] != dim:
        raise ValueError(f"编码维度 {vecs.shape[1]} != 预期 {dim}")
    import faiss
    index = faiss.IndexFlatIP(dim)
    index.add(vecs)
    metas = [{k: r[k] for k in _META_KEYS if k in r} for r in records]
    return index, metas


def save_index(index, metas: list[dict], path: str | Path, config: dict | None = None) -> None:
    """把 FAISS 索引 + 元数据 + 配置写到目录 path 下。

    用 serialize_index 走 Python 文件 IO 而非 faiss C 层 fopen,避免 Windows 中文路径打不开。
    """
    import faiss
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    (path / "index.faiss").write_bytes(faiss.serialize_index(index))
    with open(path / "meta.jsonl", "w", encoding="utf-8") as fh:
        for m in metas:
            fh.write(json.dumps(m, ensure_ascii=False) + "\n")
    if config:
        with open(path / "config.json", "w", encoding="utf-8") as fh:
            json.dump(config, fh, ensure_ascii=False, indent=2)


def load_index(path: str | Path):
    """从目录加载 (index, metas, config)。config 不存在时返回 {}(向后兼容)。"""
    import faiss
    path = Path(path)
    raw = (path / "index.faiss").read_bytes()
    index = faiss.deserialize_index(np.frombuffer(raw, dtype="uint8"))
    metas: list[dict] = []
    with open(path / "meta.jsonl", encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                metas.append(json.loads(line))
    config: dict = {}
    cfg = path / "config.json"
    if cfg.exists():
        with open(cfg, encoding="utf-8") as fh:
            config = json.load(fh)
    return index, metas, config


def search_index(index, metas: list[dict], query_vec, top_k: int = 5) -> list[RetrievalHit]:
    """对归一化 query 向量做 Top-K 内积检索,返回按相似度降序的命中列表。"""
    if not metas:
        return []
    qv = np.asarray(query_vec, dtype="float32").reshape(1, -1)
    k = min(top_k, len(metas))
    scores, idxs = index.search(qv, k)
    hits: list[RetrievalHit] = []
    for score, i in zip(scores[0], idxs[0]):
        if i < 0:
            continue
        hits.append(_as_hit(metas[i], float(score)))
    return hits


def _prepare_model(model_name: str) -> str:
    """返回实际加载的模型路径/名称。

    若 model_name 本身或本机 data/models/<短名>/ 已是本地模型目录(含 config.json),
    则切到本地目录并强制离线加载,避免 huggingface_hub 对镜像站的域名校验导致下载失败。
    否则原样返回(走 HuggingFace 下载)。
    """
    import os
    p = Path(model_name)
    if (p / "config.json").exists():
        os.environ["HF_HUB_OFFLINE"] = "1"
        return str(p.resolve())
    cand = Path("data") / "models" / p.name
    if (cand / "config.json").exists():
        os.environ["HF_HUB_OFFLINE"] = "1"
        return str(cand.resolve())
    return model_name


class DenseRetriever:
    """封装编码函数 + FAISS 索引 + 元数据;encode_fn 可注入以便离线测试。

    生产用法:DenseRetriever.from_model_name("BAAI/bge-m3")。索引路径保存后,
    load() 若未传 encode_fn,会从 config.json 读回模型名重新加载编码模型。
    """

    def __init__(self, encode_fn, dim: int):
        self._encode = encode_fn
        self.dim = dim
        self.index = None
        self.metas: list[dict] = []
        self.config: dict = {}

    @classmethod
    def from_model_name(cls, model_name: str = "BAAI/bge-m3", device: str | None = None) -> "DenseRetriever":
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer(_prepare_model(model_name), device=device)
        dim = int(model.get_embedding_dimension())

        def encode_fn(texts: list[str], batch_size: int = 32) -> np.ndarray:
            return model.encode(texts, batch_size=batch_size,
                                normalize_embeddings=True, show_progress_bar=False)

        obj = cls(encode_fn, dim)
        obj.config["embedding_model"] = model_name
        return obj

    @classmethod
    def load(cls, path: str | Path, encode_fn=None, dim: int | None = None,
             device: str | None = None) -> "DenseRetriever":
        """加载索引目录;未注入 encode_fn 时按 config.embedding_model 重建编码模型。"""
        index, metas, config = load_index(path)
        if encode_fn is None:
            model_name = config.get("embedding_model", "BAAI/bge-m3")
            obj = cls.from_model_name(model_name, device=device)
        else:
            obj = cls(encode_fn, dim or int(index.d))
        obj.config = config
        obj.index = index
        obj.metas = metas
        return obj

    def build_index(self, records: list[dict], batch_size: int = 32, config: dict | None = None) -> None:
        self.index, self.metas = build_index(records, self._encode, self.dim, batch_size=batch_size)
        if config:
            self.config.update(config)

    def encode_query(self, query: str) -> np.ndarray:
        return np.asarray(self._encode([query], batch_size=1)[0], dtype="float32")

    def search(self, query: str, top_k: int = 5) -> list[RetrievalHit]:
        qv = self.encode_query(query)
        return search_index(self.index, self.metas, qv, top_k)

    def save(self, path: str | Path) -> None:
        if self.index is None:
            raise RuntimeError("尚无索引,先 build_index 再 save")
        save_index(self.index, self.metas, path, config=self.config)
