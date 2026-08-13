# Benchmarking Large Language Models in Retrieval-Augmented Generation

- **paper_id**: rgb_chen2023
- **作者**: Jiawei Chen, Hongyu Lin, Xianpei Han, Le Sun
- **年份 / venue**: 2023 / AAAI 2024
- **arXiv**: https://arxiv.org/abs/2309.01431

## 核心贡献

- **RGB(Retrieval-Augmented Generation Benchmark)**:首个把 RAG 所需能力拆成四个维度的系统性诊断基准:
  - **noise robustness(噪声鲁棒性)**:无关/噪音文档干扰下能否答对;
  - **negative rejection(负拒答)**:检索文档不含答案时能否正确拒答(不硬答);
  - **information integration(信息整合)**:答案分散在多个文档时能否聚合;
  - **counterfactual robustness(反事实鲁棒性)**:文档与模型记忆冲突时能否以文档为准。
- 中英双语语料;评估 6 个代表性 LLM,发现它们在 noise robustness 上尚可,但 **negative rejection、information integration、反事实处理显著偏弱**。

## 方法

- 把实例按四类能力拆成 4 个独立 testbed;用准确性/拒答行为等指标诊断各 LLM 的 RAG 能力瓶颈。

## 数据集

- 英中双语 RGB 语料(4 testbeds)。

## 对项目可借鉴点

- **negative rejection 维度与项目"拒答率"指标直接对应**:RGB 证明 LLM 在"无证据时该拒答"上偏弱,正是项目把拒答率列为关键指标(并区分真/误拒答)的文献依据。
- noise robustness 提示:Top-K 增大(RO3)或 hybrid 融合带入噪音时,鲁棒性会受考验,支撑 H4 的担忧。
- 4 能力维度可作为评估集题型的理论框架(事实型/方法理解/对比/跨章节/无答案五类与之呼应)。

## 缺陷 / 开放问题

- 测试集规模有限,以能力诊断为主,未给出缓解方案。
- 聚焦单轮 QA,未覆盖引用级定位(项目用双层引用标准补足这一面)。
