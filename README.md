# rag-paper-assistant

面向 **RAG 领域论文**的**可溯源**学术问答系统。

> 状态:项目脚手架已就绪,各模块待实现。

## 项目定位

- 以 RAG 领域论文为知识库,提供学术问答
- 每个回答必须可溯源:指回具体的论文、段落与检索依据
- 支持多种检索策略对比:dense / hybrid / hybrid+rerank

## 快速开始

(待实现后补充安装、配置、运行方式)

## 项目结构

| 目录 | 用途 |
| --- | --- |
| `configs/` | 实验配置(dense / hybrid / hybrid_rerank) |
| `data/` | 原始论文、处理后数据、评估数据 |
| `research/` | 领域研究、论文卡片、文献矩阵、实验计划 |
| `src/` | 核心代码:ingestion / retrieval / generation / evaluation |
| `scripts/` | 命令行入口:建索引、查询、跑实验、评估 |
| `tests/` | 单元与集成测试 |
| `outputs/` | 实验结果、图表、日志 |
| `paper/` | 论文写作 |

## 文档

- [`PROJECT_STATE.md`](PROJECT_STATE.md) — 项目当前进度与待办
- [`research/experiment_plan.md`](research/experiment_plan.md) — 实验计划
