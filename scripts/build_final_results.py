"""重建 final_results.csv:横比 E1~E6,数值全部取最新一致产物。"""
import csv
import json
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

FIELDS = ["experiment", "retriever", "chunking", "top_k", "rerank", "hit@1", "hit@3",
          "hit@5", "mrr", "citation_accuracy", "faithfulness", "true_refusal_rate",
          "false_refusal_rate", "should_have_refused", "avg_latency_s", "note"]


def row(**kw):
    d = {f: "" for f in FIELDS}
    d.update(kw)
    return d


rows = []
# E1~E4
for e, lab, tk, rk in [("e01_dense_v2", "E1 Dense", 5, "no"),
                       ("e02_bm25", "E2 BM25", 5, "no"),
                       ("e03_hybrid", "E3 Hybrid", 5, "no"),
                       ("e04_hybrid_rerank", "E4 Hybrid+Rerank", "20→5", "yes")]:
    d = json.load(open(f"outputs/experiments/{e}/metrics.json", encoding="utf-8"))
    r = d["retrieval"]
    g = d["generation_real"]
    rows.append(row(experiment=lab, retriever=lab.split()[-1].lower().replace("+", "_"),
                    chunking="fixed_512_80", top_k=tk, rerank=rk,
                    **{"hit@1": round(r["hit@1"], 4), "hit@3": round(r["hit@3"], 4),
                       "hit@5": round(r["hit@5"], 4), "mrr": round(r["mrr"], 4)},
                    citation_accuracy=round(g["citation_accuracy"], 4),
                    faithfulness=round(g["citation_accuracy"], 4),
                    true_refusal_rate=round(g["true_refusal_rate"], 4),
                    false_refusal_rate=round(g["false_refusal_rate"], 4),
                    should_have_refused=g["should_have_refused"],
                    avg_latency_s=round(g["avg_latency"], 2)))

# E5 切块(章节级检索)
e5 = json.load(open("outputs/experiments/e05_chunk_ablation/summary.json", encoding="utf-8"))
for s, chunk, note in [("fixed_256_50", "fixed_256_50", "E5切块(章节级),256/50"),
                       ("fixed_512_80", "fixed_512_80", "E5切块(章节级),当前最佳"),
                       ("section_aware", "section_aware", "E5切块(章节级),0跨章但检索略弱")]:
    v = e5["strategies"][s]
    rows.append(row(experiment="E5 " + s, retriever="dense", chunking=chunk, top_k=5, rerank="no",
                    **{"hit@1": v["hit@1"], "hit@3": v["hit@3"], "hit@5": v["hit@5"], "mrr": v["mrr"]},
                    avg_latency_s=v["avg_latency"], note=note))

# E6 纯检索
e6 = json.load(open("outputs/experiments/e06_topk/summary.json", encoding="utf-8"))
for tk in (3, 5, 8):
    v = e6["strategies"][f"top{tk}"]
    rows.append(row(experiment=f"E6 Top-K={tk}", retriever="dense", chunking="fixed_512_80",
                    top_k=tk, rerank="no",
                    **{"hit@1": v["hit@1"], "hit@3": v["hit@3"], "hit@5": v["hit@5"], "mrr": v["mrr"]},
                    avg_latency_s=v["avg_latency"], note="RQ3 Top-K消融(纯检索)"))

# E6 生成侧(最新逐个跑结果)
for tk in (3, 5, 8):
    d = json.load(open(f"outputs/experiments/e06_topk/top{tk}_generation/metrics.json", encoding="utf-8"))
    g = d["generation_real"]
    rows.append(row(experiment=f"E6 Top-K={tk}(生成)", retriever="dense", chunking="fixed_512_80",
                    top_k=tk, rerank="no",
                    citation_accuracy=round(g["citation_accuracy"], 4),
                    faithfulness=round(d["faithfulness"], 4) if d.get("faithfulness") is not None else "",
                    true_refusal_rate=round(g["true_refusal_rate"], 4),
                    false_refusal_rate=round(g["false_refusal_rate"], 4),
                    should_have_refused=g["should_have_refused"],
                    avg_latency_s=round(g["avg_latency"], 2), note="北极星(引用/拒答/延迟)"))

with open("outputs/experiments/final_results.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=FIELDS)
    w.writeheader()
    w.writerows(rows)

print(f"final_results.csv rebuilt, rows={len(rows)}")
for r in csv.DictReader(open("outputs/experiments/final_results.csv", encoding="utf-8")):
    print(f"{r['experiment']:<24}top{r['top_k']:<6}hit1 {r['hit@1']:<7}mrr {r['mrr']:<8}"
          f"cit {r['citation_accuracy']:<8}false_ref {r['false_refusal_rate']:<8}{r['note']}")