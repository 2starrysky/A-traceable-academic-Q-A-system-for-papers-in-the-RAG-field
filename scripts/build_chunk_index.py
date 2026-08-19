"""切块 + 建稠密索引:读 documents.jsonl → 按参数切块 → bge-m3 编码 → 保存 FAISS 索引。

复用 Day 7/D8 的 splitter/build_index 逻辑,但由单一 CLI 参数化(chunk_size/overlap/
chunking 策略),产出指定文件名,供 E5 切块消融为不同切法各自建索引。
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
os_chdir = True
import os
os.chdir(ROOT)

from src.ingestion.loaders import Document
from src.ingestion.splitter import Chunk, split_fixed, split_section_aware
from src.retrieval.dense import DenseRetriever, _records_from_jsonl


def _read_documents(path: Path) -> dict[str, list[Document]]:
    by_paper: dict[str, list[Document]] = {}
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            rec = json.loads(line)
            by_paper.setdefault(rec["paper_id"], []).append(Document(**rec))
    return by_paper


def _write_chunks(chunks: list[Chunk], path: Path) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        for c in chunks:
            fh.write(json.dumps(c.as_dict(), ensure_ascii=False) + "\n")


def main() -> None:
    ap = argparse.ArgumentParser(description="按参数切块并构建 bge-m3 稠密索引")
    ap.add_argument("--documents", default="data/processed/documents.jsonl")
    ap.add_argument("--chunk-size", type=int, default=512)
    ap.add_argument("--overlap", type=int, default=80)
    ap.add_argument("--chunking", choices=["fixed", "section_aware"], default="fixed")
    ap.add_argument("--chunks-out", default=None,
                    help="chunk JSONL 输出路径(默认 data/processed/chunks_<name>.jsonl)")
    ap.add_argument("--index-out", default=None,
                    help="索引目录(默认 data/processed/idx_<name>);已存在则报错")
    ap.add_argument("--model", default="BAAI/bge-m3")
    ap.add_argument("--batch-size", type=int, default=32)
    ap.add_argument("--device", default=None)
    args = ap.parse_args()

    name = f"{args.chunking}_sz{args.chunk_size}_ov{args.overlap}"
    chunks_out = Path(args.chunks_out) if args.chunks_out else ROOT / "data" / "processed" / f"chunks_{name}.jsonl"
    index_out = Path(args.index_out) if args.index_out else ROOT / "data" / "processed" / f"idx_{name}"

    if index_out.exists():
        print(f"INFO 索引目录已存在,跳过: {index_out}", file=sys.stderr)

    docs_path = ROOT / args.documents
    by_paper = _read_documents(docs_path)
    if not by_paper:
        print(f"ERROR 无可切分文档 {docs_path}", file=sys.stderr)
        sys.exit(1)

    chunks_all: list[Chunk] = []
    for pid in sorted(by_paper):
        if args.chunking == "fixed":
            chunks_all.extend(split_fixed(by_paper[pid], args.chunk_size, args.overlap))
        else:
            chunks_all.extend(split_section_aware(by_paper[pid], args.chunk_size, args.overlap))
    _write_chunks(chunks_all, chunks_out)
    print(f"切块: {len(chunks_all)} chunks → {chunks_out} "
          f"(size={args.chunk_size}, overlap={args.overlap}, {args.chunking})")
    print(f"  平均 token={sum(c.token_count for c in chunks_all)/len(chunks_all):.1f}, "
          f"跨章节={sum(1 for c in chunks_all if len(c.sections) > 1)}")

    if index_out.exists():
        print("INFO 索引已存在,结束。")
        return

    records = _records_from_jsonl(chunks_out)
    print(f"加载模型 {args.model} ...")
    retriever = DenseRetriever.from_model_name(args.model, device=args.device)
    print(f"编码 {len(records)} chunks, dim={retriever.dim}, batch={args.batch_size} ...")
    t0 = time.time()
    retriever.build_index(records, batch_size=args.batch_size, config={
        "embedding_model": args.model, "dim": retriever.dim,
        "index_type": "IndexFlatIP", "normalize": True, "n_chunks": len(records),
        "chunking": args.chunking, "chunk_size": args.chunk_size, "overlap": args.overlap,
        "source": str(docs_path.relative_to(ROOT)),
    })
    retriever.save(index_out)
    print(f"索引已保存 {index_out} (用时 {time.time()-t0:.1f}s)")


if __name__ == "__main__":
    main()