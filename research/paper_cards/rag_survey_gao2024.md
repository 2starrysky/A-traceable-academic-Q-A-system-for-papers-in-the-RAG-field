# Retrieval-Augmented Generation for Large Language Models: A Survey

- **paper_id**: rag_survey_gao2024
- **作者**: Yunfan Gao, Yun Xiong, Xinyu Gao, Kangxiang Jia, Jinliu Pan, Yuxi Bi, Yi Dai, Jiawei Sun, Meng Wang, Haofen Wang
- **年份 / venue**: 2024 / arXiv
- **arXiv**: https://arxiv.org/abs/2312.10997

## 核心贡献

- 系统综述 RAG 范式演进:**Naive RAG → Advanced RAG → Modular RAG** 三阶段分类。
- 拆解 RAG 的三部件基础:**检索、生成、增强(augmentation)**,逐部件梳理 SOTA 技术。
- 介绍评估框架与基准,并指出当前挑战与未来方向。

## 方法

- 综述方法论:按范式与部件两条线组织文献,分类讨论预检索/检索/后检索优化、生成增强、评估。

## 数据集

- 无(综述)。

## 对项目可借鉴点

- **项目定位的坐标系**:本项目"dense / hybrid / hybrid+rerank"三配置横跨 Naive/Advanced RAG,综述是评估集"论文对比"题的素材库(如"Hybrid 属于哪一范式")。
- 检索增强的三个环节(预检索改写、融合重排、生成约束)为项目各配置的设计理由提供文献依据。
- 综述里对混合检索与重排的讨论,是 H1/H2 文献预判的权威参考(Day 5 精读重点)。

## 缺陷 / 开放问题

- 综述性质,无新方法;对特定方法的细节描述有限。
- 篇幅长(全文数十页),做知识库语料时切块策略影响大(RQ2 直接相关)。
