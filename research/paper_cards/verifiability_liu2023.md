# Evaluating Verifiability in Generative Search Engines

- **paper_id**: verifiability_liu2023
- **作者**: Nelson F. Liu, Tianyi Zhang, Percy Liang
- **年份 / venue**: 2023 / Findings of EMNLP 2023
- **arXiv**: https://arxiv.org/abs/2304.09848

## 核心贡献

- 提出生成式搜索引擎的**可核查性(verifiability)**评估框架,两层标准:
  - **引用召回(citation recall)**:所有陈述都应被引用支撑;
  - **引用精度(citation precision)**:每个引用都应支持其关联的陈述。
- 人工审计 Bing Chat、NeevaAI、perplexity.ai、YouChat 四个商业系统:平均仅 **51.5%** 的生成句子被引用完全支撑、**74.5%** 的引用支持其关联句子——数字令人担忧,揭示"流畅但不可信"的普遍问题。

## 方法

- 人类标注者对查询-响应对做细粒度标注:句子级与引用级的支持关系。
- 从历史 Google 查询与 Reddit 动态收集多样化查询集。

## 数据集

- 四个商业系统 + 多样化查询集(Google 历史查询、Reddit 开放问题)。

## 对项目可借鉴点

- **本项目北极星指标(引用正确率)的直接理论同构**:项目"论文 + 章节双层都对才算引用正确"正是把本文的 citation precision 细化为两层。Day 5 精读本文可为评估协议提供权威支撑。
- 51.5%/74.5% 这两个数字可作为本项目评估结果的外部参照(项目若在 12 篇小库上明显更高,本身是有意义的发现)。
- "流畅但不可信"正是用户"大模型答得顺溜可能是幻觉"担心的科学化表达。

## 缺陷 / 开放问题

- 人工评估成本高、标准漂移风险(项目风险 R4 与之相同,缓解方案可借鉴其标注指南)。
- 针对商业黑盒系统,未给出可复用的自动评估工具链。
