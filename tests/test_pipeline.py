"""pipeline 模块测试:检索→生成串联、空检索拒答、top_k 截断。

retriever 用 FakeRetriever(固定命中),generator 用真实 Generator + fake client,
不依赖网络/真实 API。
"""
from __future__ import annotations

from types import SimpleNamespace

from src.generation.generator import Generator
from src.pipeline import PipelineResult, answer_question
from src.retrieval.dense import RetrievalHit


def hit(chunk_id="c1", paper_id="p1", title="Paper One", section="3 Method",
        text="some evidence text", score=0.9, page_start=3, page_end=3) -> RetrievalHit:
    return RetrievalHit(
        score=score, chunk_id=chunk_id, paper_id=paper_id, title=title,
        section=section, sections=(section,), page_start=page_start, page_end=page_end,
        text=text, source="https://arxiv.org/abs/1", chunking="fixed", token_count=5,
    )


def fake_client(content: str = "answer text"):
    class _Completions:
        def __init__(self, content):
            self._content = content
            self.calls = []

        def create(self, model, messages, temperature):
            self.calls.append({"model": model, "messages": messages, "temperature": temperature})
            resp = SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=self._content))])
            return resp

    return SimpleNamespace(chat=SimpleNamespace(completions=_Completions(content)))


class FakeRetriever:
    def __init__(self, hits):
        self._hits = hits

    def search(self, question, top_k=5):
        return self._hits[:top_k]


def test_pipeline_retrieves_then_generates():
    hits = [hit(chunk_id="c1"), hit(chunk_id="c2")]
    retriever = FakeRetriever(hits)
    generator = Generator(fake_client("答案是 [1]。"), model="deepseek-chat")
    result = answer_question("Q", retriever, generator, top_k=5)
    assert isinstance(result, PipelineResult)
    assert result.question == "Q"
    assert [h.chunk_id for h in result.hits] == ["c1", "c2"]
    assert result.answer == "答案是 [1]。"
    assert [h.chunk_id for h in result.citations] == ["c1"]
    assert result.refused is False


def test_pipeline_empty_retrieval_refuses():
    retriever = FakeRetriever([])
    generator = Generator(fake_client("不该被调用"))
    result = answer_question("知识库外的问题", retriever, generator, top_k=5)
    assert result.hits == []
    assert result.refused is True
    assert "无法从给定材料中回答" in result.answer


def test_pipeline_topk_caps_retrieval():
    hits = [hit(chunk_id=f"c{i}") for i in range(5)]
    retriever = FakeRetriever(hits)
    generator = Generator(fake_client("ok"))
    result = answer_question("Q", retriever, generator, top_k=3)
    assert len(result.hits) == 3
    assert [h.chunk_id for h in result.hits] == ["c0", "c1", "c2"]
