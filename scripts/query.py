"""命令行入口:对单个问题执行 检索 → 生成 → 带引用回答。

默认走完整 RAG 闭环(读 configs/dense.yaml 的 top_k 与 generation 配置);
加 --retrieve-only 保留 Day 8 纯检索行为。
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
os.chdir(ROOT)  # 保证本地模型 data/models/<短名>/ 与 .env 的相对路径解析到项目根

# Windows 控制台默认 GBK,打印论文原文的 Unicode 字符(如减号 − U+2212)会崩,强制 UTF-8
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import yaml

from src.generation.generator import create_generator
from src.pipeline import answer_question
from src.retrieval.dense import DenseRetriever

_PREVIEW = 300
_CITE_PREVIEW = 160


def _load_config(path: str) -> dict:
    with open(ROOT / path, encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def _clip(text: str, n: int) -> str:
    return text if len(text) <= n else text[:n] + "…"


def _print_retrieval(question: str, hits, full_text: bool) -> None:
    print(f"\n问题: {question}\n")
    if not hits:
        print("无检索结果。")
        return
    print(f"Top-{len(hits)} 检索结果:")
    for i, hit in enumerate(hits, 1):
        text = hit.text if full_text else _clip(hit.text, _PREVIEW)
        print(f"#{i}  相似度 {hit.score:.4f} | {hit.chunk_id}")
        print(f"    论文: {hit.title}({hit.paper_id})")
        print(f"    章节: {hit.section} | 页码 {hit.page_start}-{hit.page_end}")
        print(f"    原文: {text}")
        print()


def _print_answer(result, full_text: bool) -> None:
    print(f"\n问题: {result.question}\n")
    print("========== 答案 ==========")
    print(result.answer)
    if result.refused:
        print("\n(系统判定:上下文无足够证据,已拒答)")
    print("\n========== 引用来源 ==========")
    if not result.citations:
        print("(无引用)")
    for n, hit in enumerate(result.citations, 1):
        text = hit.text if full_text else _clip(hit.text, _CITE_PREVIEW)
        print(f"[{n}] {hit.chunk_id} | {hit.title}({hit.paper_id}) | "
              f"章节:{hit.section} | 页码 {hit.page_start}-{hit.page_end} | 相似度 {hit.score:.4f}")
        print(f"    原文: {text}")
    print("\n========== 检索 Top-K(生成所用) ==========")
    for i, hit in enumerate(result.hits, 1):
        print(f"#{i}  相似度 {hit.score:.4f} | {hit.chunk_id} | "
              f"{hit.title}({hit.paper_id}) | {hit.section} | 页码 {hit.page_start}-{hit.page_end}")


def main() -> None:
    ap = argparse.ArgumentParser(description="对单个问题执行 Dense 检索+生成,输出带引用回答")
    ap.add_argument("--question", "-q", required=True, help="要回答的问题")
    ap.add_argument("--config", default="configs/dense.yaml", help="实验配置(读 top_k/generation/index_path)")
    ap.add_argument("--index", default=None, help="索引目录(覆盖配置)")
    ap.add_argument("--top-k", type=int, default=None, help="Top-K(覆盖配置)")
    ap.add_argument("--retrieve-only", action="store_true", help="只检索不生成(Day 8 行为)")
    ap.add_argument("--full-text", action="store_true", help="打印完整原文(默认截断)")
    ap.add_argument("--device", default=None)
    args = ap.parse_args()

    cfg = _load_config(args.config)
    retrieval = cfg.get("retrieval", {})
    top_k = args.top_k if args.top_k is not None else retrieval.get("top_k", 5)
    index = args.index or retrieval.get("dense", {}).get("index_path", "data/processed/dense_index")

    print(f"加载索引 {index} ...")
    retriever = DenseRetriever.load(ROOT / index, device=args.device)

    if args.retrieve_only:
        hits = retriever.search(args.question, top_k=top_k)
        _print_retrieval(args.question, hits, full_text=args.full_text)
        return

    gen = retrieval.get("generation", {})
    generator = create_generator(
        provider=gen.get("provider", "deepseek"),
        model=gen.get("llm_model"),
        base_url=gen.get("base_url"),
        temperature=gen.get("temperature", 0.2),
    )
    result = answer_question(args.question, retriever, generator, top_k=top_k)
    _print_answer(result, full_text=args.full_text)


if __name__ == "__main__":
    main()
