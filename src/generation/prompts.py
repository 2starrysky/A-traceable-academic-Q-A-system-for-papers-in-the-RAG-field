"""提示词模板:只依据给定证据回答;无证据拒答;引用编号对应真实检索命中。

冻结约束(experiment_plan.md §3 / research_questions.md §4):章节号随检索命中
原样带入 prompt,模型只引用编号、不得自行猜测章节。
"""
from __future__ import annotations

_SYSTEM = (
    "你是一个学术问答助手,回答必须严格基于下面给出的论文片段(检索上下文)。\n"
    "硬性要求:\n"
    "1. 只能依据上下文中的内容回答,不得使用上下文之外的知识。\n"
    "2. 如果上下文不足以回答问题,直接回答\"无法从给定材料中回答\",不要编造。\n"
    "3. 不得编造论文、章节或页码;章节与页码一律以上下文标注为准。\n"
    "4. 回答用中文。\n"
    "5. 引用来源时,在相应句末用方括号编号标注(编号取上下文各片段的编号,如 [1]、[2]),"
    "不要自创编号之外的来源。"
)


def build_system_prompt() -> str:
    return _SYSTEM


def _format_block(i: int, hit) -> str:
    pages = f"{hit.page_start}-{hit.page_end}" if hit.page_start != hit.page_end else str(hit.page_start)
    return (
        f"[{i}] 论文:{hit.title}({hit.paper_id}) | 章节:{hit.section} | "
        f"页码:{pages} | Chunk ID:{hit.chunk_id}\n"
        f"原文:{hit.text}"
    )


def build_user_prompt(question: str, hits) -> str:
    """把检索命中格式化为带编号的上下文块,末尾附问题。

    hits: 顺序即为编号 [1][2]… 的来源(检索器 Top-K 顺序)。
    """
    blocks = "\n\n".join(_format_block(i, hit) for i, hit in enumerate(hits, 1))
    return (
        f"以下是检索到的论文片段(带编号):\n\n{blocks}\n\n"
        f"问题:{question}\n\n"
        f"请依据上面的片段回答,并在引用处用 [编号] 标注。"
    )
