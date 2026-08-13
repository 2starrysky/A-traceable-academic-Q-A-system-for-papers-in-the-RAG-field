# Corrective Retrieval Augmented Generation

- **paper_id**: crag_yan2024
- **作者**: Shi-Qi Yan, Jia-Chen Gu, Yun Zhu, Zhen-Hua Ling
- **年份 / venue**: 2024 / ACM MM 2024
- **arXiv**: https://arxiv.org/abs/2401.15884

## 核心贡献

- **CRAG**:针对"检索失败怎么办"的纠错式 RAG。核心是一个轻量检索评估器,评估已检索文档的整体质量并给出置信度,据此触发不同动作。
- 检索评估为 **Correct / Incorrect / Ambiguous** 三种状态:Correct 直接走生成;Incorrect/Ambiguous 触发纠正(静态语料不足时扩展 web 检索)。
- 提出 **decompose-then-recompose**:把检索文档拆成细粒度段落、按相关度过滤噪声后再重组,聚焦关键信息。
- 即插即用,可与多种 RAG 基线耦合,在短/长文生成任务上都显著提升。

## 方法

- 检索评估器(轻量判别式模型或 LLM)打分 → 置信度阈值切分三态。
- 纠错路径:静态检索失败 → 引入 web 检索扩展;decompose-then-recompose 清洗文档。

## 数据集

- PopQA、Biography、PubHealth、ArcChallenge(覆盖短/长文生成)。

## 对项目可借鉴点

- **检索纠错/反思**方向的代表,与"检索失败导致误拒答"直接相关:CRAG 的评估器相当于给"该不该继续用这批证据"一个信号。
- 评估集"无答案"题(10 题)里,如何区分"检索没捞到"(误拒答)与"确实没有"(真拒答),可借鉴 CRAG 的置信度思想做解释。
- decompose-then-recompose 的"去噪后重组"对章节感知切块后的证据清洗有参考。

## 缺陷 / 开放问题

- 检索评估器本身需要标注或较强的 LLM 判断,质量波动会传导。
- web 检索引入外部依赖与延迟,与项目"小规模静态知识库 + 平均延迟指标"约束冲突(仅作思想参考)。
