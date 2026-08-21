# RAG Paper Assistant

**面向 RAG 领域论文的可溯源学术问答系统**

> 一个以 RAG 研究论文为知识库的学术问答系统，每个回答必须可溯源到具体论文、章节和段落。

## 项目背景

大语言模型(LLM)在生成回答时容易产生"幻觉"——一本正经地编造不存在的引用。本系统通过 **检索增强生成(RAG)** 技术，让每个回答都基于真实论文证据，并以 `[1][2]` 编号标注引用来源，用户可一键查看答案出自哪篇论文、哪个章节。

**研究问题：**
- RQ1：Dense、Hybrid、Hybrid+Reranker 三种检索配置对检索质量和生成质量有何差异？
- RQ2：固定 Token 切块和章节感知切块，哪一种更适合学术论文 RAG？
- RQ3：Top-K 增大是否一定提高回答质量？

## 系统架构

```
用户提问
  ↓
检索器(Dense / BM25 / Hybrid / Hybrid+Reranker)
  ↓  从 439 个论文段落中找到最相关的 top-k 个
提示词模板(带编号上下文 + 约束指令)
  ↓
LLM(DeepSeek deepseek-chat)
  ↓  生成回答 + 标注 [1][2] 引用编号
引用解析器
  ↓  [1] → 真实 Chunk ID → 论文标题 + 章节 + 页码
返回带出处的答案
```

**关键设计：** 章节元数据随检索结果传入提示词，LLM 只选择编号，不猜测章节——确保引用正确性反映检索质量，而非模型运气。

## 环境安装

```bash
# 1. 克隆仓库
git clone <repo-url>
cd rag-paper-assistant

# 2. 创建虚拟环境(推荐)
python -m venv venv
venv\Scripts\activate     # Windows
# source venv/bin/activate  # Linux/Mac

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置 API Key
#    在项目根目录创建 .env 文件：
echo DEEPSEEK_API_KEY=你的密钥 > .env
#    可选: DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
```

**主要依赖：** pypdf, tiktoken, sentence-transformers, rank-bm25, faiss-cpu, openai, gradio, pyyaml

## 数据准备

```bash
# 1. 放入论文 PDF
#    将 12 篇 RAG 相关论文放入 data/raw/papers/ 目录
#    文件名格式: paper_id.pdf (如 rag_lewis2021.pdf)

# 2. 解析 PDF → 结构化文档
python scripts/build_documents.py
#    输出: data/processed/documents.jsonl (1888 段落)

# 3. 切块(固定 Token 512/overlap 80)
python scripts/build_chunks.py --chunking fixed
#    输出: data/processed/chunks_fixed.jsonl (439 块)
```

## 构建索引

```bash
# Dense 索引(bge-m3 编码 + FAISS)
python scripts/build_index.py --chunks data/processed/chunks_fixed.jsonl
#    首次运行下载 bge-m3 模型(~2.3GB)，后续离线加载
#    输出: data/processed/dense_index/
```

## 使用方式

### Web Demo（推荐）

```bash
python app.py                # 启动 Gradio 界面，默认 http://localhost:7860
python app.py --port 8080    # 自定义端口
python app.py --share        # 生成公网分享链接
```

界面支持：选择检索器(Dense/BM25/Hybrid/Hybrid+Reranker) → 设置 Top-K → 输入问题 → 查看答案、引用来源和检索详情。

### 命令行查询

```bash
# 完整闭环(检索 + 生成 + 带引用答案)
python scripts/query.py --question "RAG-Sequence是什么?" --top-k 5

# 纯检索(不接 LLM)
python scripts/query.py --question "RAG-Sequence是什么?" --retrieve-only

# 使用 Hybrid 检索器
python scripts/query.py --question "Top-K越大越好吗?" --config configs/hybrid.yaml
```

## 实验结果

### 主实验：检索配置对比(E1-E4)

| 配置 | Hit@1 | Hit@5 | MRR | 引用正确率 | 误拒答率 | 延迟 |
|------|-------|-------|-----|-----------|---------|------|
| E1 Dense | **0.700** | **0.900** | **0.780** | 0.958 | 0.400 | 2.06s |
| E2 BM25 | 0.000 | 0.125 | 0.045 | 0.800 | 0.875 | 1.08s |
| E3 Hybrid | 0.650 | 0.875 | 0.735 | 0.957 | 0.425 | 1.89s |
| E4 Hybrid+Rerank | 0.675 | 0.875 | 0.767 | **0.962** | **0.350** | 307.83s |

