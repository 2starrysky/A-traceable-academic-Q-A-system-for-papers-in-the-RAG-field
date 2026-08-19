"""E6 生成侧(单 Top-K):某 top_k 带 LLM 跑北极星指标,产出 outputs/experiments/e06_topk/top{k}_generation/。

单独拆出,便于逐个 top_k 前台运行,避免 300 次 LLM 调用超时。
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
os.chdir(ROOT)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from scripts.run_topk_final import _load_chunks, _run_generation_topk
from src.retrieval.dense import DenseRetriever

_DENSE_IDX = "data/processed/dense_index"
_E6_OUT = "outputs/experiments/e06_topk"


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--top-k", type=int, required=True)
    args = ap.parse_args()

    with open(ROOT / "configs/dense.yaml", encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh) or {}
    gen_cfg = (cfg.get("retrieval") or {}).get("generation", {})

    print(f"加载索引 {_DENSE_IDX} ...", flush=True)
    retriever = DenseRetriever.load(ROOT / _DENSE_IDX)
    questions = [json.loads(l) for l in open(ROOT / "data/evaluation/questions.jsonl", encoding="utf-8") if l.strip()]
    chunks = _load_chunks()
    print(f"开始生成 Top-K={args.top_k}, {len(questions)} 题 ...", flush=True)

    metrics, per = _run_generation_topk(retriever, questions, chunks, gen_cfg, args.top_k)
    out = ROOT / _E6_OUT / f"top{args.top_k}_generation"
    out.mkdir(parents=True, exist_ok=True)
    with open(out / "metrics.json", "w", encoding="utf-8") as fh:
        json.dump(metrics, fh, ensure_ascii=False, indent=2)
    with open(out / "per_question.jsonl", "w", encoding="utf-8") as fh:
        for r in per:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")

    gr = metrics["generation_real"]
    print(f"\nDone Top-K={args.top_k}: 引用={gr['citation_accuracy']:.3f} "
          f"真拒={gr['true_refusal_rate']:.3f} 误拒={gr['false_refusal_rate']:.3f} "
          f"应拒未拒={gr['should_have_refused']} 延迟={gr['avg_latency']:.2f}s", flush=True)


if __name__ == "__main__":
    main()