"""端到端流水线:问题 → Dense Top-K 检索 → LLM 生成 → 带引用答案。

retriever/generator 均可注入,便于测试与后续 Hybrid/Reranker 换用。
"""
from __future__ import annotations

from dataclasses import dataclass, field

from src.generation.generator import GenerationResult, Generator
from src.retrieval.dense import RetrievalHit


@dataclass
class PipelineResult:
    """单次问答结果:hits 为检索命中;answer/citations/refused 由生成结果派生。"""
    question: str
    hits: list[RetrievalHit] = field(default_factory=list)
    generation: GenerationResult | None = None

    @property
    def answer(self) -> str:
        return self.generation.text if self.generation else ""

    @property
    def citations(self) -> list[RetrievalHit]:
        return self.generation.citations if self.generation else []

    @property
    def refused(self) -> bool:
        return self.generation.refused if self.generation else False


def answer_question(question: str, retriever, generator: Generator,
                    top_k: int = 5) -> PipelineResult:
    """检索 → 生成;retriever 需有 search(question, top_k),generator 需有 generate(question, hits)。"""
    hits = retriever.search(question, top_k=top_k)
    generation = generator.generate(question, hits)
    return PipelineResult(question=question, hits=hits, generation=generation)
