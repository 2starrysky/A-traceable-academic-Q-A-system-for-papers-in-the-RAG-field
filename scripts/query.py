"""命令行入口:对单个问题执行 Dense Top-K 检索,打印 问题/Chunk ID/论文/章节/相似度/原文。

Day 8 阶段只做检索(不接 LLM);Day 9 在此之上追加生成与引用。
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
os.chdir(ROOT)  # 保证本地模型 data/models/<短名>/ 的相对路径解析到项目根

# Windows 控制台默认 GBK,打印论文原文的 Unicode 字符(如减号 − U+2212)会崩,强制 UTF-8
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from src.retrieval.dense import DenseRetriever

_PREVIEW = 300


def main() -> None:
    ap = argparse.ArgumentParser(description="对单个问题做 Dense Top-K 检索并打印可溯源结果")
    ap.add_argument("--question", "-q", required=True, help="要检索的问题")
    ap.add_argument("--index", default="data/processed/dense_index", help="索引目录(含 index.faiss/meta.jsonl)")
    ap.add_argument("--top-k", type=int, default=5)
    ap.add_argument("--full-text", action="store_true", help="打印完整原文(默认截断前 300 字符)")
    ap.add_argument("--device", default=None)
    args = ap.parse_args()

    index_path = ROOT / args.index
    print(f"加载索引 {index_path} ...")
    retriever = DenseRetriever.load(index_path, dim=None, encode_fn=None, device=args.device)
    hits = retriever.search(args.question, top_k=args.top_k)

    print(f"\n问题: {args.question}\n")
    if not hits:
        print("无检索结果。")
        return
    print(f"Top-{len(hits)} 检索结果:")
    for i, hit in enumerate(hits, 1):
        text = hit.text if args.full_text else (hit.text[: _PREVIEW] + ("…" if len(hit.text) > _PREVIEW else ""))
        print(f"#{i}  相似度 {hit.score:.4f} | {hit.chunk_id}")
        print(f"    论文: {hit.title}({hit.paper_id})")
        print(f"    章节: {hit.section} | 页码 {hit.page_start}-{hit.page_end}")
        print(f"    原文: {text}")
        print()


if __name__ == "__main__":
    main()
