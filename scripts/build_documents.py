"""命令行入口:把 data/raw/papers 的论文语料转成 data/processed/documents.jsonl。"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.ingestion.loaders import build_documents, load_metadata, validate_corpus


def main() -> None:
    ap = argparse.ArgumentParser(description="把论文 PDF 语料转成结构化 documents.jsonl")
    ap.add_argument("--papers", default="data/raw/papers", help="PDF 目录")
    ap.add_argument("--metadata", default="research/literature_matrix.csv", help="文献矩阵 CSV")
    ap.add_argument("--output", default="data/processed/documents.jsonl", help="输出 JSONL 路径")
    args = ap.parse_args()

    pdf_dir = ROOT / args.papers
    meta_path = ROOT / args.metadata
    out_path = ROOT / args.output

    metadata = load_metadata(meta_path)
    check = validate_corpus(pdf_dir, metadata)
    if check["missing"] or check["extra"]:
        print(f"WARNING 元数据有但 PDF 缺失: {check['missing']}  多余 PDF: {check['extra']}", file=sys.stderr)
    if not check["n_papers"]:
        print(f"ERROR 没有可解析的论文(pdf_dir={pdf_dir})", file=sys.stderr)
        sys.exit(1)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    per_paper: Counter[str] = Counter()
    sections_per_paper: dict[str, set[str]] = {}
    total = 0
    with open(out_path, "w", encoding="utf-8") as fh:
        for doc in build_documents(pdf_dir, metadata):
            fh.write(json.dumps(doc.as_dict(), ensure_ascii=False) + "\n")
            per_paper[doc.paper_id] += 1
            sections_per_paper.setdefault(doc.paper_id, set()).add(doc.section)
            total += 1

    print(f"元数据 {len(metadata)} 篇,解析 {check['n_papers']} 篇,共 {total} 条 document")
    print(f"输出: {out_path}")
    for pid in sorted(per_paper):
        print(f"  {pid:22s} 段落={per_paper[pid]:5d}  章节={len(sections_per_paper[pid]):3d}")


if __name__ == "__main__":
    main()
