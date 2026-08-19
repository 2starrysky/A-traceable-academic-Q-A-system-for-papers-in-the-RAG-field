"""E1 Dense Baseline 实验:逐题 检索→生成→判定,含神谕(oracle)检索归因。

产物 outputs/experiments/e01_dense/:
- config.json      实验配置 + git commit + 评估集版本 + 时间戳
- per_question.jsonl  逐题全量(检索命中/答案/引用/判定/延迟/oracle)
- metrics.json     汇总指标(检索 Hit@K/MRR + 生成 引用正确率/真误拒答率/平均延迟)

plan 要求:不覆盖旧实验(目录已存在则报错);不自动修改论文结论(只记录)。
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import yaml

from src.evaluation import generation_metrics, retrieval_metrics
from src.generation.generator import create_generator
from src.retrieval.dense import DenseRetriever, RetrievalHit

_QUESTIONS = ROOT / "data" / "evaluation" / "questions.jsonl"
_CHUNKS = ROOT / "data" / "processed" / "chunks_fixed.jsonl"
_DEFAULT_OUT = "outputs/experiments/e01_dense"


def _git_head() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"],
                              capture_output=True, text=True, cwd=ROOT, check=True).stdout.strip()
    except Exception:
        return "unknown"


def _read_questions() -> list[dict]:
    qs = []
    with open(_QUESTIONS, encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                qs.append(json.loads(line))
    return qs


def _load_chunks() -> dict[str, dict]:
    chunks = {}
    with open(_CHUNKS, encoding="utf-8") as fh:
        for line in fh:
            r = json.loads(line)
            chunks[r["chunk_id"]] = r
    return chunks


def _oracle_hits(chunk_ids: list[str], chunks: dict[str, dict]) -> list[RetrievalHit]:
    """把标注相关 chunk 直接构造成检索命中(神谕检索,不跑检索器)。"""
    hits = []
    for cid in chunk_ids:
        m = chunks[cid]
        hits.append(RetrievalHit(
            score=1.0, chunk_id=m["chunk_id"], paper_id=m["paper_id"], title=m["title"],
            section=m["section"], sections=tuple(m.get("sections") or []),
            page_start=m["page_start"], page_end=m["page_end"], text=m["text"],
            source=m["source"], chunking=m["chunking"], token_count=m["token_count"],
        ))
    return hits


def _citation_correct_for(citations, gold_paper_id: str, gold_chunk_ids, gold_sections) -> bool:
    return any(generation_metrics.citation_correct(c, gold_paper_id, gold_chunk_ids, gold_sections)
               for c in citations)


def _build_retriever(method: str, retrieval_cfg: dict, chunks: dict[str, dict],
                     top_k: int = 5, device=None):
    """按 method 构造检索器:dense / bm25 / hybrid(RRF) / hybrid_rerank。

    返回 (retriever, method_label)。均实现 search(query, top_k) -> list[RetrievalHit]。
    """
    from src.retrieval.bm25 import BM25Retriever
    from src.retrieval.fusion import merge_hits

    index_path = retrieval_cfg.get("dense", {}).get("index_path", "data/processed/dense_index")

    if method == "dense":
        print(f"加载索引 {index_path} ...")
        return DenseRetriever.load(ROOT / index_path, device=device), "dense"

    if method == "bm25":
        print(f"构建 BM25 索引(基于 {len(chunks)} chunks) ...")
        return BM25Retriever.from_chunks(list(chunks.values())), "bm25"

    if method == "hybrid":
        print(f"加载索引 {index_path} + 构建 BM25 ...")
        dense = DenseRetriever.load(ROOT / index_path, device=device)
        bm25 = BM25Retriever.from_chunks(list(chunks.values()))

        class _Hybrid:
            def search(self, query: str, top_k: int = 5):
                d = dense.search(query, top_k=top_k * 2)  # 候选放大避免融合丢边
                b = bm25.search(query, top_k=top_k * 2)
                return merge_hits(d, b, top_k=top_k)

        return _Hybrid(), "hybrid"

    if method == "hybrid_rerank":
        from src.retrieval.reranker import Reranker, rerank_hits

        rerank_cfg = retrieval_cfg.get("rerank") or {}
        rerank_model = rerank_cfg.get("model", "BAAI/bge-reranker-v2-m3")
        final_top_k = retrieval_cfg.get("final_top_k", top_k)
        coarse_k = retrieval_cfg.get("top_k", 20)  # 粗排候选池大小

        print(f"加载索引 {index_path} + 构建 BM25 + 加载重排器 {rerank_model} ...")
        dense = DenseRetriever.load(ROOT / index_path, device=device)
        bm25 = BM25Retriever.from_chunks(list(chunks.values()))
        reranker = Reranker.from_model_name(rerank_model)

        class _HybridRerank:
            def search(self, query: str, top_k: int = 5):
                d = dense.search(query, top_k=coarse_k)
                b = bm25.search(query, top_k=coarse_k)
                coarse = merge_hits(d, b, top_k=coarse_k)
                return rerank_hits(query, coarse, reranker, top_k=final_top_k)

            def coarse_search(self, query: str, top_k: int = 5):
                d = dense.search(query, top_k=coarse_k)
                b = bm25.search(query, top_k=coarse_k)
                return merge_hits(d, b, top_k=coarse_k)

        return _HybridRerank(), "hybrid_rerank"

    raise ValueError(f"未知检索方法: {method}")


def main() -> None:
    import argparse
    ap = argparse.ArgumentParser(description="运行检索+生成实验(E1 dense / E2 bm25 / E3 hybrid / E4 hybrid_rerank)")
    ap.add_argument("--config", default="configs/dense.yaml")
    ap.add_argument("--out", default=_DEFAULT_OUT)
    ap.add_argument("--method", default=None, choices=["dense", "bm25", "hybrid", "hybrid_rerank"],
                    help="检索方法(默认取 config 的 retrieval.method)")
    ap.add_argument("--device", default=None)
    args = ap.parse_args()

    with open(ROOT / args.config, encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh) or {}
    retrieval_cfg = cfg.get("retrieval", {})
    top_k = retrieval_cfg.get("top_k", 5)
    method = args.method or retrieval_cfg.get("method", "dense")
    gen_cfg = retrieval_cfg.get("generation", {})

    if args.out == _DEFAULT_OUT:
        out = ROOT / {
            "dense": "outputs/experiments/e01_dense",
            "bm25": "outputs/experiments/e02_bm25",
            "hybrid": "outputs/experiments/e03_hybrid",
            "hybrid_rerank": "outputs/experiments/e04_hybrid_rerank",
        }[method]
    else:
        out = ROOT / args.out
    if out.exists():
        print(f"ERROR 输出目录已存在(不覆盖旧实验): {out}", file=sys.stderr)
        sys.exit(1)

    questions = _read_questions()
    chunks = _load_chunks()
    if len(questions) != 50:
        print(f"ERROR 评估集 {len(questions)} 题 != 50", file=sys.stderr)
        sys.exit(1)

    retriever, method_label = _build_retriever(method, retrieval_cfg, chunks, top_k=top_k, device=args.device)
    rerank = method == "hybrid_rerank"
    generator = create_generator(
        provider=gen_cfg.get("provider", "deepseek"),
        model=gen_cfg.get("llm_model"),
        base_url=gen_cfg.get("base_url"),
        temperature=gen_cfg.get("temperature", 0.2),
    )
    print(f"开始实验: method={method_label}, {len(questions)} 题, top_k={top_k} ...")

    per_question: list[dict] = []
    for i, q in enumerate(questions, 1):
        answerable = bool(q.get("answerable"))
        gold_ids = q.get("relevant_chunk_ids", [])
        gold_paper = q.get("paper_id", "")
        gold_sections = [chunks[c].get("section", "") for c in gold_ids if c in chunks]

        # 真实检索
        t0 = time.time()
        hits = retriever.search(q["question"], top_k=top_k)
        gen = generator.generate(q["question"], hits)
        real_lat = time.time() - t0
        real = {
            "retrieved": [{"chunk_id": h.chunk_id, "paper_id": h.paper_id,
                           "section": h.section, "page_start": h.page_start,
                           "page_end": h.page_end, "score": round(h.score, 4)} for h in hits],
            "answer": gen.text,
            "refused": gen.refused,
            "citations": [h.chunk_id for h in gen.citations],
            "latency": round(real_lat, 3),
        }
        real["citation_correct"] = _citation_correct_for(gen.citations, gold_paper, gold_ids, gold_sections)
        real["refusal_class"] = generation_metrics.classify_refusal(gen.refused, answerable)

        record = {
            "id": q["id"], "type": q["type"], "question": q["question"],
            "answerable": answerable, "real": real,
        }

        # 重排前后排名变化(仅 hybrid_rerank):记录每个相关 chunk 在粗排 vs 精排的位次
        if rerank and answerable and gold_ids and hasattr(retriever, "coarse_search"):
            coarse = retriever.coarse_search(q["question"], top_k=top_k)
            coarse_pos = {h.chunk_id: i + 1 for i, h in enumerate(coarse)}
            fine_pos = {h.chunk_id: i + 1 for i, h in enumerate(hits)}
            deltas = []
            moved = any(gold in coarse_pos and gold in fine_pos and
                        fine_pos[gold] < coarse_pos[gold] for gold in gold_ids)
            for g in gold_ids:
                deltas.append({
                    "chunk_id": g,
                    "coarse_rank": coarse_pos.get(g),
                    "fine_rank": fine_pos.get(g),
                    "delta": (coarse_pos.get(g) - fine_pos.get(g)) if (g in coarse_pos and g in fine_pos) else None,
                })
            record["rerank"] = {
                "coarse_retrieved": [h.chunk_id for h in coarse],
                "deltas": deltas,
                "gold_moved_up": moved,
            }

        # 神谕检索(仅可答题):直接喂标注相关 chunk
        if answerable and gold_ids:
            t0 = time.time()
            ohits = _oracle_hits(gold_ids, chunks)
            ogen = generator.generate(q["question"], ohits)
            o_lat = time.time() - t0
            record["oracle"] = {
                "answer": ogen.text,
                "refused": ogen.refused,
                "citations": [h.chunk_id for h in ogen.citations],
                "latency": round(o_lat, 3),
                "citation_correct": _citation_correct_for(ogen.citations, gold_paper, gold_ids, gold_sections),
                "refusal_class": generation_metrics.classify_refusal(ogen.refused, answerable),
            }

        per_question.append(record)
        if i % 10 == 0:
            print(f"  完成 {i}/{len(questions)}")

    # ---- 指标 ----
    # 检索(Hit@K/MRR):gold=相关 chunk,只在可答题上
    gold_by_id = {q["id"]: q.get("relevant_chunk_ids", []) for q in questions}
    preds = [[h["chunk_id"] for h in r["real"]["retrieved"]] for r in per_question]
    golds = [gold_by_id.get(r["id"], []) if r["answerable"] else [] for r in per_question]
    retrieval = retrieval_metrics.evaluate_retrieval(preds, golds, ks=(1, 3, 5))

    # 生成:真实组 / oracle 组
    real_records = [{
        "answerable": r["answerable"], "refused": r["real"]["refused"],
        "citation_correct": r["real"]["citation_correct"], "latency": r["real"]["latency"],
    } for r in per_question]
    oracle_records = [{
        "answerable": True, "refused": r["oracle"]["refused"],
        "citation_correct": r["oracle"]["citation_correct"], "latency": r["oracle"]["latency"],
    } for r in per_question if "oracle" in r]
    gen_real = generation_metrics.compute_generation_metrics(real_records)
    gen_oracle = generation_metrics.compute_generation_metrics(oracle_records)

    # 重排前后排名变化汇总(仅 hybrid_rerank)
    rerank_summary = None
    if rerank:
        up = 0
        down = 0
        stayed = 0
        not_in_top = 0
        for r in per_question:
            if "rerank" not in r:
                continue
            for d in r["rerank"]["deltas"]:
                if d["delta"] is None:
                    not_in_top += 1
                elif d["delta"] > 0:
                    up += 1
                elif d["delta"] < 0:
                    down += 1
                else:
                    stayed += 1
        rerank_summary = {"gold_moved_up": up, "gold_moved_down": down,
                          "gold_stayed": stayed, "gold_not_in_top": not_in_top}

    metrics = {
        "retrieval": retrieval,
        "generation_real": gen_real,
        "generation_oracle": gen_oracle,
        "rerank": rerank_summary,
    }

    # ---- 落盘 ----
    out.mkdir(parents=True, exist_ok=True)
    git = _git_head()
    rerank_cfg = retrieval_cfg.get("rerank") or {}
    config = {
        "experiment": f"E-{method_label}",
        "retrieval": {"method": method_label, "top_k": top_k,
                      "embedding_model": "BAAI/bge-m3",
                      "reranker": rerank,
                      "rerank_model": (rerank_cfg.get("model") if rerank else None),
                      "final_top_k": retrieval_cfg.get("final_top_k", top_k),
                      "fusion": "rrf" if method_label in ("hybrid", "hybrid_rerank") else None},
        "chunking": {"strategy": "fixed", "size": 512, "overlap": 80},
        "generation": {"provider": gen_cfg.get("provider"), "llm_model": gen_cfg.get("llm_model"),
                       "temperature": gen_cfg.get("temperature")},
        "git_head": git,
        "evaluation_set": "data/evaluation/questions.jsonl",
        "n_questions": len(questions),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    }
    with open(out / "config.json", "w", encoding="utf-8") as fh:
        json.dump(config, fh, ensure_ascii=False, indent=2)
    with open(out / "per_question.jsonl", "w", encoding="utf-8") as fh:
        for r in per_question:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    with open(out / "metrics.json", "w", encoding="utf-8") as fh:
        json.dump(metrics, fh, ensure_ascii=False, indent=2)

    # ---- 摘要 ----
    print("\n================ 实验摘要 ================")
    print(f"实验方法: {method_label} | fixed_512/80 | top_k={top_k} | git={git} | 产物: {args.out}")
    print(f"检索指标: Hit@1={retrieval['hit@1']:.3f} Hit@3={retrieval['hit@3']:.3f} "
          f"Hit@5={retrieval['hit@5']:.3f} MRR={retrieval['mrr']:.3f} (可答题 {retrieval['n_answered']})")
    print(f"生成(真实检索): 引用正确率={gen_real['citation_accuracy']:.3f} "
          f"真拒答率={gen_real['true_refusal_rate']:.3f} 误拒答率={gen_real['false_refusal_rate']:.3f} "
          f"应拒未拒={gen_real['should_have_refused']} 平均延迟={gen_real['avg_latency']:.2f}s")
    print(f"生成(神谕):     引用正确率={gen_oracle['citation_accuracy']:.3f} "
          f"误拒答率={gen_oracle['false_refusal_rate']:.3f} 平均延迟={gen_oracle['avg_latency']:.2f}s")
    if rerank_summary:
        print(f"重排(粗排{retrieval_cfg.get('top_k')}→精排top{retrieval_cfg.get('final_top_k', top_k)}):"
              f" 正确chunk排名上升={rerank_summary['gold_moved_up']} "
              f"下降={rerank_summary['gold_moved_down']} "
              f"不变={rerank_summary['gold_stayed']} "
              f"未进粗排top={rerank_summary['gold_not_in_top']}")
    print(f"归因提示: 真实 vs 神谕引用正确率差距 = 检索失败贡献;"
          f"神谕本身低 → 评估集标注或生成问题(不自动改结论)")


if __name__ == "__main__":
    main()
