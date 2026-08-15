"""文本清洗与章节结构标注:去页眉页脚/页码/arXiv 戳记、合并断行连字符、折叠空白,并把正文切分成带 section 的段落。"""
from __future__ import annotations

import re
from collections import Counter
from typing import Iterable

_ARXIV_STAMP_RE = re.compile(
    r"^arXiv:\d{4}\.\d{4,5}(v\d+)?\s+\[[^\]]+\]\s+\d{1,2}\s+[A-Za-z]{3,9}\s+\d{4}$"
)
_PAGE_NUM_RE = re.compile(r"^\d{1,3}$")
_DIGIT_RE = re.compile(r"\d+")
_CTRL_RANGE_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")
_CTRL_CHARS = frozenset(
    {chr(c) for c in range(0x200B, 0x2010)}
    | {chr(c) for c in range(0x202A, 0x202F)}
    | {chr(0xFEFF)}
)
_SPACES_RE = re.compile(r"[ \t\xa0]+")
# 行尾连字符 + 换行 + 小写/数字开头 → 断行拼接(大写开头视为真实换行)
_HYPHEN_JOIN_RE = re.compile(r"-\n(?=[a-z0-9])")
# 满行 + 行尾句末标点(可带引号/括号/尖括号)→ 段落结束
_PARA_END_RE = re.compile(r"[.!?]['\")\]>]*$")
_HEADER_MAX_LEN = 90

_LIGATURES = {
    "ﬀ": "ff", "ﬁ": "fi", "ﬂ": "fl",
    "ﬃ": "ffi", "ﬄ": "ffl",
}

# 无编号章节标题白名单(整行匹配,忽略尾部冒号)
_NAMED_SECTIONS = {
    "abstract", "introduction", "related work", "background", "preliminaries",
    "method", "methods", "methodology", "approach", "model", "models",
    "framework", "experiments", "experimental setup", "evaluation", "results",
    "conclusion", "conclusions", "discussion", "limitations", "broader impact",
    "acknowledgments", "acknowledgements", "references", "appendix",
    "overview", "architecture",
}
# 编号无点时的已知章节首词(单数/复数都要,避免把年份行误判为标题)
_KNOWN_HEADING_WORDS = {
    "introduction", "related", "background", "preliminaries", "method",
    "methods", "methodology", "approach", "model", "models", "framework",
    "training", "experiment", "experiments", "experimental", "evaluation",
    "results", "result", "conclusion", "conclusions", "discussion",
    "limitations", "acknowledgments", "acknowledgements", "references",
    "appendix", "overview", "architecture", "setup", "system", "data",
}

# 层级编号(如 "2.1 Models" / "5.3 Qualitative Analysis"):靠结构识别;标题不含逗号,避免参考文献条目误判
_NUM_SECTION_RE = re.compile(r"^\d+(?:\.\d+)+\.?\s+[A-Z][^,\n]*$")
# 单层编号(如 "3 Method" / "2 RELATED WORK"):标题首词必须命中词表,避免列表项/年份行误判
_NUM_SECTION_WORD_RE = re.compile(
    r"^\d+(?:\.\d+)*\.?\s+([A-Z][\w\-]+(?:\s+[A-Z][\w\-]+){0,4})$"
)
# 罗马数字编号(如 "I. INTRODUCTION"):不含逗号,避免参考文献条目("X. Bresson, ...")误判
_ROMAN_SECTION_RE = re.compile(
    r"^(?:I{1,3}|IV|V|VI{0,3}|IX|X)\.\s+[A-Z][\w/'\&\- ]*$"
)


def expand_ligatures(text: str) -> str:
    return "".join(_LIGATURES.get(c, c) for c in text)


def strip_control_chars(text: str) -> str:
    text = _CTRL_RANGE_RE.sub("", text)
    return "".join(ch for ch in text if ch not in _CTRL_CHARS)


def collapse_spaces(line: str) -> str:
    return _SPACES_RE.sub(" ", line).strip()


def is_footerish(line: str) -> bool:
    """整行是页码或 arXiv 提交戳记。"""
    s = line.strip()
    return bool(_PAGE_NUM_RE.match(s) or _ARXIV_STAMP_RE.match(s))


def merge_hyphenations(text: str) -> str:
    return _HYPHEN_JOIN_RE.sub("", text)


