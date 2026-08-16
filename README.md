# rag-paper-assistant

面向 **RAG 领域论文**的**可溯源**学术问答系统。

> 状态:Day 11 已完成——可溯源 RAG 闭环 + 50 题评估集 + 检索/生成指标 + E1 Dense Baseline 首份成绩单(Hit@5=0.9 / 引用正确率 0.958)。

## 项目定位

- 以 RAG 领域论文为知识库,提供学术问答
- 每个回答必须可溯源:指回具体的论文、段落与检索依据
- 支持多种检索策略对比:dense / hybrid / hybrid+rerank

## 快速开始

```bash
# 1. 安装依赖(建议 venv)
pip install -r requirements.txt

# 2. 语料:12 篇 PDF(data/raw/papers/) → documents.jsonl
python scripts/build_documents.py

# 3. 分块:fixed(512/80)+ section-aware 两种 chunking
python scripts/build_chunks.py --chunking both

# 4. 建 Dense 索引:bge-m3 编码 + FAISS(首次运行需下载模型)
python scripts/build_index.py --chunks data/processed/chunks_fixed.jsonl

# 5. 问答:完整闭环(检索 → 生成 → 带引用答案;LLM key 放 .env 的 DEEPSEEK_API_KEY)
python scripts/query.py --question "RAG-Sequence是什么?" --top-k 5

# 6. 纯检索(不接 LLM,Day 8 行为)
python scripts/query.py --question "RAG-Sequence是什么?" --retrieve-only
```

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
