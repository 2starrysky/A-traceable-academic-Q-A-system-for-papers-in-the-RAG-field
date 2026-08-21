"""Gradio Demo：可溯源学术问答系统 Web 界面。

启动方式：
  python app.py              # 默认 0.0.0.0:7860
  python app.py --port 8080  # 自定义端口

功能：
  - 选择检索器(Dense / BM25 / Hybrid / Hybrid+Reranker)
  - 选择 Top-K(3~8)
  - 输入问题 → 返回带引用答案 + 检索详情
"""
from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from dotenv import load_dotenv
load_dotenv()

import gradio as gr

from src.generation.generator import create_generator
from src.pipeline import answer_question
from src.retrieval.dense import DenseRetriever

# ── 全局缓存 ────────────────────────────────────────────────────────
_chunks: dict[str, dict] = {}
_generator = None
_retrievers: dict[str, object] = {}


def _load_chunks():
    """加载 chunks_fixed.jsonl。"""
    global _chunks
    if _chunks:
        return _chunks
    path = ROOT / "data" / "processed" / "chunks_fixed.jsonl"
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                c = __import__("json").loads(line)
                _chunks[c["chunk_id"]] = c
    print(f"  [OK] loaded {len(_chunks)} chunks")
    return _chunks


def _get_generator():
    global _generator
    if _generator is None:
        _generator = create_generator()
    return _generator


def _get_retriever(method: str):
    """构建检索器（带缓存）。"""
    if method in _retrievers:
        return _retrievers[method]

    chunks = _load_chunks()
    chunk_list = list(chunks.values())

    if method == "Dense":
        retriever = DenseRetriever.from_chunks(chunk_list)

    elif method == "BM25":
        from src.retrieval.bm25 import BM25Retriever
        retriever = BM25Retriever.from_chunks(chunk_list)

    elif method == "Hybrid":
        from src.retrieval.bm25 import BM25Retriever
        from src.retrieval.fusion import merge_hits

        dense = DenseRetriever.from_chunks(chunk_list)
        bm25 = BM25Retriever.from_chunks(chunk_list)

        class _Hybrid:
            def search(self, query, top_k=5):
                d = dense.search(query, top_k=top_k * 2)
                b = bm25.search(query, top_k=top_k * 2)
                return merge_hits(d, b, top_k=top_k)

        retriever = _Hybrid()

    elif method == "Hybrid+Reranker":
        from src.retrieval.bm25 import BM25Retriever
        from src.retrieval.fusion import merge_hits
        from src.retrieval.reranker import Reranker, rerank_hits

        dense = DenseRetriever.from_chunks(chunk_list)
        bm25 = BM25Retriever.from_chunks(chunk_list)
        reranker = Reranker.from_model_name("BAAI/bge-reranker-v2-m3")

        class _HybridRerank:
            def search(self, query, top_k=5):
                coarse_k = 20
                d = dense.search(query, top_k=coarse_k)
                b = bm25.search(query, top_k=coarse_k)
                coarse = merge_hits(d, b, top_k=coarse_k)
                return rerank_hits(query, coarse, reranker, top_k=top_k)

        retriever = _HybridRerank()

    else:
        raise ValueError(f"Unknown method: {method}")

    _retrievers[method] = retriever
    return retriever


# ── 核心回答函数 ──────────────────────────────────────────────────────