def _digit_norm(line: str) -> str:
    """把行中数字替换为 #,用于匹配页码变化的页眉页脚(如 ACM 页眉 "111:16 Lyu, et al.")。"""
    return _DIGIT_RE.sub("#", line)


def find_repeated_footers(
    pages_text: Iterable[str],
    *,
    max_len: int = 80,
    min_repeat: int = 2,
) -> dict:
    """统计跨页重复的短行(页眉/页脚),返回 {"exact": 完全重复行, "templates": 数字归一模板}。"""
    exact: Counter[str] = Counter()
    templates: Counter[str] = Counter()
    for text in pages_text:
        seen_e: set[str] = set()
        seen_t: set[str] = set()
        for raw in text.splitlines():
            s = " ".join(raw.split())
            if not s or len(s) > max_len or s.isdigit():
                continue
            if s not in seen_e:
                seen_e.add(s)
                exact[s] += 1
            t = _digit_norm(s)
            if t not in seen_t:
                seen_t.add(t)
                templates[t] += 1
    return {
        "exact": {s for s, n in exact.items() if n >= min_repeat},
        "templates": {t for t, n in templates.items() if n >= min_repeat},
    }


def clean_page_text(text: str, repeated_lines: dict) -> str:
    """清洗单页文本:删页眉页脚/页码/arXiv 戳记,合并断行连字符,折叠空白。

    repeated_lines 由 find_repeated_footers 对全文预计算,含 exact 与 templates 两类页眉页脚。
    """
    text = strip_control_chars(text)
    text = expand_ligatures(text)
    text = merge_hyphenations(text)
    exact = repeated_lines["exact"]
    templates = repeated_lines["templates"]
    lines = []
    for raw in text.splitlines():
        s = collapse_spaces(raw)
        if not s or is_footerish(s) or s in exact or _digit_norm(s) in templates:
            continue
        lines.append(s)
    return "\n".join(lines)


def is_section_header(line: str) -> bool:
    """判断一行是否为章节标题(编号/罗马数字/白名单)。"""
    s = line.strip()
    if not s or len(s) > _HEADER_MAX_LEN:
        return False
    if s[-1] in ".,;":
        return False
    if s.endswith(":"):
        return is_section_header(s[:-1])
    if s.lower() in _NAMED_SECTIONS:
        return True
    if _NUM_SECTION_RE.match(s):
        return True
    m = _NUM_SECTION_WORD_RE.match(s)
    if m and m.group(1).split()[0].lower() in _KNOWN_HEADING_WORDS:
        return True
    if "," in s:
        return False
    return bool(_ROMAN_SECTION_RE.match(s))


def _clean_heading(s: str) -> str:
    """把同行标题 "4.1.2 Implementation. Our ColBERT models are implemented" 截断为标题部分。"""
    if not re.match(r"^\d+(?:\.\d+)+\.?\s+[A-Z]", s):
        return s
    m = re.search(r"\.\s+[A-Z]", s)
    if m and m.start() < 60 and re.search(r"[A-Za-z]", s[:m.start()]):
        return s[:m.start()]
    return s


def _is_para_end(line: str) -> bool:
    """满行(>=25 字符)且行尾为句末标点 → 段落在此结束。"""
    return len(line) >= 25 and bool(_PARA_END_RE.search(line))


def split_section_paragraphs(
    page_texts: Iterable[str],
) -> list[tuple[str, int, str]]:
    """把每页清洗后文本切分为 (section, page, paragraph_text)。

    段落边界 = 空行 / 章节标题行 / 满行句号结尾;section 状态跨页维护;段落不跨页。
    """
    out: list[tuple[str, int, str]] = []
    section = "frontmatter"
    for page_no, text in enumerate(page_texts, start=1):
        para: list[str] = []
        for raw in text.splitlines():
            s = raw.strip()
            if not s:
                if para:
                    out.append((section, page_no, "\n".join(para)))
                    para = []
                continue
            if is_section_header(s):
                if para:
                    out.append((section, page_no, "\n".join(para)))
                    para = []
                section = _clean_heading(s)
                continue
            if para and _is_para_end(para[-1]):
                out.append((section, page_no, "\n".join(para)))
                para = []
            para.append(s)
        if para:
            out.append((section, page_no, "\n".join(para)))
    return out
