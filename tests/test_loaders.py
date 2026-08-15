"""ingestion 模块测试:元数据 / PDF 提取 / 文本清洗 / 章节标注 / 文档 schema。"""
from __future__ import annotations

from pathlib import Path

from src.ingestion import cleaner
from src.ingestion.loaders import (
    build_documents,
    iter_pdf_pages,
    load_metadata,
    validate_corpus,
)

ROOT = Path(__file__).resolve().parents[1]
PAPERS = ROOT / "data" / "raw" / "papers"
CSV = ROOT / "research" / "literature_matrix.csv"
EMPTY_FOOTERS = {"exact": set(), "templates": set()}


# ---- 元数据 ----

def test_metadata_has_12_papers():
    meta = load_metadata(CSV)
    assert len(meta) >= 12


def test_metadata_fields():
    meta = load_metadata(CSV)
    rag = meta["rag_lewis2021"]
    assert rag.title.startswith("Retrieval-Augmented Generation")
    assert rag.arxiv_id == "2005.11401"
    assert rag.source == "https://arxiv.org/abs/2005.11401"


def test_corpus_matches_metadata():
    meta = load_metadata(CSV)
    check = validate_corpus(PAPERS, meta)
    assert not check["missing"]
    assert not check["extra"]
    assert check["n_papers"] == len(meta)


def test_pdf_extraction_nonempty():
    pages = list(iter_pdf_pages(PAPERS / "rag_lewis2021.pdf"))
    assert len(pages) > 10
    assert all(text.strip() for _, text in pages)
    assert [n for n, _ in pages] == list(range(1, len(pages) + 1))


# ---- 清洗 ----

def test_cleaner_removes_arxiv_stamp():
    out = cleaner.clean_page_text(
        "Abstract\narXiv:2005.11401v4  [cs.CL]  12 Apr 2021\nSome body text.",
        EMPTY_FOOTERS,
    )
    assert "arXiv:2005" not in out
    assert "Abstract" in out and "Some body text" in out


def test_cleaner_removes_page_number():
    out = cleaner.clean_page_text("Some text.\n7\n", EMPTY_FOOTERS)
    assert "Some text" in out
    assert "\n7\n" not in out


def test_cleaner_merges_hyphenation():
    out = cleaner.clean_page_text("down-\nstream", EMPTY_FOOTERS)
    assert "downstream" in out


def test_cleaner_removes_repeated_footer():
    rep = cleaner.find_repeated_footers(["header X\nbody a", "header X\nbody b"])
    assert "header X" in rep["exact"]
    out = cleaner.clean_page_text("header X\nkeep me", rep)
    assert "header X" not in out and "keep me" in out


def test_cleaner_removes_page_variant_footer():
    rep = cleaner.find_repeated_footers(
        ["111:2 Lyu, et al.\nbody a", "111:3 Lyu, et al.\nbody b"]
    )
    assert rep["templates"]
    out = cleaner.clean_page_text("111:5 Lyu, et al.\nkeep me", rep)
    assert "Lyu, et al" not in out and "keep me" in out


def test_cleaner_strips_control_chars():
    z = chr(0x200B)
    bom = chr(0xFEFF)
    assert cleaner.strip_control_chars(f"a{z}b{bom}c") == "abc"


def test_cleaner_collapses_spaces():
    assert cleaner.collapse_spaces("  a\t  b   c  ") == "a b c"


# ---- 章节检测 ----

def test_section_header_positive():
    for s in [
        "2.1 Models", "5.3. Qualitative Analysis", "2 RELATED WORK",
        "3.1 News Collection", "4 EXPERIMENT", "I. INTRODUCTION",
        "Abstract", "3 Method", '3.2 Open-domain Summarization: RAG in "Delete"',
    ]:
        assert cleaner.is_section_header(s), s


def test_section_header_negative():
    for s in [
        "1. The question should be fully answered",
        "2022. Improving language models by retrieving from",
        "X. Bresson, and B. Hooi,", "Table 4: Evaluation", "Accuracy",
        "This is just a normal sentence about retrieval methods.",
    ]:
        assert not cleaner.is_section_header(s), s


def test_clean_heading_truncates_inline_body():
    s = "4.1.2 Implementation. Our ColBERT models are implemented on top of PyTorch."
    assert cleaner._clean_heading(s) == "4.1.2 Implementation"


def test_split_paragraphs_annotates_sections():
    paras = cleaner.split_section_paragraphs(
        ["Abstract\nWe propose X. This is more text here.\n\n3. Method\nWe do Y."]
    )
    secs = [sec for sec, _, _ in paras]
    assert "Abstract" in secs and "3. Method" in secs


# ---- 文档 schema ----

def test_build_documents_schema():
    meta = load_metadata(CSV)
    docs = [
        d for d in build_documents(PAPERS, meta)
        if d.paper_id in {"rag_lewis2021", "ragas_es2025"}
    ]
    assert docs
    for d in docs:
        rec = d.as_dict()
        assert set(rec) == {"paper_id", "title", "section", "page", "text", "source"}
        assert rec["text"].strip()
        assert isinstance(rec["page"], int) and rec["page"] >= 1
        assert rec["source"].startswith("https://arxiv.org/abs/")
    by_paper = {}
    for d in docs:
        by_paper.setdefault(d.paper_id, []).append(d)
    for pid, ds in by_paper.items():
        assert [d.page for d in ds] == sorted(d.page for d in ds)
