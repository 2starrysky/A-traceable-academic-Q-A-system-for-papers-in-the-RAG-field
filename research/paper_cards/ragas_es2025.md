# Ragas: Automated Evaluation of Retrieval Augmented Generation

- **paper_id**: ragas_es2025
- **作者**: Shahul Es, Jithin James, Luis Espinosa-Anke, Steven Schockaert
- **年份 / venue**: 2025 / arXiv
- **arXiv**: https://arxiv.org/abs/2309.15217

## 核心贡献

- **Ragas**:面向 RAG 管线的**免标注(reference-free)**评估框架,无需金标准人工标注即可评估 RAG 多个维度。
- 指标套件覆盖检索与生成两侧:
  - 检索侧:**上下文相关性、上下文召回**;
  - 生成侧:**faithfulness(忠实度)、答案相关性、答案正确性**。
- 关键主张:免标注框架可加速 RAG 架构的评估迭代。

## 方法

- 用合成问题构建评估集;faithfulness 通过对答案断言与上下文的一致性判定,答案相关性用生成问题与原始问题的相似度衡量。

## 数据集

- 合成构建的 RAG 评估集。

## 对项目可借鉴点

- **faithfulness 指标的权威来源**:项目指标表里的"忠实度"定义与 Ragas 一致(断言是否被上下文支持)。
- 免标注/LLM-as-judge 的方法论可对比:项目 RQ1b 采用**人工标注金标准**评估引用正确率,与 Ragas 形成"人工 vs 自动"两种评估范式的对比讨论。
- 其指标拆解(检索侧 vs 生成侧分开看)正是项目 RQ1a/RQ1b 拆分的思想。

## 缺陷 / 开放问题

- 免标注指标依赖 LLM judge,存在系统性偏差(尤其对"引用定位"这类细粒度判断,LLM 不如人工可靠——项目因此坚持人工标注)。
- 对"章节级引用正确"这种双层标准,Ragas 的 metrics 粒度不够。
