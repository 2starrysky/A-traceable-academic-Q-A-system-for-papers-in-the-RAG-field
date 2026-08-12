# 实验计划

## 目标

对比三种检索配置在可溯源学术问答上的表现:
1. **dense** — 纯稠密向量检索(`configs/dense.yaml`)
2. **hybrid** — 稠密 + BM25 融合(`configs/hybrid.yaml`)
3. **hybrid_rerank** — 混合检索 + 重排(`configs/hybrid_rerank.yaml`)

## 评估数据

(待定义:问题集、金标准引用、构建方式)

## 指标

- 检索:Recall@k、MRR、NDCG
- 生成:忠实度、引用正确性、回答质量

## 步骤

1. 收集论文并构建知识库
2. 构建评估集
3. 用三种配置各跑一遍
4. 计算指标 + 错误分析
5. 撰写结果

## 结果记录

实验输出统一存到 `outputs/experiments/`,并记录配置指纹、数据版本、commit hash,保证可追溯。
