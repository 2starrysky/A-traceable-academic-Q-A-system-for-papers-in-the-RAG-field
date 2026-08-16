"""评估集落盘:读 candidates.json(题目/建议答案)+ retrieval_results.json(建议相关 chunk)→ questions.jsonl + 校验。

schema:question/answerable/reference_answer/relevant_chunk_ids/paper_id/section/type。
铁律:本脚本只组装'已由用户确认'的数据;候选值是用户确认前的建议,确认后才是定稿。
无答案题(answerable=false)省略 paper_id/section/reference_answer/relevant_chunk_ids。
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

_CANDIDATES = ROOT / "data" / "evaluation" / "candidates.json"
_RESULTS = ROOT / "data" / "evaluation" / "retrieval_results.json"
_OUT = ROOT / "data" / "evaluation" / "questions.jsonl"
_CHUNKS = ROOT / "data" / "processed" / "chunks_fixed.jsonl"

_TYPE_QUOTA = {"fact": 15, "method": 10, "comparison": 10, "cross_section": 5, "unanswerable": 10}


def _load_jsonl_chunk_ids(path: Path) -> set[str]:
    ids = set()
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                ids.add(json.loads(line)["chunk_id"])
    return ids


def main() -> None:
    with open(_CANDIDATES, encoding="utf-8") as fh:
        candidates = json.load(fh)["questions"]
    with open(_RESULTS, encoding="utf-8") as fh:
        results = {r["id"]: r for r in json.load(fh)}
    known_chunk_ids = _load_jsonl_chunk_ids(_CHUNKS)

    errors: list[str] = []
    rows: list[dict] = []
    for q in candidates:
        qid = q["id"]
        if q["type"] == "unanswerable":
            if q.get("answerable") is not False:
                errors.append(f"{qid}: 无答案题 answerable 应为 false")
            rows.append({"id": qid, "type": q["type"], "question": q["question"], "answerable": False})
            continue
        if q.get("answerable") is not True:
            errors.append(f"{qid}: 可答题 answerable 应为 true")
        r = results.get(qid)
        relevant = list(r["suggested_chunk_ids"]) if r else []
        if not relevant:
            errors.append(f"{qid}: relevant_chunk_ids 为空")
        for cid in relevant:
            if cid not in known_chunk_ids:
                errors.append(f"{qid}: chunk_id {cid} 不在 chunks_fixed.jsonl")
        if len(relevant) != len(set(relevant)):
            errors.append(f"{qid}: relevant_chunk_ids 有重复")
        rows.append({
            "id": qid,
            "type": q["type"],
            "question": q["question"],
            "answerable": True,
            "paper_id": q["paper_id"],
            "section": q["section"],
            "reference_answer": q["reference_answer"],
            "relevant_chunk_ids": relevant,
        })

    # 全局校验:数量与配额
    if len(rows) != 50:
        errors.append(f"总数 {len(rows)} != 50")
    counts = {}
    for r in rows:
        counts[r["type"]] = counts.get(r["type"], 0) + 1
    for t, expect in _TYPE_QUOTA.items():
        if counts.get(t, 0) != expect:
            errors.append(f"type {t} 数量 {counts.get(t, 0)} != {expect}")

    if errors:
        print("校验失败:")
        for e in errors:
            print("  -", e)
        sys.exit(1)

    with open(_OUT, "w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"落盘成功:{len(rows)} 题 → {_OUT}")
    print(f"类型分布:{counts}")
    print(f"可答题相关 chunk 总数:"
          f"{sum(len(r['relevant_chunk_ids']) for r in rows if r['answerable'])}")


if __name__ == "__main__":
    main()
