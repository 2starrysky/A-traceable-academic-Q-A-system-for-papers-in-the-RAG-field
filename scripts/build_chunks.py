"""命令行入口:读 documents.jsonl,生成 fixed/section_aware 两种 chunk,并输出切块统计。"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.ingestion.loaders import Document
from src.ingestion.splitter import Chunk, split_fixed, split_section_aware


def _read_documents(path: Path) -> dict[str, list[Document]]:
    by_paper: dict[str, list[Document]] = {}
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            rec = json.loads(line)
            doc = Document(**rec)
            by_paper.setdefault(doc.paper_id, []).append(doc)
    return by_paper


def _write_chunks(chunks: list[Chunk], path: Path) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        for c in chunks:
            fh.write(json.dumps(c.as_dict(), ensure_ascii=False) + "\n")


def _summarize(chunks: list[Chunk], per_paper: dict[str, int]) -> dict:
    tokens = [c.token_count for c in chunks]
    return {
        "total": len(chunks),
        "per_paper": dict(sorted(per_paper.items())),
        "avg_tokens": round(sum(tokens) / len(tokens), 1) if tokens else 0,
        "min_tokens": min(tokens) if tokens else 0,
        "max_tokens": max(tokens) if tokens else 0,
        "empty_chunks": sum(1 for c in chunks if not c.text.strip()),
        "multi_section_chunks": sum(1 for c in chunks if len(c.sections) > 1),
        "papers_with_chunks": len(per_paper),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="把 documents.jsonl 切成 fixed / section_aware 两种 chunk")
    ap.add_argument("--documents", default="data/processed/documents.jsonl")
    ap.add_argument("--chunk-size", type=int, default=512)
    ap.add_argument("--overlap", type=int, default=80)
    ap.add_argument("--output-dir", default="data/processed")
    ap.add_argument("--stats", default="outputs/chunk_statistics.json")
    ap.add_argument("--chunking", choices=["both", "fixed", "section_aware"], default="both")
    args = ap.parse_args()

    docs_path = ROOT / args.documents
    out_dir = ROOT / args.output_dir
    stats_path = ROOT / args.stats

    by_paper = _read_documents(docs_path)
    if not by_paper:
        print(f"ERROR 没有可切分的文档({docs_path})", file=sys.stderr)
        sys.exit(1)

    out_dir.mkdir(parents=True, exist_ok=True)
    stats_path.parent.mkdir(parents=True, exist_ok=True)

    do_fixed = args.chunking in ("both", "fixed")
    do_sa = args.chunking in ("both", "section_aware")
    fixed_all, sa_all = [], []
    fixed_per, sa_per = {}, {}
    for pid in sorted(by_paper):
        docs = by_paper[pid]
        if do_fixed:
            cs = split_fixed(docs, args.chunk_size, args.overlap)
            fixed_all.extend(cs)
            fixed_per[pid] = len(cs)
        if do_sa:
            cs = split_section_aware(docs, args.chunk_size, args.overlap)
            sa_all.extend(cs)
            sa_per[pid] = len(cs)

    report: dict = {
        "config": {
            "chunk_size": args.chunk_size,
            "overlap": args.overlap,
            "tokenizer": "tiktoken cl100k_base",
            "source": str(docs_path.relative_to(ROOT)),
        }
    }
    if do_fixed:
        _write_chunks(fixed_all, out_dir / "chunks_fixed.jsonl")
        report["fixed"] = _summarize(fixed_all, fixed_per)
    if do_sa:
        _write_chunks(sa_all, out_dir / "chunks_section_aware.jsonl")
        report["section_aware"] = _summarize(sa_all, sa_per)

    with open(stats_path, "w", encoding="utf-8") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=2)

    print(f"文档 {len(by_paper)} 篇,chunk_size={args.chunk_size},overlap={args.overlap}")
    for name, chunks, per in (("fixed", fixed_all, fixed_per), ("section_aware", sa_all, sa_per)):
        if chunks:
            print(f"  {name:14s}: {len(chunks):5d} chunks,平均 {report[name]['avg_tokens']:.0f} token")
    print(f"统计: {stats_path}")


if __name__ == "__main__":
    main()
