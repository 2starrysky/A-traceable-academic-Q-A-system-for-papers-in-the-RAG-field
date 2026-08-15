"""splitter 模块测试:fixed / section_aware 两种切块的窗口、overlap、metadata、section 边界与 schema。"""
from __future__ import annotations

import json
from pathlib import Path

from src.ingestion.loaders import Document
from src.ingestion.splitter import split_fixed, split_section_aware

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "data" / "processed" / "documents.jsonl"


class FakeEncoder:
    """按空白切分的伪 tokenizer,便于不依赖网络验证切块逻辑。"""

    def encode(self, text: str) -> list[str]:
        return text.split()

    def decode(self, tokens: list[str]) -> str:
        return " ".join(tokens)


FAKE = FakeEncoder()


def mk_doc(text, section="Abstract", page=1, paper_id="p1", title="T",
           source="https://arxiv.org/abs/1") -> Document:
    return Document(
        paper_id=paper_id, title=title, section=section,
        page=page, text=text, source=source,
    )


# ---- fixed 切块 ----

def test_fixed_windows_and_overlap():
    docs = [mk_doc(" ".join(f"w{i}" for i in range(10)))]
    chunks = split_fixed(docs, chunk_size=4, overlap=1, encoder=FAKE)
    assert len(chunks) == 3
    assert chunks[0].text == "w0 w1 w2 w3"
    assert chunks[0].token_count == 4
    # overlap:后一块开头重现前一块尾部 token
    assert chunks[1].text.split()[0] == "w3"
    assert chunks[2].text.split()[0] == "w6"
    assert chunks[2].text == "w6 w7 w8 w9"


def test_chunk_id_unique():
    docs = [mk_doc(" ".join(f"w{i}" for i in range(10)))]
    chunks = split_fixed(docs, chunk_size=4, overlap=1, encoder=FAKE)
    ids = [c.chunk_id for c in chunks]
    assert len(ids) == len(set(ids))
    assert ids == ["p1-0001", "p1-0002", "p1-0003"]


def test_chunk_not_empty():
    docs = [mk_doc("   "), mk_doc("aaa bbb ccc")]
    chunks = split_fixed(docs, chunk_size=10, overlap=1, encoder=FAKE)
    assert len(chunks) == 1
    assert all(c.text.strip() for c in chunks)


def test_metadata_preserved():
    doc = mk_doc("aaa bbb ccc ddd eee", section="3 Method", page=2)
    chunks = split_fixed([doc], chunk_size=10, overlap=1, encoder=FAKE)
    c = chunks[0]
    assert c.paper_id == "p1" and c.title == "T"
    assert c.section == "3 Method"
    assert c.page_start == 2 and c.page_end == 2
    assert c.source == "https://arxiv.org/abs/1"
    assert c.chunking == "fixed"


def test_fixed_can_cross_sections_and_tracks_pages():
    docs = [
        mk_doc("aaa bbb", section="Abstract", page=1),
        mk_doc("mmm nnn", section="3 Method", page=3),
    ]
    chunks = split_fixed(docs, chunk_size=10, overlap=1, encoder=FAKE)
    assert len(chunks) == 1
    c = chunks[0]
    assert c.section == "Abstract"  # 主 section = 窗口起始段落
    assert c.sections == ("Abstract", "3 Method")
    assert c.page_start == 1 and c.page_end == 3


# ---- section_aware 切块 ----

def test_section_aware_no_cross_section():
    docs = [
        mk_doc(" ".join(["a"] * 10), section="Abstract", page=1),
        mk_doc(" ".join(["m"] * 10), section="3 Method", page=2),
    ]
    chunks = split_section_aware(docs, chunk_size=6, overlap=1, encoder=FAKE)
    assert len(chunks) == 4  # 两节各拆 2 块
    for c in chunks:
        assert c.section in ("Abstract", "3 Method")
        # chunk 内不混两节内容
        assert not ("a" in c.text and "m" in c.text)


def test_section_aware_long_section_split():
    docs = [mk_doc(" ".join(["a"] * 10), section="Abstract", page=1)]
    chunks = split_section_aware(docs, chunk_size=4, overlap=1, encoder=FAKE)
    assert len(chunks) == 3  # 10 token 超长,组内续拆
    assert all(c.section == "Abstract" for c in chunks)


def test_short_paragraphs_merged():
    docs = [
        mk_doc("a a", section="Abstract", page=1),
        mk_doc("b b", section="Abstract", page=1),
        mk_doc("c c", section="Abstract", page=1),
    ]
    chunks = split_section_aware(docs, chunk_size=10, overlap=1, encoder=FAKE)
    assert len(chunks) == 1
    assert "a a" in chunks[0].text and "c c" in chunks[0].text


def test_section_aware_chunking_flag():
    docs = [mk_doc("aaa bbb ccc")]
    chunks = split_section_aware(docs, chunk_size=10, overlap=1, encoder=FAKE)
    assert chunks[0].chunking == "section_aware"


# ---- 真实语料 schema ----

def test_real_documents_schema():
    docs = []
    with open(DOCS, encoding="utf-8") as fh:
        for line in fh:
            rec = json.loads(line)
            if rec["paper_id"] == "rag_lewis2021":
                docs.append(Document(**rec))
    assert docs
    chunks = split_fixed(docs, chunk_size=100, overlap=10)
    assert chunks
    keys = {"chunk_id", "paper_id", "title", "section", "sections",
            "page_start", "page_end", "text", "source", "chunking", "token_count"}
    for c in chunks:
        rec = c.as_dict()
        assert set(rec) == keys
        assert rec["text"].strip()
        assert 0 < rec["token_count"] <= 100
        assert rec["page_start"] <= rec["page_end"]
    ids = [c.chunk_id for c in chunks]
    assert len(ids) == len(set(ids))
