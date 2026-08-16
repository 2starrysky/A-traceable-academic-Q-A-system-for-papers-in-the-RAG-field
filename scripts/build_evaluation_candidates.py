"""评估集候选处理:读 candidates.json → 对可答题跑 Dense 检索 → 生成建议相关 chunk + 确认文档。

产物:
- data/evaluation/retrieval_results.json:每题 top-8 检索命中(供人工核对)。
- data/evaluation/question_candidates.md:按类型分组的确认文档(铁律:答案/相关 chunk 待用户确认)。

建议相关 chunk 的启发:取检索命中里 paper_id 与题目主论文一致的 chunk(按相似度),其余命中全部列出供人工挑选。
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

from src.retrieval.dense import DenseRetriever

_CANDIDATES = ROOT / "data" / "evaluation" / "candidates.json"
_RESULTS = ROOT / "data" / "evaluation" / "retrieval_results.json"
_DOC = ROOT / "data" / "evaluation" / "question_candidates.md"
_INDEX = ROOT / "data" / "processed" / "dense_index"
TOP_K = 8
_PREVIEW = 160

_TYPE_LABEL = {
    "fact": "事实型(15)",
    "method": "方法理解型(10)",
    "comparison": "论文对比型(10)",
    "cross_section": "跨章节型(5)",
    "unanswerable": "无答案型(10)",
}


def _clip(text: str, n: int) -> str:
    return text if len(text) <= n else text[:n] + "…"


def _suggested_ids(hits, paper_id: str) -> list[str]:
    """启发式建议:与题目主论文一致的命中 chunk_id(按相似度序)。"""
    return [h.chunk_id for h in hits if h.paper_id == paper_id]


def main() -> None:
    with open(_CANDIDATES, encoding="utf-8") as fh:
        data = json.load(fh)
    questions = data["questions"]

    print(f"加载索引 {_INDEX} ...")
    retriever = DenseRetriever.load(_INDEX)
    print(f"处理 {len(questions)} 题(top_k={TOP_K})...")

    results = []
    for q in questions:
        qid = q["id"]
        if q["type"] == "unanswerable":
            results.append({"id": qid, "question": q["question"], "answerable": False, "hits": []})
            continue
        hits = retriever.search(q["question"], top_k=TOP_K)
        suggested = _suggested_ids(hits, q["paper_id"])
        results.append({
            "id": qid,
            "question": q["question"],
            "answerable": True,
            "paper_id": q["paper_id"],
            "suggested_chunk_ids": suggested,
            "hits": [
                {"chunk_id": h.chunk_id, "paper_id": h.paper_id, "title": h.title,
                 "section": h.section, "page_start": h.page_start, "page_end": h.page_end,
                 "score": round(h.score, 4), "text": h.text}
                for h in hits
            ],
        })

    with open(_RESULTS, "w", encoding="utf-8") as fh:
        json.dump(results, fh, ensure_ascii=False, indent=1)

    # 组装确认文档
    by_type = {t: [] for t in _TYPE_LABEL}
    for q in questions:
        by_type[q["type"]].append(q)
    res_by_id = {r["id"]: r for r in results}

    lines = [
        "# 评估集候选问题(50 题)——待人工确认",
        "",
        "> **铁律**:`answerable` / `reference_answer` / `relevant_chunk_ids` 由你人工确认,"
        "以下是 AI 建议值(候选),不得视为定稿。",
        "> **确认方式**:在对话中回复「第 X 题通过」,或「第 X 题答案应改为…/相关 chunk 应为…」。",
        "",
        "> 配额:事实 15 / 方法理解 10 / 论文对比 10 / 跨章节 5 / 无答案 10 = 50。",
        "",
    ]
    for t, label in _TYPE_LABEL.items():
        lines.append(f"## {label}")
        for q in by_type[t]:
            lines.append(f"### {q['id']} [{q['type']}]")
            lines.append(f"- 问题:{q['question']}")
            if q.get("answerable") is False:
                lines.append("- answerable: **false(无答案,知识库外)**")
                lines.append("- 建议:系统应拒答;无需 reference_answer/relevant_chunk_ids。")
                lines.append("")
                continue
            lines.append(f"- answerable: true")
            lines.append(f"- 建议论文/章节:{q['paper_id']} · {q.get('section')}")
            lines.append(f"- 建议标准答案:{q['reference_answer']}")
            r = res_by_id[q["id"]]
            sug = r["suggested_chunk_ids"]
            if sug:
                lines.append(f"- 建议相关 chunk({len(sug)}):{', '.join(sug)}")
            else:
                lines.append("- 建议相关 chunk:**⚠️ 检索未直接命中目标论文,请从下方命中中人工指定**")
            lines.append(f"- 检索 top-{len(r['hits'])}(供核对):")
            for h in r["hits"]:
                mark = "★" if h["chunk_id"] in sug else " "
                lines.append(
                    f"  - {mark} {h['chunk_id']} | {h['paper_id']} | {h['section']} | "
                    f"页{h['page_start']}-{h['page_end']} | sim {h['score']}"
                )
                lines.append(f"    原文:{_clip(h['text'], _PREVIEW)}")
            lines.append("")

    with open(_DOC, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))
    print(f"完成:检索结果 → {_RESULTS}")
    print(f"确认文档 → {_DOC}")
    print(f"建议相关 chunk 空(需人工指定)的题数: "
          f"{sum(1 for r in results if r['answerable'] and not r['suggested_chunk_ids'])}")


if __name__ == "__main__":
    main()