**关键发现：**
- Dense 在中文语义查询上显著优于 BM25（Hit@1: 0.70 vs 0.00）
- Hybrid 检索召回增强但排序略损（逐题找回 E1 失败的 10/11 题）
- Reranker 引用正确率最高(0.962)，但 CPU 延迟 150 倍

### 切块消融(E5)

| 策略 | 块数 | 跨章节 | Section Hit@5 | MRR |
|------|------|--------|---------------|------|
| fixed 256/50 | 911 | 187 | 0.875 | **0.731** |
| fixed 512/80 | 439 | 149 | **0.900** | 0.695 |
| section-aware | 505 | **0** | 0.875 | 0.672 |

### Top-K 消融(E6)

| Top-K | 检索 Hit@5 | 引用正确率 | 误拒答率 | 延迟 |
|-------|-----------|-----------|---------|------|
| 3 | 0.875 | 0.958 | 0.400 | 2.07s |
| 5 | 0.900 | 0.962 | 0.350 | 2.20s |
| 8 | 0.900 | **1.000** | **0.300** | 2.39s |

### Prompt 消融(E7)

约束指令("只基于检索内容回答，不要编造")是最高性价比杠杆：Support Rate 36% → 62%（+26pp）。

## 错误分析

- **BM25 中文失效**：72% 错误率，几乎全是 bm25_error——中文语义查询与英文论文文本词面不匹配
- **生成层保守**：Dense 38% 错误中，generation_error 主导（DeepSeek 对对比/综合题倾向拒答）
- **Reranker 性价比**：引用正确率仅提升 0.4pp，延迟增加 150 倍
- **切块影响有限**：三种策略 Hit@5 差异仅 0.875-0.900

详见 `research/error_analysis.md` 和 `outputs/figures/` 图表。

## 项目结构

```
rag-paper-assistant/
├── app.py                      # Gradio Web Demo
├── configs/                    # 实验配置(dense/hybrid/hybrid_rerank)
├── data/
│   ├── raw/papers/             # 12 篇论文 PDF
│   ├── processed/              # 处理后的文档、chunks、索引
│   └── evaluation/             # 评估集(50 题)
├── paper/                      # 研究报告
│   ├── manuscript_v2.md        # 论文终稿
│   ├── references.bib          # 参考文献
│   └── figures/                # 论文图表
├── research/                   # 研究文档
│   ├── scope/                  # 研究问题与假设
│   ├── paper_cards/            # 论文精读卡片
│   └── learning_notes.md       # 学习笔记(逐日讲解)
├── src/                        # 核心代码
│   ├── ingestion/              # PDF 解析、切块
│   ├── retrieval/              # Dense/BM25/Hybrid/Reranker
│   ├── generation/             # LLM 提示词与生成
│   └── evaluation/             # 评估指标与错误分析
├── scripts/                    # 命令行工具
├── outputs/                    # 实验结果与图表
└── tests/                      # 单元测试(81 项)
```

## 局限性

1. **小知识库**：仅 12 篇论文，结论未必迁移到更大语料
2. **单一 LLM**：使用 DeepSeek deepseek-chat，未做多模型对比
3. **CPU 重排慢**：E4 Hybrid+Reranker 延迟 308s/题，需 GPU 加速
4. **评估集有限**：50 题，可能未覆盖所有失败模式
5. **LLM 评估波动**：E7 使用 LLM-as-judge，存在 ±5% 方差

## 复现说明

```bash
# 从零复现完整实验
pip install -r requirements.txt
echo DEEPSEEK_API_KEY=你的密钥 > .env

# 数据处理
python scripts/build_documents.py
python scripts/build_chunks.py --chunking fixed
python scripts/build_index.py

# 运行实验
python scripts/run_experiment.py --method dense       # E1
python scripts/run_experiment.py --method bm25        # E2
python scripts/run_experiment.py --method hybrid      # E3
python scripts/run_experiment.py --method hybrid_rerank  # E4

# 启动 Demo
python app.py
```

## License

MIT
