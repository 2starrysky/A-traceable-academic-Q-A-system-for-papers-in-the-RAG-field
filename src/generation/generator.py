"""问答生成器:调用 OpenAI 兼容 LLM(默认 DeepSeek)生成带引用的回答。

client 可注入(fake 用于测试);引用解析把答案里的 [n] 编号映射回真实检索命中,
越界/不存在的编号丢弃。拒答(上下文无证据)在空命中时不调 API 直接返回,
有命中时由 LLM 文本特征识别。
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass, field

from src.generation.prompts import build_system_prompt, build_user_prompt
from src.retrieval.dense import RetrievalHit

# 上下文无证据时模型常见的拒答表达
_REFUSAL_PATTERNS = re.compile(
    r"无法(从|根据)?(给定)?(上下文|材料).*回答|无法回答|不能回答|"
    r"上下文(中|里)?没有|材料(中|里)?没有|未提供(相关)?(信息|内容)|"
    r"找不到(相关|与.*相关)?(信息|证据)|没有(相关|与问题相关)?(信息|证据)",
    re.IGNORECASE,
)

_CITE_RE = re.compile(r"\[(\d{1,3})\]")

_EMPTY_HITS_TEXT = "无法从给定材料中回答。"


@dataclass
class GenerationResult:
    """一次生成的输出:text 为回答;citations 为该回答实际引用的检索命中;refused 为是否拒答。"""
    text: str
    citations: list[RetrievalHit] = field(default_factory=list)
    refused: bool = False


class Generator:
    def __init__(self, client, model: str = "deepseek-chat", temperature: float = 0.2):
        self._client = client
        self.model = model
        self.temperature = temperature

    def generate(self, question: str, hits) -> GenerationResult:
        if not hits:
            return GenerationResult(text=_EMPTY_HITS_TEXT, refused=True)
        messages = [
            {"role": "system", "content": build_system_prompt()},
            {"role": "user", "content": build_user_prompt(question, hits)},
        ]
        resp = self._client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
        )
        text = (resp.choices[0].message.content or "").strip()
        citations = self._parse_citations(text, hits)
        refused = bool(_REFUSAL_PATTERNS.search(text))
        return GenerationResult(text=text, citations=citations, refused=refused)

    def _parse_citations(self, text: str, hits) -> list[RetrievalHit]:
        """提取 [n] 编号映射到真实命中;越界编号丢弃;按出现顺序、按 chunk_id 去重。"""
        hits_list = list(hits)
        seen: set[str] = set()
        result: list[RetrievalHit] = []
        for m in _CITE_RE.finditer(text):
            n = int(m.group(1))
            if 1 <= n <= len(hits_list):
                hit = hits_list[n - 1]
                if hit.chunk_id not in seen:
                    seen.add(hit.chunk_id)
                    result.append(hit)
        return result


def create_generator(provider: str = "deepseek", model: str | None = None,
                     base_url: str | None = None, api_key: str | None = None,
                     temperature: float = 0.2) -> Generator:
    """工厂:从 .env/环境变量读 DeepSeek(OpenAI 兼容)配置;key/model/base_url 可显式覆盖。

    依赖 python-dotenv(.env 已 gitignore,key 不入库)。
    """
    from dotenv import load_dotenv
    from openai import OpenAI

    load_dotenv()
    key = api_key or os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("未找到 LLM API key:请在 .env 设置 DEEPSEEK_API_KEY")
    url = base_url or os.getenv("DEEPSEEK_BASE_URL") or "https://api.deepseek.com/v1"
    mdl = model or os.getenv("DEEPSEEK_MODEL") or "deepseek-chat"
    client = OpenAI(api_key=key, base_url=url)
    return Generator(client, model=mdl, temperature=temperature)
