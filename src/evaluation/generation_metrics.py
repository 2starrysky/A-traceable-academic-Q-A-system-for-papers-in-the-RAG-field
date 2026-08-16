"""生成指标:引用正确率(论文+章节双层)、拒答拆分(真/误)、指标汇总。

章节判定按相关 chunk:引用 chunk 的 section 与任一相关 chunk 的 section
"章节号前缀相等或字符串相等"(如 5 vs 5.2)。引用正确 = 论文对 且 章节对。
引用正确率的分母 = 作答的可答题(拒答不计入);拒答由真/误拒答率覆盖。
"""
from __future__ import annotations

import re

_SECTION_NUM_RE = re.compile(r"^([0-9]+|[IVXivx]+)")


def section_num(s: str) -> str | None:
    m = _SECTION_NUM_RE.match(s or "")
    return m.group(1) if m else None


def section_match(cit_section: str, gold_section: str) -> bool:
    if cit_section == gold_section:
        return True
    cn, gn = section_num(cit_section), section_num(gold_section)
    return bool(cn and gn and cn == gn)


def citation_correct(citation, gold_paper_id: str, gold_chunk_ids,
                     gold_sections) -> bool:
    """双层判定。citation 为 RetrievalHit(有 paper_id/section/chunk_id)。"""
    if citation.paper_id != gold_paper_id:
        return False
    if citation.chunk_id in set(gold_chunk_ids):
        return True
    return any(section_match(citation.section, gs) for gs in gold_sections)


def classify_refusal(refused: bool, answerable: bool) -> str:
    """拒答四分类:true_refusal(无答案+拒答,正确)/false_refusal(有答案+拒答,检索失败)
    /answered_ok(有答案+作答)/should_have_refused(无答案但作答,错误)。"""
    if refused:
        return "true_refusal" if not answerable else "false_refusal"
    return "answered_ok" if answerable else "should_have_refused"


def compute_generation_metrics(records) -> dict:
    """汇总生成指标。

    records: list[dict],每项含 answerable/refused/citation_correct(作答且可答时)/latency。
    返回:citation_accuracy(作答可答题中引用正确比例)/true_refusal_rate/false_refusal_rate/
    should_have_refused 数/avg_latency/n_answerable/n_unanswerable。
    """
    n_ans = n_una = n_true_ref = n_false_ref = n_should = 0
    answered = corr = 0
    lat_sum = 0.0
    for r in records:
        if r.get("latency") is not None:
            lat_sum += r["latency"]
        if r["answerable"]:
            n_ans += 1
            if r["refused"]:
                n_false_ref += 1
            else:
                answered += 1
                if r.get("citation_correct"):
                    corr += 1
        else:
            n_una += 1
            if r["refused"]:
                n_true_ref += 1
            else:
                n_should += 1
    return {
        "citation_accuracy": corr / answered if answered else 0.0,
        "true_refusal_rate": n_true_ref / n_una if n_una else 0.0,
        "false_refusal_rate": n_false_ref / n_ans if n_ans else 0.0,
        "should_have_refused": n_should,
        "avg_latency": lat_sum / len(records) if records else 0.0,
        "n_answerable": n_ans,
        "n_unanswerable": n_una,
    }