def answer(question: str, method: str, top_k: int):
    """Gradio 回调：检索 → 生成 → 格式化输出。"""
    if not question.strip():
        return "请输入问题。", "", "", ""

    retriever = _get_retriever(method)
    generator = _get_generator()

    t0 = time.time()
    result = answer_question(question, retriever, generator, top_k=top_k)
    elapsed = time.time() - t0

    # ── 答案 ──
    if result.refused:
        answer_text = f"{result.answer}\n\n⏱ 延迟: {elapsed:.2f}s (系统判定:上下文无足够证据,已拒答)"
    else:
        answer_text = f"{result.answer}\n\n⏱ 延迟: {elapsed:.2f}s"

    # ── 引用来源 ──
    cites = []
    for i, hit in enumerate(result.citations, 1):
        cites.append(
            f"**[{i}]** {hit.title} (`{hit.paper_id}`)\n"
            f"章节: {hit.section} | 页码: {hit.page_start}-{hit.page_end}\n"
            f"Chunk ID: `{hit.chunk_id}` | 分数: {hit.score:.4f}\n"
            f"> {hit.text[:300]}..."
        )
    cite_text = "\n\n---\n\n".join(cites) if cites else "(无引用)"

    # ── 检索详情 ──
    details = []
    for i, hit in enumerate(result.hits, 1):
        details.append(
            f"#{i} | `{hit.chunk_id}` | 分数: {hit.score:.4f}\n"
            f"论文: {hit.title} (`{hit.paper_id}`)\n"
            f"章节: {hit.section} | 页码: {hit.page_start}-{hit.page_end}\n"
            f"> {hit.text[:200]}..."
        )
    detail_text = "\n\n---\n\n".join(details) if details else "(无检索结果)"

    return answer_text, cite_text, detail_text, f"{elapsed:.2f}s"


# ── Gradio UI ─────────────────────────────────────────────────────────

def build_ui():
    with gr.Blocks(
        title="RAG Paper Assistant",
        theme=gr.themes.Soft(),
        css="""
        .main-title { text-align: center; margin-bottom: 0.5em; }
        .subtitle { text-align: center; color: #666; font-size: 0.9em; }
        """
    ) as app:
        gr.HTML("<h1 class='main-title'>📚 RAG Paper Assistant</h1>")
        gr.HTML("<p class='subtitle'>可溯源学术问答系统 — 基于 12 篇 RAG 论文知识库</p>")

        with gr.Row():
            # ── 左栏：输入 ──
            with gr.Column(scale=1):
                question = gr.Textbox(
                    label="🔍 输入问题",
                    placeholder="例如: RAG-Sequence 是什么?",
                    lines=3,
                )
                with gr.Row():
                    method = gr.Dropdown(
                        choices=["Dense", "BM25", "Hybrid", "Hybrid+Reranker"],
                        value="Dense",
                        label="检索器",
                    )
                    top_k = gr.Slider(
                        minimum=3, maximum=8, value=5, step=1,
                        label="Top-K",
                    )
                submit_btn = gr.Button("🚀 提问", variant="primary")

                gr.Markdown(
                    """
                    **示例问题：**
                    - RAG-Sequence 是什么?
                    - Dense 和 Sparse 检索各有什么优势?
                    - Top-K 越大越好吗?
                    - Lost in the Middle 发现了什么?
                    """
                )

            # ── 右栏：输出 ──
            with gr.Column(scale=2):
                answer_output = gr.Textbox(label="💡 答案", lines=8)
                with gr.Tabs():
                    with gr.TabItem("📎 引用来源"):
                        cite_output = gr.Markdown(label="引用来源")
                    with gr.TabItem("🔎 检索详情"):
                        detail_output = gr.Markdown(label="检索 Top-K 详情")
                latency_output = gr.Textbox(label="⏱ 延迟", interactive=False)

        # ── 事件绑定 ──
        submit_btn.click(
            fn=answer,
            inputs=[question, method, top_k],
            outputs=[answer_output, cite_output, detail_output, latency_output],
        )
        question.submit(
            fn=answer,
            inputs=[question, method, top_k],
            outputs=[answer_output, cite_output, detail_output, latency_output],
        )

    return app


# ── 入口 ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="RAG Paper Assistant Gradio Demo")
    parser.add_argument("--port", type=int, default=7860)
    parser.add_argument("--host", type=str, default="0.0.0.0")
    parser.add_argument("--share", action="store_true", help="Gradio 公网分享链接")
    args = parser.parse_args()

    print("=" * 60)
    print("RAG Paper Assistant — Gradio Demo")
    print("=" * 60)
    print("初始化:加载 chunks + 模型...")
    _load_chunks()
    print("启动 Gradio 服务...")

    app = build_ui()
    app.launch(server_name=args.host, server_port=args.port, share=args.share)
