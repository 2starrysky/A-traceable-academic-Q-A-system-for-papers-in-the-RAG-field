"""dense retriever 模块测试:索引构建、Top-K 检索、相似度排序、保存/加载、维度校验与真实 chunk schema。

用确定性伪编码(crc32 词袋 + 归一化)注入,不依赖网络/模型下载。
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from src.retrieval.dense import DenseRetriever, build_index, load_index, save_index, search_index

ROOT = Path(__file__).resolve().parents[1]
CHUNKS = ROOT / "data" / "processed" / "chunks_fixed.jsonl"

DIM = 8


def fake_encode(texts: list[str], batch_size: int = 32) -> np.ndarray:
    """确定性词袋伪向量:词 → crc32 取模落到 DIM 维,归一化后内积可作相似度。"""
    def vec(text: str) -> np.ndarray:
        v = np.zeros(DIM, dtype="float32")
        for tok in text.lower().split():
            v[zlib_crc32(tok) % DIM] += 1.0
        n = np.linalg.norm(v)
        return v / n if n > 0 else v

    return np.array([vec(t) for t in texts])


def zlib_crc32(tok: str) -> int:
    import zlib
    return zlib.crc32(tok.encode("utf-8"))


def mk_record(chunk_id="c1", paper_id="p1", title="Paper One", section="3 Method",
              sections=("3 Method",), page_start=2, page_end=3, text="retrieval augmented generation",
              source="https://arxiv.org/abs/1", chunking="fixed", token_count=5) -> dict:
    return {
        "chunk_id": chunk_id, "paper_id": paper_id, "title": title, "section": section,
        "sections": list(sections), "page_start": page_start, "page_end": page_end,
        "text": text, "source": source, "chunking": chunking, "token_count": token_count,
    }


def test_build_index_schema_and_meta_alignment():
    records = [mk_record(chunk_id="c1", text="retrieval augmented generation"),
               mk_record(chunk_id="c2", text="dense passage retrieval"),
               mk_record(chunk_id="c3", text="query encoder model")]
    index, metas = build_index(records, fake_encode, DIM)
    assert index.ntotal == 3
    assert len(metas) == 3
    assert [m["chunk_id"] for m in metas] == ["c1", "c2", "c3"]
    assert metas[0]["title"] == "Paper One" and metas[0]["section"] == "3 Method"
    assert metas[0]["page_start"] == 2 and metas[0]["page_end"] == 3
    assert metas[0]["source"] == "https://arxiv.org/abs/1"
    assert metas[0]["token_count"] == 5


def test_search_returns_topk_sorted_desc():
    records = [
        mk_record(chunk_id="c1", text="retrieval augmented generation for knowledge"),
        mk_record(chunk_id="c2", text="dense passage retrieval with vectors"),
        mk_record(chunk_id="c3", text="how to bake a cake"),
    ]
    index, metas = build_index(records, fake_encode, DIM)
    qv = fake_encode(["retrieval augmented generation"])[0]
    hits = search_index(index, metas, qv, top_k=3)
    assert len(hits) == 3
    assert hits[0].chunk_id == "c1"
    scores = [h.score for h in hits]
    assert scores == sorted(scores, reverse=True)


def test_topk_capped_and_clamped():
    records = [mk_record(chunk_id=f"c{i}", text=f"common prefix topic {i}") for i in range(10)]
    index, metas = build_index(records, fake_encode, DIM)
    qv = fake_encode(["topic 1"])[0]
    assert len(search_index(index, metas, qv, top_k=5)) == 5
    # top_k 超过总量 → 返回全部
    assert len(search_index(index, metas, qv, top_k=99)) == 10


def test_hit_carries_full_traceable_metadata():
    records = [mk_record(chunk_id="c1", paper_id="p1", title="T",
                         section="4 Experiments", page_start=7, page_end=7,
                         text="dense retrieval works", source="src") ]
    index, metas = build_index(records, fake_encode, DIM)
    qv = fake_encode(["dense retrieval works"])[0]
    hit = search_index(index, metas, qv, top_k=1)[0]
    assert hit.paper_id == "p1" and hit.title == "T"
    assert hit.section == "4 Experiments"
    assert hit.page_start == 7 and hit.page_end == 7
    assert hit.source == "src"
    assert hit.chunking == "fixed"
    assert hit.token_count == 5
    assert hit.text == "dense retrieval works"


def test_exact_match_score_near_one():
    text = "retrieval augmented generation for knowledge intensive nlp"
    records = [mk_record(chunk_id="c1", text=text),
               mk_record(chunk_id="c2", text="unrelated cake recipe")]
    index, metas = build_index(records, fake_encode, DIM)
    qv = fake_encode([text])[0]
    hits = search_index(index, metas, qv, top_k=2)
    assert hits[0].chunk_id == "c1"
    assert hits[0].score == pytest.approx(1.0, abs=1e-5)


def test_dim_mismatch_raises():
    records = [mk_record(text="whatever")]
    with pytest.raises(ValueError):
        build_index(records, fake_encode, DIM + 3)


def test_empty_records_raises():
    with pytest.raises(ValueError):
        build_index([], fake_encode, DIM)


def test_save_load_roundtrip(tmp_path):
    records = [mk_record(chunk_id="c1", text="dense passage retrieval"),
               mk_record(chunk_id="c2", text="late interaction model")]
    index, metas = build_index(records, fake_encode, DIM)
    config = {"embedding_model": "fake", "dim": DIM, "n_chunks": 2}
    save_index(index, metas, tmp_path / "idx", config=config)

    index2, metas2, config2 = load_index(tmp_path / "idx")
    assert index2.ntotal == 2
    assert index2.d == DIM
    assert metas2 == metas
    assert config2["dim"] == DIM and config2["embedding_model"] == "fake"

    qv = fake_encode(["dense passage retrieval"])[0]
    hits = search_index(index2, metas2, qv, top_k=2)
    assert hits[0].chunk_id == "c1"


def test_dense_retriever_class_roundtrip(tmp_path):
    records = [mk_record(chunk_id="c1", text="dense passage retrieval"),
               mk_record(chunk_id="c2", text="baking a cake")]
    r = DenseRetriever(fake_encode, DIM)
    r.build_index(records, batch_size=2, config={"embedding_model": "fake"})
    hits = r.search("dense passage retrieval", top_k=1)
    assert hits[0].chunk_id == "c1"

    r.save(tmp_path / "idx")
    r2 = DenseRetriever.load(tmp_path / "idx", encode_fn=fake_encode, dim=DIM)
    hits2 = r2.search("dense passage retrieval", top_k=1)
    assert hits2[0].chunk_id == "c1"
    assert r2.config["embedding_model"] == "fake"


def test_real_chunks_schema_offline():
    """在真实语料上用伪编码构建索引,校验命中记录字段与 Day 7 chunk schema 对齐。"""
    records = []
    with open(CHUNKS, encoding="utf-8") as fh:
        for line in fh:
            records.append(json.loads(line))
            if len(records) >= 20:
                break
    assert records
    index, metas = build_index(records, fake_encode, DIM)
    qv = fake_encode([records[0]["text"]])[0]
    hits = search_index(index, metas, qv, top_k=3)
    keys = {"score", "chunk_id", "paper_id", "title", "section", "sections",
            "page_start", "page_end", "text", "source", "chunking", "token_count"}
    for h in hits:
        assert set(h.as_dict()) == keys
        assert h.text.strip()
        assert h.page_start <= h.page_end
    ids = [h.chunk_id for h in hits]
    assert len(ids) == len(set(ids))
