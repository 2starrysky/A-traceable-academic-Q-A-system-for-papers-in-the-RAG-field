"""命令行入口:读 chunk JSONL → bge-m3 批量编码 → 构建并保存 FAISS 稠密索引 + 元数据 + 配置。"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
os.chdir(ROOT)  # 保证本地模型 data/models/<短名>/ 的相对路径解析到项目根

from src.retrieval.dense import DenseRetriever, _records_from_jsonl


def _git_head() -> str | None:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, cwd=ROOT, check=True,
        ).stdout.strip()
        return out or None
    except Exception:
        return None


def main() -> None:
    ap = argparse.ArgumentParser(description="读 chunk JSONL,用 bge-m3 构建并保存 FAISS 稠密索引")
    ap.add_argument("--chunks", default="data/processed/chunks_fixed.jsonl")
    ap.add_argument("--index", default="data/processed/dense_index")
    ap.add_argument("--model", default="BAAI/bge-m3")
    ap.add_argument("--batch-size", type=int, default=32)
    ap.add_argument("--device", default=None)
    args = ap.parse_args()

    chunks_path = ROOT / args.chunks
    index_path = ROOT / args.index

    records = _records_from_jsonl(chunks_path)
    if not records:
        print(f"ERROR 没有可索引的 chunk({chunks_path})", file=sys.stderr)
        sys.exit(1)

    print(f"加载模型 {args.model} ...")
    retriever = DenseRetriever.from_model_name(args.model, device=args.device)
    print(f"索引 {len(records)} 个 chunk,维度 {retriever.dim},batch_size={args.batch_size} ...")
    t0 = time.time()
    retriever.build_index(
        records,
        batch_size=args.batch_size,
        config={
            "embedding_model": args.model,
            "dim": retriever.dim,
            "index_type": "faiss.IndexFlatIP",
            "normalize": True,
            "n_chunks": len(records),
            "source": str(chunks_path.relative_to(ROOT)),
            "git_head": _git_head(),
        },
    )
    retriever.save(index_path)
    elapsed = time.time() - t0
    print(f"完成:{len(records)} chunks → {index_path}(编码+建索引 {elapsed:.1f}s)")
    print(f"复现配置: {index_path / 'config.json'}")


if __name__ == "__main__":
    main()
