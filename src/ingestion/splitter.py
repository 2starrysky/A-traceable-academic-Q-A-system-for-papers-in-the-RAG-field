"""分块:fixed(chunk_size/overlap)与 section-aware(max_chunk_size/overlap)两种切块,保留可溯源定位信息。

输入为文档段落(带 paper_id/title/section/page/text/source 的对象),输出 Chunk 列表。
token 计数默认用 tiktoken cl100k_base(与项目 gpt-4o-mini 对齐),可注入 encoder 便于测试/替换。
"""
from __future__ import annotations

from dataclasses import dataclass

_DEFAULT_ENCODER = None


def _get_encoder():
    global _DEFAULT_ENCODER
    if _DEFAULT_ENCODER is None:
        import tiktoken
        _DEFAULT_ENCODER = tiktoken.get_encoding("cl100k_base")
    return _DEFAULT_ENCODER


@dataclass(frozen=True)
class Chunk:
    chunk_id: str
    paper_id: str
    title: str
    section: str
    sections: tuple[str, ...]
    page_start: int
    page_end: int
    text: str
    source: str
    chunking: str
    token_count: int

    def as_dict(self) -> dict:
        return {
            "chunk_id": self.chunk_id,
            "paper_id": self.paper_id,
            "title": self.title,
            "section": self.section,
            "sections": list(self.sections),
            "page_start": self.page_start,
            "page_end": self.page_end,
            "text": self.text,
            "source": self.source,
            "chunking": self.chunking,
            "token_count": self.token_count,
        }


def _build_stream(docs, encode):
    """把一组文档段落拼成 token 流 + 段落边界表 (start, end, section, page)。"""
    tokens: list[int] = []
    segs: list[tuple[int, int, str, int]] = []
    sep = encode("\n\n")
    for doc in docs:
        t = encode(doc.text)
        start = len(tokens)
        tokens.extend(t)
        segs.append((start, len(tokens), doc.section, doc.page))
        tokens.extend(sep)
    return tokens, segs


def _windows(n: int, chunk_size: int, overlap: int):
    """在长度 n 的 token 流上产出 [start, end) 窗口,步长 = chunk_size - overlap。

    窗口覆盖到 n 即停止;剩余不足一个步长时不再滑,避免产生超短尾窗。
    """
    step = max(1, chunk_size - overlap)
    start = 0
    while True:
        end = min(start + chunk_size, n)
        if end <= start:
            break
        yield start, end
        if end >= n:
            break
        next_start = start + step
        if next_start >= n:
            break
        start = next_start


def _build_chunk_data(tokens, t0, t1, segs, decode):
    """由窗口 [t0, t1) 解析出一个 chunk 的内容(主 section、覆盖 section、页范围、文本)。"""
    text = decode(tokens[t0:t1]).strip()
    if not text:
        return None
    covered = [s for s in segs if s[0] < t1 and s[1] > t0]
    if not covered:
        return None
    main = next((s for s in segs if s[0] <= t0 < s[1]), None)
    if main is None:
        cand = [s for s in segs if s[1] <= t0]
        main = cand[-1] if cand else covered[0]
    return {
        "text": text,
        "section": main[2],
        "sections": tuple(dict.fromkeys(s[2] for s in covered)),
        "page_start": min(s[3] for s in covered),
        "page_end": max(s[3] for s in covered),
        "token_count": t1 - t0,
    }


def split_fixed(
    docs,
    chunk_size: int = 512,
    overlap: int = 80,
    encoder=None,
) -> list[Chunk]:
    """fixed 切块:整篇段落拼成 token 流后滑窗(step = chunk_size - overlap),chunk 可跨 section。"""
    encoder = encoder or _get_encoder()
    if not docs:
        return []
    tokens, segs = _build_stream(docs, encoder.encode)
    meta = {"paper_id": docs[0].paper_id, "title": docs[0].title, "source": docs[0].source}
    chunks: list[Chunk] = []
    seq = 0
    for t0, t1 in _windows(len(tokens), chunk_size, overlap):
        data = _build_chunk_data(tokens, t0, t1, segs, encoder.decode)
        if data is None:
            continue
        seq += 1
        chunks.append(
            Chunk(
                chunk_id=f"{meta['paper_id']}-{seq:04d}",
                paper_id=meta["paper_id"],
                title=meta["title"],
                source=meta["source"],
                chunking="fixed",
                **data,
            )
        )
    return chunks


def split_section_aware(
    docs,
    chunk_size: int = 512,
    overlap: int = 80,
    encoder=None,
) -> list[Chunk]:
    """section-aware 切块:按 section 分组,组内滑窗;chunk 不跨 section,超长 section 组内续拆。"""
    encoder = encoder or _get_encoder()
    if not docs:
        return []
    groups: list[list] = []
    for doc in docs:
        if groups and groups[-1][0] == doc.section:
            groups[-1][1].append(doc)
        else:
            groups.append([doc.section, [doc]])
    meta = {"paper_id": docs[0].paper_id, "title": docs[0].title, "source": docs[0].source}
    chunks: list[Chunk] = []
    seq = 0
    for _section, gdocs in groups:
        tokens, segs = _build_stream(gdocs, encoder.encode)
        for t0, t1 in _windows(len(tokens), chunk_size, overlap):
            data = _build_chunk_data(tokens, t0, t1, segs, encoder.decode)
            if data is None:
                continue
            seq += 1
            chunks.append(
                Chunk(
                    chunk_id=f"{meta['paper_id']}-{seq:04d}",
                    paper_id=meta["paper_id"],
                    title=meta["title"],
                    source=meta["source"],
                    chunking="section_aware",
                    **data,
                )
            )
    return chunks
