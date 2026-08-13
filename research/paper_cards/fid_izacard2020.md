# Leveraging Passage Retrieval with Generative Models for Open Domain Question Answering

- **paper_id**: fid_izacard2020
- **作者**: Gautier Izacard, Edouard Grave
- **年份 / venue**: 2020 / arXiv(EACL 2021)
- **arXiv**: https://arxiv.org/abs/2007.01282

## 核心贡献

- **FiD(Fusion-in-Decoder)**:把检索到的多个 passage 各自独立编码,再在解码器里融合,从而让生成模型充分利用多文档证据。
- 关键发现:**top-K 从 5 增到 100,性能持续提升**——生成模型擅长聚合和组合多个 passage 的证据。
- 在 Natural Questions、TriviaQA 开放域基准上取得当时 SOTA。

## 方法

- 检索 top-K passage → 每个 passage 与 question 拼接独立过编码器 → 所有编码输出拼接后一起输入解码器生成答案。
- 编码器可并行处理各 passage,融合只发生在解码层。

## 数据集

- Natural Questions、TriviaQA。

## 对项目可借鉴点

- **多证据融合生成**的直接支撑:RAG 评估下答案要"引多个 Chunk",FiD 证明"给更多相关证据、让模型自己聚合"是有效路线。
- 与 **RQ3(Top-K 5→8)** 直接对话:FiD 观察到越多越好,而 Lost in the Middle 观察到处在中间的证据被忽视——本项目正是要在这两种张力下实测 Top-K 的影响。
- 与 RAG(Lewis)形成"融合时机"对比:RAG 在生成层加权,FiD 在解码前融合。

## 缺陷 / 开放问题

- 计算量与 Top-K 线性增长;FiD 本身不输出可溯源的引用定位。
- 无融合权重/选择机制,对低相关 passage 的噪音较敏感。
