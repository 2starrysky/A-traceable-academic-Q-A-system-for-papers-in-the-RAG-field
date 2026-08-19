"""E5 切块消融实验:比较 fixed 256/50、fixed 512/80、section-aware 三种切块策略。

控制变量(仅"切块"变化,其余全部不变):Dense 检索(bge-m3)、Top-K=5、
生成模型(deepseek-chat)、评估集(同一 50 题)。每切法各自用 bge-m3 重建稠密索引。

判定口径(切块无关):评估集 gold chunk_id 绑定 512/80 fixed,换了切法 id 全对不上;
且 chunk 文本是"跨原始段落切"拼接而成,无法与任何单段精确对齐(文本/段落包含口径
在 fixed 自身上也 <30%)。故采用章节级(section)金标准——每个 chunk 自带主 section,
不随切块大小改变,是唯一真正公平的口径:检索 chunk 的主 section 与任一 gold chunk
的主 section 在章节号前缀上一致即命中(src.evaluation.chunk_metrics.section_hit)。

产物 outputs/experiments/e05_chunk_ablation/ 下分 <策略>/,含 config/per_question/metrics;
外加一份 summary.json 横比三切法,便于直接画论文图。
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

from src.evaluation import chunk_metrics, generation_metrics, retrieval_metrics
from src.generation.generator import create_generator
from src.retrieval.dense import DenseRetriever, RetrievalHit

_QUESTIONS = ROOT / "data" / "evaluation" / "questions.jsonl"
_FIXED512_IDX = "data/processed/dense_index"

# 三切法:名称 → (chunking, chunk_size, overlap, index_path)
# 512/80 索引现成;256/50 与 section-aware 索引由 build_chunk_index.py 产出
_STRATEGIES = [
    ("fixed_256_50", "fixed", 256, 50, "data/processed/idx_fixed_sz256_ov50"),
    ("fixed_512_80", "fixed", 512, 80, _FIXED512_IDX),
    ("section_aware", "section_aware", 512, 80, "data/processed/idx_section_aware_sz512_ov80"),
]

_DEFAULT_OUT = "outputs/experiments/e05_chunk_ablation"


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


def _load_chunks(path: Path) -> dict[str, dict]:
    chunks = {}
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                r = json.loads(line)
                chunks[r["chunk_id"]] = r
    return chunks


def _find_chunk_records(strategy: str) -> dict[str, dict]:
    """按策略名找到对应 chunk JSONL(含命名规则),返回 id→记录。"""
    mapping = {
        "fixed_256_50": "data/processed/chunks_fixed_sz256_ov50.jsonl",
        "fixed_512_80": "data/processed/chunks_fixed.jsonl",
        "section_aware": "data/processed/chunks_section_aware.jsonl",
    }
    p = ROOT / mapping[strategy]
    if not p.exists():
        raise FileNotFoundError(f"缺少 chunk 文件(请先 build_chunk_index): {p}")
    return _load_chunks(p)


def _build_gold_sections(q: dict, chunks: dict[str, dict]) -> set[str]:
    """gold section 集合(章节号前缀),用于章节级命中判定。"""
    secs: set[str] = set()
    for cid in q.get("relevant_chunk_ids", []):
        c = chunks.get(cid)
        if c:
            secs.add(chunk_metrics.section_num(c.get("section", "")) or c.get("section", ""))
    return secs


def _run_strategy(strategy: str, idx_path: str, questions: list[dict],
                  gen_cfg: dict, top_k: int, device=None) -> dict:
    print(f"\n========= 策略: {strategy} (索引 {idx_path}) =========")
    chunks = _find_chunk_records(strategy)
    print(f"加载索引 {idx_path} ({len(chunks)} chunks) ...")
    retriever = DenseRetriever.load(ROOT / idx_path, device=device)

    generator = create_generator(
        provider=gen_cfg.get("provider", "deepseek"),
        model=gen_cfg.get("llm_model"),
        base_url=gen_cfg.get("base_url"),
        temperature=gen_cfg.get("temperature", 0.2),
    )

    per_question: list[dict] = []
    preds = []          # chunk_id 序列(按检索排名)
    gold_sects = []     # 每题 gold section 集合
    for i, q in enumerate(questions, 1):
        answerable = bool(q.get("answerable"))
        gold_secs = _build_gold_sections(q, chunks) if answerable else set()
        gold_sects.append(gold_secs)

        t0 = time.time()
        hits = retriever.search(q["question"], top_k=top_k)
        gen = generator.generate(q["question"], hits)
        lat = time.time() - t0

        retrieved_ids = [h.chunk_id for h in hits]
        preds.append(retrieved_ids)

        # 章节级命中(切块无关)
        retrieved_secs = {chunk_metrics.section_num(chunks[h]["section"])
                          for h, ch in zip(hits, [chunks.get(cid) for cid in retrieved_ids])
                          if ch and chunk_metrics.section_num(ch["section"])}
        hit = bool(answerable and gold_secs and (retrieved_secs & gold_secs))

        record = {
            "id": q["id"], "type": q["type"], "question": q["question"],
            "answerable": answerable,
            "retrieved": [{"chunk_id": h.chunk_id, "section": h.section,
                           "score": round(h.score, 4)} for h in hits],
            "gold_sections": sorted(gold_secs) if gold_secs else [],
            "hit": hit,
            "latency": round(lat, 3),
            "answer": gen.text,
            "refused": gen.refused,
        }
        per_question.append(record)
        if i % 10 == 0:
            print(f"  完成 {i}/{len(questions)}")

    # 章节级检索指标:gold = 每题 gold 集合里"章节匹配"的 chunk_id
    gold_for_retrieval = []
    for q, gs in zip(questions, gold_sects):
        if not q.get("answerable"):
            gold_for_retrieval.append([])
            continue
        matched = [cid for cid in q.get("relevant_chunk_ids", [])
                   if cid in chunks and
                   chunk_metrics.section_match(chunks[cid].get("section", ""), gs)]
        # gs 已是章节号前缀;这里用 gold chunk 自身 section 与检索章节匹配即可
        # 简化:gold_ids = 该策略下 section 命中 gold 的 chunk(用检索 side 同口径)
        gold_for_retrieval.append([])  # 占位,下面用自定义算
    # 自定义 Hit@K / MRR(章节级)
    def _gold_chunk_ids_by_section(q, gs):
        return [cid for cid in q.get("relevant_chunk_ids", [])
                if cid in chunks and chunk_metrics.section_num(chunks[cid].get("section", "")) in gs]
    golds = [_gold_chunk_ids_by_section(q, gs) if q.get("answerable") else []
             for q, gs in zip(questions, gold_sects)]
    retrieval = retrieval_metrics.evaluate_retrieval(preds, golds, ks=(1, 3, 5))

    # 章节命中准确率(切块无关的主指标)
    answered = sum(1 for q in questions if q.get("answerable"))
    correct = sum(1 for r in per_question if r["hit"])
    hit_accuracy = correct / answered if answered else 0.0

    # 延迟汇总(拒答/引用正确率在切块消融中不具可比性:引用正确率依赖 chunk_id 对齐,
    # 而 chunk_id 随切法变化;拒答可由模型保守性主导、不反映切块差异)。主指标=章节命中。
    lats = [r["latency"] for r in per_question]
    metrics = {
        "strategy": strategy,
        "retrieval_section": {
            "hit_at_1": retrieval["hit@1"],
            "hit_at_3": retrieval["hit@3"],
            "hit_at_5": retrieval["hit@5"],
            "mrr": retrieval["mrr"],
            "section_hit_accuracy": hit_accuracy,
            "n_answered": answered,
        },
        "avg_latency": sum(lats) / len(lats) if lats else 0.0,
    }
    return metrics, per_question


def main() -> None:
    import argparse
    ap = argparse.ArgumentParser(description="E5 切块消融:比较三切法(Dense/Top-K/评估集不变)")
    ap.add_argument("--config", default="configs/dense.yaml")
    ap.add_argument("--out", default=_DEFAULT_OUT)
    ap.add_argument("--top-k", type=int, default=5)
    ap.add_argument("--device", default=None)
    args = ap.parse_args()

    with open(ROOT / args.config, encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh) or {}
    gen_cfg = (cfg.get("retrieval") or {}).get("generation", {})
    out = ROOT / args.out
    if out.exists():
        print(f"ERROR 输出目录已存在(不覆盖旧实验): {out}", file=sys.stderr)
        sys.exit(1)

    questions = _read_questions()
    if len(questions) != 50:
        print(f"ERROR 评估集 {len(questions)} 题 != 50", file=sys.stderr)
        sys.exit(1)

    out.mkdir(parents=True)
    git = _git_head()
    t_start = time.time()
    summary = {
        "experiment": "E5_chunk_ablation",
        "fixed": {"embedding_model": "BAAI/bge-m3", "retriever": "dense",
                  "top_k": args.top_k, "evaluation_set": str(_QUESTIONS.relative_to(ROOT)),
                  "judgement": "section-level (chunking-independent)"},
        "git_head": git,
        "n_questions": len(questions),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "strategies": {},
    }

    for strategy, chunking, cs, ov, idx_path in _STRATEGIES:
        metrics = None
        per_q: list[dict] = []
        try:
            metrics, per_q = _run_strategy(strategy, idx_path, questions, gen_cfg,
                                           args.top_k, device=args.device)
        except Exception as e:
            print(f"ERROR 策略 {strategy} 失败: {e}", file=sys.stderr)
            metrics = {"strategy": strategy, "error": str(e)}

        sdir = out / strategy
        sdir.mkdir(parents=True, exist_ok=True)
        with open(sdir / "metrics.json", "w", encoding="utf-8") as fh:
            json.dump(metrics, fh, ensure_ascii=False, indent=2)
        with open(sdir / "per_question.jsonl", "w", encoding="utf-8") as fh:
            for r in per_q:
                fh.write(json.dumps(r, ensure_ascii=False) + "\n")
        with open(sdir / "config.json", "w", encoding="utf-8") as fh:
            json.dump({"strategy": strategy, "chunking": chunking, "chunk_size": cs,
                       "overlap": ov, "index_path": idx_path,
                       "retriever": "dense", "top_k": args.top_k, "git_head": git},
                      fh, ensure_ascii=False, indent=2)
        summary["strategies"][strategy] = {
            k: metrics[k] for k in ("section_hit_accuracy", "hit_at_1", "hit_at_3", "hit_at_5",
                                     "mrr", "avg_latency")
            if k in metrics.get("retrieval_section", metrics)
        }
        # 兼容嵌套/扁平两种结构
        rs = metrics.get("retrieval_section") or {}
        if rs:
            summary["strategies"][strategy] = {
                "section_hit_accuracy": rs.get("section_hit_accuracy"),
                "hit@1": rs.get("hit_at_1"), "hit@3": rs.get("hit_at_3"),
                "hit@5": rs.get("hit_at_5"), "mrr": rs.get("mrr"),
                "avg_latency": metrics.get("avg_latency"),
            }

    summary["total_time_sec"] = round(time.time() - t_start)
    with open(out / "summary.json", "w", encoding="utf-8") as fh:
        json.dump(summary, fh, ensure_ascii=False, indent=2)

    print("\n================ E5 切块消融摘要 ================")
    print(f"git={git} | Top-K={args.top_k} | 判定=章节级(切块无关)")
    print(f"{'策略':<16}{'命中率':>8}{'Hit@1':>8}{'Hit@3':>8}{'Hit@5':>8}{'MRR':>8}{'延迟s':>10}")
    for s, v in summary["strategies"].items():
        print(f"{s:<16}{v.get('section_hit_accuracy',0):>8.3f}{v.get('hit@1',0):>8.3f}"
              f"{v.get('hit@3',0):>8.3f}{v.get('hit@5',0):>8.3f}"
              f"{v.get('mrr',0):>8.3f}{v.get('avg_latency',0):>10.2f}")
    print(f"总用时 {summary['total_time_sec']}s | 产物: {out}")


if __name__ == "__main__":
    main()