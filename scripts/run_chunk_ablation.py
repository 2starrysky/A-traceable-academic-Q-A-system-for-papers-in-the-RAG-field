"""E5 切块消融实验:比较 fixed 256/50、fixed 512/80、section-aware 三种切块策略。

控制变量(仅"切块"变化,其余全部不变):Dense 检索(bge-m3)、Top-K=5、
生成模型(deepseek-chat)、评估集(同一 50 题)。每切法各自用 bge-m3 重建稠密索引。

判定口径(切块无关):评估集 gold chunk_id 绑定 fixed 512/80,换了切法 id 序列不同、
chunk 边界也不同;且 chunk 文本是"跨原始段落切"拼接而成,无法与任何单段精确对齐。
故采用章节级(section)金标准——每个 chunk 自带主 section,不随切块大小改变,是唯一
真正公平的口径:检索到的 chunk 主 section 与任一 gold chunk 主 section 在章节号前缀
上一致即命中。gold 章节集从 canonical(fixed 512/80)chunk 算一次、所有策略共用,
保证跨切法公平。

产物 outputs/experiments/e05_chunk_ablation/ 下分 <策略>/,含 config/per_question/metrics;
外加 summary.json 横比三切法,便于直接画论文图。
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

from src.evaluation import chunk_metrics
from src.retrieval.dense import DenseRetriever

_QUESTIONS = ROOT / "data" / "evaluation" / "questions.jsonl"
_FIXED512_IDX = "data/processed/dense_index"

# 三切法:名称 → (chunking, chunk_size, overlap, index_path)
_STRATEGIES = [
    ("fixed_256_50", "fixed", 256, 50, "data/processed/idx_fixed_sz256_ov50"),
    ("fixed_512_80", "fixed", 512, 80, _FIXED512_IDX),
    ("section_aware", "section_aware", 512, 80, "data/processed/idx_section_aware_sz512_ov80"),
]

_DEFAULT_OUT = "outputs/experiments/e05_chunk_ablation"
_CANONICAL_CHUNKS = "data/processed/chunks_fixed.jsonl"  # 评估集 gold 基于此

_CHUNK_MAP = {
    "fixed_256_50": "data/processed/chunks_fixed_sz256_ov50.jsonl",
    "fixed_512_80": "data/processed/chunks_fixed.jsonl",
    "section_aware": "data/processed/chunks_section_aware.jsonl",
}


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


def _canonical_gold_sections(questions: list[dict]) -> list[set]:
    """从 canonical(fixed 512/80)chunk 算每可答题的 gold 章节集,所有策略共用。

    章节号取前缀(如 5 / 5.2 → "5"),保证跨切法用同一套"正确答案章节"。
    """
    chunks = _load_chunks(ROOT / _CANONICAL_CHUNKS)
    gold_by_q: list[set] = []
    for q in questions:
        secs: set = set()
        if q.get("answerable"):
            for cid in q.get("relevant_chunk_ids", []):
                c = chunks.get(cid)
                if c:
                    secs.add(chunk_metrics.section_num(c.get("section", "")) or c.get("section", ""))
        gold_by_q.append(secs)
    return gold_by_q


def _sec_of(chunk_dict_or_hit) -> str | None:
    """从 chunk dict 或 RetrievalHit 取章节号前缀。"""
    sec = chunk_dict_or_hit.get("section") if hasattr(chunk_dict_or_hit, "get") else chunk_dict_or_hit.section
    return chunk_metrics.section_num(sec)


def _run_strategy(strategy: str, idx_path: str, questions: list[dict],
                  top_k: int, gold_by_question: list[set],
                  device=None) -> tuple[dict, list[dict]]:
    print(f"\n========= 策略: {strategy} (索引 {idx_path}) =========")
    chunks = _load_chunks(ROOT / _CHUNK_MAP[strategy])
    print(f"加载索引 {idx_path} ({len(chunks)} chunks) ...")
    retriever = DenseRetriever.load(ROOT / idx_path, device=device)

    per_question: list[dict] = []
    for i, q in enumerate(questions, 1):
        answerable = bool(q.get("answerable"))
        gold_secs = gold_by_question[i - 1]  # 与策略无关的 canonical gold 章节集

        t0 = time.time()
        hits = retriever.search(q["question"], top_k=top_k)
        lat = time.time() - t0

        retrieved_ids = [h.chunk_id for h in hits]
        # 章节级命中(切块无关):命中对象自带 .section
        retrieved_secs = {_sec_of(h) for h in hits if _sec_of(h)}
        hit = bool(answerable and gold_secs and (retrieved_secs & gold_secs))

        per_question.append({
            "id": q["id"], "type": q["type"], "question": q["question"],
            "answerable": answerable,
            "retrieved": [{"chunk_id": cid, "section": _sec_of(chunks[cid]),
                           "score": round(h.score, 4)}
                          for cid, h in zip(retrieved_ids, hits)],
            "gold_sections": sorted(gold_secs) if gold_secs else [],
            "hit": hit,
            "latency": round(lat, 3),
        })
        if i % 50 == 0:
            print(f"  完成 {i}/{len(questions)}")

    # ---- 章节级检索指标(切块无关):统一用"章节号前缀集合"比较 ----
    def _in_gold(ids, gs, k):
        return any(_sec_of(chunks[cid]) in gs for cid in ids[:k])

    def _first_rank(ids, gs):
        for rank, cid in enumerate(ids, 1):
            if _sec_of(chunks[cid]) in gs:
                return rank
        return None

    ks = (1, 3, 5)
    hit_cnt = {k: 0 for k in ks}
    mrr_sum = 0.0
    answered = 0
    for q, gs, rec in zip(questions, gold_by_question, per_question):
        if not q.get("answerable") or not gs:
            continue
        answered += 1
        ids = [r["chunk_id"] for r in rec["retrieved"]]
        for k in ks:
            hit_cnt[k] += 1 if _in_gold(ids, gs, k) else 0
        rank = _first_rank(ids, gs)
        if rank is not None:
            mrr_sum += 1.0 / rank

    retrieval_section = {
        f"hit@{k}": hit_cnt[k] / answered if answered else 0.0 for k in ks
    }
    retrieval_section["mrr"] = mrr_sum / answered if answered else 0.0
    retrieval_section["n_answered"] = answered

    correct = sum(1 for r in per_question if r["hit"])
    hit_accuracy = correct / answered if answered else 0.0
    lats = [r["latency"] for r in per_question]

    metrics = {
        "strategy": strategy,
        "retrieval_section": {**retrieval_section, "section_hit_accuracy": hit_accuracy},
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
    out = ROOT / args.out
    if out.exists():
        print(f"ERROR 输出目录已存在(不覆盖旧实验): {out}", file=sys.stderr)
        sys.exit(1)

    questions = _read_questions()
    if len(questions) != 50:
        print(f"ERROR 评估集 {len(questions)} 题 != 50", file=sys.stderr)
        sys.exit(1)

    gold_by_q = _canonical_gold_sections(questions)
    n_gold = sum(1 for gs in gold_by_q if gs)
    print(f"canonical gold 章节集(基于 fixed 512/80):{n_gold}/40 可答题有 gold")

    out.mkdir(parents=True)
    git = _git_head()
    t_start = time.time()
    summary = {
        "experiment": "E5_chunk_ablation",
        "fixed": {"embedding_model": "BAAI/bge-m3", "retriever": "dense",
                  "top_k": args.top_k, "evaluation_set": str(_QUESTIONS.relative_to(ROOT)),
                  "judgement": "section-level (chunking-independent)",
                  "gold_sections_source": _CANONICAL_CHUNKS},
        "git_head": git,
        "n_questions": len(questions),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "strategies": {},
    }

    for strategy, chunking, cs, ov, idx_path in _STRATEGIES:
        metrics = None
        per_q: list[dict] = []
        try:
            metrics, per_q = _run_strategy(strategy, idx_path, questions,
                                           args.top_k, gold_by_q, device=args.device)
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

        rs = (metrics or {}).get("retrieval_section") or {}
        summary["strategies"][strategy] = {
            "section_hit_accuracy": rs.get("section_hit_accuracy"),
            "hit@1": rs.get("hit@1"), "hit@3": rs.get("hit@3"),
            "hit@5": rs.get("hit@5"), "mrr": rs.get("mrr"),
            "avg_latency": (metrics or {}).get("avg_latency"),
        }

    summary["total_time_sec"] = round(time.time() - t_start)
    with open(out / "summary.json", "w", encoding="utf-8") as fh:
        json.dump(summary, fh, ensure_ascii=False, indent=2)

    print("\n================ E5 切块消融摘要 ================")
    print(f"git={git} | Top-K={args.top_k} | 判定=章节级(切块无关)")
    print(f"{'策略':<16}{'命中率':>8}{'Hit@1':>8}{'Hit@3':>8}{'Hit@5':>8}{'MRR':>8}{'延迟s':>10}")
    for s, v in summary["strategies"].items():
        def fmt(x): return f"{x:>8.3f}" if isinstance(x, float) else f"{0:>8.3f}"
        print(f"{s:<16}{fmt(v.get('section_hit_accuracy'))}{fmt(v.get('hit@1'))}"
              f"{fmt(v.get('hit@3'))}{fmt(v.get('hit@5'))}{fmt(v.get('mrr'))}"
              f"{v.get('avg_latency') or 0:>10.2f}")
    print(f"总用时 {summary['total_time_sec']}s | 产物: {out}")


if __name__ == "__main__":
    main()