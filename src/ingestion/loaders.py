"""论文加载器:读取元数据,用 pypdf 逐页提取,组装成结构化 document(paper_id/title/section/page/text/source)。"""
from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

from pypdf import PdfReader

from src.ingestion.cleaner import (
    clean_page_text,
    find_repeated_footers,
    split_section_paragraphs,
)


@dataclass(frozen=True)
class PaperMetadata:
    paper_id: str
    title: str
    arxiv_id: str
    source: str
    year: int | None = None


@dataclass
class Document:
    paper_id: str
    title: str
    section: str
    page: int
    text: str
    source: str

    def as_dict(self) -> dict:
        return {
            "paper_id": self.paper_id,
            "title": self.title,
            "section": self.section,
            "page": self.page,
            "text": self.text,
            "source": self.source,
        }


def load_metadata(csv_path: str | Path) -> dict[str, PaperMetadata]:
    """从 literature_matrix.csv 读取 paper_id → 元数据 映射。"""
    result: dict[str, PaperMetadata] = {}
    with open(csv_path, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            paper_id = (row.get("paper_id") or "").strip()
            arxiv_id = (row.get("arxiv_id") or "").strip()
            year_raw = (row.get("year") or "").strip()
            result[paper_id] = PaperMetadata(
                paper_id=paper_id,
                title=(row.get("title") or "").strip(),
                arxiv_id=arxiv_id,
                source=f"https://arxiv.org/abs/{arxiv_id}" if arxiv_id else "",
                year=int(year_raw) if year_raw.isdigit() else None,
            )
    return result


def iter_pdf_pages(pdf_path: str | Path) -> Iterator[tuple[int, str]]:
    """逐页提取文本,产出 (page_number, text),页码从 1 开始。"""
    reader = PdfReader(str(pdf_path))
    for i, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        if text.strip():
            yield i, text


def validate_corpus(pdf_dir: str | Path, metadata: dict[str, PaperMetadata]) -> dict:
    """核对 PDF 文件与元数据是否一一对应。"""
    pdf_ids = {p.stem for p in Path(pdf_dir).glob("*.pdf")}
    meta_ids = set(metadata)
    return {
        "n_papers": len(pdf_ids & meta_ids),
        "missing": sorted(meta_ids - pdf_ids),
        "extra": sorted(pdf_ids - meta_ids),
    }


def build_documents(
    pdf_dir: str | Path,
    metadata: dict[str, PaperMetadata],
) -> Iterator[Document]:
    """把每篇 PDF 清洗并按 (section, page) 切分为 Document 记录流。"""
    for paper_id, meta in metadata.items():
        pdf_path = Path(pdf_dir) / f"{paper_id}.pdf"
        if not pdf_path.exists():
            continue
        pages = list(iter_pdf_pages(pdf_path))
        page_texts = [text for _, text in pages]
        repeated = find_repeated_footers(page_texts)
        cleaned = [clean_page_text(text, repeated) for text in page_texts]
        for section, page, para in split_section_paragraphs(cleaned):
            yield Document(
                paper_id=paper_id,
                title=meta.title,
                section=section,
                page=page,
                text=para,
                source=meta.source,
            )
