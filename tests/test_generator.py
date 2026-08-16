"""generator 模块测试:prompt 组装、引用编号解析、越界丢弃、去重、空命中拒答、拒答识别。

用可注入的 fake OpenAI 兼容 client,不依赖网络/真实 API。
"""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from src.generation.generator import Generator, create_generator
from src.generation.prompts import build_system_prompt, build_user_prompt
from src.retrieval.dense import RetrievalHit


def hit(chunk_id="c1", paper_id="p1", title="Paper One", section="3 Method",
        text="retrieval augmented generation for knowledge", score=0.9,
        page_start=3, page_end=3) -> RetrievalHit:
    return RetrievalHit(
        score=score, chunk_id=chunk_id, paper_id=paper_id, title=title,
        section=section, sections=(section,), page_start=page_start, page_end=page_end,
        text=text, source="https://arxiv.org/abs/1", chunking="fixed", token_count=5,
    )


def fake_client(content: str = "answer text"):
    """构造 fake OpenAI 兼容 client:chat.completions.create 返回固定 content,并记录调用参数。"""
    class _Completions:
        def __init__(self, content):
            self._content = content
            self.calls = []

        def create(self, model, messages, temperature):
            self.calls.append({"model": model, "messages": messages, "temperature": temperature})
            resp = SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=self._content))])
            return resp

    return SimpleNamespace(chat=SimpleNamespace(completions=_Completions(content)))


def test_build_system_prompt_has_frozen_constraints():
    sys_prompt = build_system_prompt()
    # 冻结约束:只依据上下文、无证据拒答、不编造、引用用方括号编号标注
    assert "只能依据上下文" in sys_prompt
    assert "无法从给定材料中回答" in sys_prompt
    assert "不得编造" in sys_prompt
    assert "方括号编号" in sys_prompt and "[1]" in sys_prompt


def test_build_user_prompt_carries_real_section_not_guess():
    """章节/页码/paper_id 来自检索命中元数据(prompt 里原样带入,不由模型猜)。"""
    hits = [hit(chunk_id="c1", paper_id="rag_lewis2021", title="RAG",
                section="2 Methods", page_start=3, page_end=4),
            hit(chunk_id="c2", paper_id="dpr", title="DPR",
                section="4 Experiments", page_start=7, page_end=7)]
    prompt = build_user_prompt("What is RAG-Sequence?", hits)
    assert "[1]" in prompt and "[2]" in prompt
    assert "rag_lewis2021" in prompt and "2 Methods" in prompt and "3-4" in prompt
    assert "dpr" in prompt and "4 Experiments" in prompt and "7" in prompt
    assert "c1" in prompt and "c2" in prompt


def test_generate_returns_text_and_citations():
    hits = [hit(chunk_id="c1", text="rag sequence definition"),
            hit(chunk_id="c2", text="dense passage retrieval")]
    client = fake_client("RAG-Sequence 的定义见 [1],同时与 [2] 相关。")
    gen = Generator(client, model="deepseek-chat", temperature=0.2)
    result = gen.generate("RAG-Sequence是什么?", hits)
    assert result.text == "RAG-Sequence 的定义见 [1],同时与 [2] 相关。"
    assert [h.chunk_id for h in result.citations] == ["c1", "c2"]
    assert result.refused is False


def test_out_of_range_citation_dropped():
    hits = [hit(chunk_id="c1")]
    client = fake_client("见 [1] 和 [99] 与 [0]。")
    result = Generator(client).generate("q", hits)
    assert [h.chunk_id for h in result.citations] == ["c1"]


def test_citation_dedup_by_chunk_id():
    hits = [hit(chunk_id="c1"), hit(chunk_id="c2")]
    client = fake_client("先 [2] 再 [2] 最后 [1][2]。")
    result = Generator(client).generate("q", hits)
    assert [h.chunk_id for h in result.citations] == ["c2", "c1"]


def test_no_citations_when_answer_has_none():
    hits = [hit(chunk_id="c1")]
    client = fake_client("这是一个不带引用的回答。")
    result = Generator(client).generate("q", hits)
    assert result.citations == []
    assert result.refused is False


def test_empty_hits_refused_without_api_call():
    client = fake_client("should not be called")
    gen = Generator(client)
    result = gen.generate("q", [])
    assert result.refused is True
    assert "无法从给定材料中回答" in result.text
    assert client.chat.completions.calls == []  # 未调 API


def test_refusal_detected_from_text():
    hits = [hit(chunk_id="c1")]
    client = fake_client("无法从给定材料中回答这个问题。")
    result = Generator(client).generate("q", hits)
    assert result.refused is True


def test_prompt_and_temperature_passed_to_client():
    hits = [hit(chunk_id="c1")]
    client = fake_client("ok")
    gen = Generator(client, model="deepseek-chat", temperature=0.3)
    gen.generate("我的问题", hits)
    call = client.chat.completions.calls[0]
    assert call["model"] == "deepseek-chat"
    assert call["temperature"] == 0.3
    assert call["messages"][0]["role"] == "system"
    assert call["messages"][1]["role"] == "user"
    assert "我的问题" in call["messages"][1]["content"]


def test_create_generator_missing_key_raises(monkeypatch):
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setattr("dotenv.load_dotenv", lambda *a, **k: None)  # 屏蔽 .env 注入
    with pytest.raises(RuntimeError, match="API key"):
        create_generator(api_key=None)
