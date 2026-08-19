"""切块无关的"相关"判定:章节级(section-level)。

为什么用章节而不是 chunk_id / 文本:
- chunk_id 绑定 512/80 fixed,换了切法(id 全变)直接对不上 → 不公平;
- chunk 文本是"跨原始段落切"拼接而成,与任何单一段落都不精确相等,
  文本包含/段落覆盖口径在 fixed 自身上也成立率不足 30% → 不可靠。

章节(section)每个 chunk 都自带、且不随切块大小改变主归属,是唯一真正
"切块无关"的公平口径。判定 = 检索 chunk 的主 section 与任一 gold chunk 的
主 section 在"章节号前缀"上一致(如 5 与 5.2 算同章),复用 Day 11 的
section_match 逻辑。

接口命中(hit)判定:retrieved chunk 的 section 与 gold chunk 集合中任一
chunk 的 section section_match 即为命中。与 generation_metrics 的双层判定
前半段(章节)一致,可保证跨切法可比。
"""
from __future__ import annotations

import re

from src.evaluation.generation_metrics import section_match

_SECTION_NUM_RE = re.compile(r"^([0-9]+|[IVXivx]+)")


def section_num(s: str) -> str | None:
    m = _SECTION_NUM_RE.match(s or "")
    return m.group(1) if m else None


def section_hit(retrieved_section: str, gold_sections: set[str]) -> bool:
    """retrieved chunk 的主 section 是否与任一 gold section 同章(前缀匹配)。"""
    return any(section_match(retrieved_section, gs) for gs in gold_sections)