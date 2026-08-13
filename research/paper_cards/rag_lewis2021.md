# Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks

- **paper_id**: rag_lewis2021
- **作者**: Patrick Lewis, Ethan Perez, Aleksandra Piktus, Fabio Petroni, Vladimir Karpukhin, Naman Goyal, Heinrich Küttler, Mike Lewis, Wen-tau Yih, Tim Rocktäschel, Sebastian Riedel, Douwe Kiela
- **年份 / venue**: 2021 / NeurIPS 2020
- **arXiv**: https://arxiv.org/abs/2005.11401

## 核心贡献

- RAG 开山之作:把参数化记忆(预训练 seq2seq)与非参数化记忆(可微访问的稠密向量索引)统一进一个可微分的生成框架。
- 提出两种条件方式:**RAG-Sequence**(整段生成共用同一批检索文档)与 **RAG-Token**(每个 token 可选不同文档)。
- 在 NQ、TriviaQA、WebQuestions 等开放域 QA 上刷新 SOTA,超越纯参数 seq2seq 与 task-specific extractive 架构;生成侧语言更具体、多样、事实正确。

## 方法

- 非参数记忆 = 用 DPR 检索 Wikipedia 的稠密索引;参数记忆 = BART 生成器。
- 检索 top-K 文档,生成时按文档概率加权(log-sum-exp / token-wise)。

## 数据集

- Natural Questions、TriviaQA、WebQuestions、CuratedTREC、FEVER、MS-MARCO、Jeopardy。

## 对项目可借鉴点

- 本项目知识库的"锚点论文":评估集里关于"RAG 是什么、两种公式差异"的事实型/方法理解题直接以本文为准。
- RAG-Sequence(同一批证据支撑整段答案)是"引用正确率"评估下最自然的生成范式——答案整体绑定到一组 Chunk。

## 缺陷 / 开放问题

- 生成质量强依赖检索 top-K 文档的相关性;检索失败时无纠错机制(对比 CRAG)。
- 稠密索引更新昂贵,世界知识难以及时更新(作者自述的 open problem)。
