# Lost in the Middle: How Language Models Use Long Contexts

- **paper_id**: litm_liu2023
- **作者**: Nelson F. Liu, Kevin Lin, John Hewitt, Ashwin Paranjape, Michele Bevilacqua, Fabio Petroni, Percy Liang
- **年份 / venue**: 2023 / TMLR 2024
- **arXiv**: https://arxiv.org/abs/2307.03172

## 核心贡献

- 系统性揭示 LLM 对长上下文的非鲁棒使用:**相关信息出现在输入中间时,性能显著下降**;出现在开头或结尾时性能最高。
- 即使对显式支持长上下文的模型,该现象依然存在。
- 提供两项任务(多文档 QA、键值检索)上的位置敏感性分析协议。

## 方法

- 控制变量:固定同一批相关证据,只改变它在上下文中的位置,测任务准确率随位置的函数。
- 多文档 QA 与 key-value retrieval 两个诊断任务。

## 数据集

- 多文档问答构造集、键值检索构造集。

## 对项目可借鉴点

- **Top-K 与上下文排序的直接理论依据(RQ3)**:Top-K 从 5 增至 8 会把更多证据塞进上下文中间,本文提示这未必提升、甚至可能因位置偏差受损——正是 H4 的文献背书。
- 引用的展示顺序(证据块如何排布)可能影响模型"用没用对",对生成时的上下文编排有启发。
- 与 FiD"越多越好"形成可对比的反向观点,是评估集对比题的好素材。

## 缺陷 / 开放问题

- 诊断性发现为主,未给出修复方案;任务以短答案为载体,长文/多跳场景结论需谨慎迁移。
- 仅测"位置",未测证据相关性与噪音混合的影响(RGB 的 noise robustness 补充了这一面)。
