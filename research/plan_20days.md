# 20 天完整计划(rag-paper-assistant)

> 项目手册 · 用户人工确认版 · 2026-08-13 落盘。
> 每天开工读本文件对应 Day + `PROJECT_STATE.md` + 当天 GitHub Issue。本计划为**操作手册**,优先于其它推断的计划。

---

## 一、项目最终目标

**项目名称**:面向 RAG 领域论文的可溯源学术问答系统

**系统功能**

用户输入:
- Dense Retrieval 和 BM25 各自有什么优势?
- RAG-Sequence 和 RAG-Token 有什么区别?
- 为什么 Top-K 不是越大越好?
- Ragas 如何评估 Faithfulness?

系统输出:
- 基于论文证据的回答;
- 论文标题;
- 章节信息;
- 原始文本 Chunk;
- 检索分数;
- 无证据时拒绝回答。

**核心实验问题**:在小规模 RAG 论文知识库中,Dense Retrieval、Hybrid Retrieval 和 Hybrid+Reranker 对检索质量、回答忠实度和响应延迟有什么影响?

**附加研究问题**:固定 Token 切块和章节感知切块,哪一种更适合学术论文 RAG?

---

## 二、20 天最终交付物

项目结束时至少要有:

1. 10～15 篇 RAG 核心论文知识库
2. 6 篇核心论文精读笔记
3. 40～60 条人工评估数据
4. Dense Retrieval Baseline
5. BM25 Retrieval
6. Hybrid Retrieval
7. Hybrid + Reranker
8. 两种 Chunk 策略
9. Hit@K、MRR、Faithfulness、引用正确率等指标
10. 错误案例分析
11. Gradio Web Demo
12. GitHub 项目与完整 README
13. 6～10 页小型研究报告
14. 3～5 分钟演示视频

这不是以"20 天投稿"为目标,而是完成一篇结构完整、具有实验依据的研究型项目报告或 Workshop 风格初稿。

---

## 三、只安装这些 Skills

不要安装所有仓库。20 天内控制在 10 个左右。

**1. 科研主流程**(来源:Academic Research Skills)

安装:
- deep-research
- academic-paper
- academic-paper-reviewer

| Skill | 用途 |
| --- | --- |
| deep-research | 构思、论文扫描、文献综述、事实核验 |
| academic-paper | 论文计划、提纲、写作、引用检查 |
| academic-paper-reviewer | 方法审查、模拟同行评审、复审 |

该仓库提供 socratic、three-way-scan、lit-review、fact-check、citation-check、methodology-focus、re-review 等模式(Mode Registry)。

**2. 论文和文件处理**(来源:Anthropic Skills)

安装:
- pdf(读取论文、提取章节)
- xlsx(处理实验表格)

如果你的论文都使用 arXiv HTML 或 Markdown,pdf 的使用频率会降低,但仍建议安装。

**3. RAG 技术实现**(来源:Orchestra AI Research Skills)

安装:
- sentence-transformers
- faiss
- academic-plotting

二选一:
- weights-and-biases
- mlflow

建议选择 **mlflow**,原因是可以完全在本地运行。如果你更习惯云端看图表,可以选择 W&B。

暂时不安装:qdrant、pinecone、langchain、crewai、autogpt、autoresearch。20 天项目使用 FAISS 已经足够。

**4. 通用科研 Skills**(来源:K-Dense Scientific Agent Skills)

安装:
- paper-lookup
- scientific-visualization

如果已经使用 deep-research lit-review,就不要同时使用 K-Dense 的完整 literature-review 生成第二套文献综述。

**5. 项目专属 Skills**(自己创建)

- rag-experiment:保证每次实验完整记录;
- rag-error-analysis:区分解析、检索、重排和生成错误;
- novelty-audit:限制 AI 随意声称创新;
- project-review:每天结束时检查项目状态。

其中最重要的是 **rag-experiment**。

---

## 四、MCP 配置建议

最多配置 4 个。

**必选或强烈推荐**

1. **GitHub MCP**:查看 Issue、管理任务、查看 PR、检查 CI、远程读取仓库。优先使用 GitHub 官方实现(GitHub MCP Server)。只给当前仓库权限,不要给整个 GitHub 账号的高权限 Token。

2. **Context7 MCP**:查询当前版本库文档;检查 FAISS、Sentence Transformers、Gradio 等 API;避免 Agent 使用过时写法。Codex 官方 MCP 文档将 Context7、GitHub 和 Playwright 等列为常见集成。

**可选**

3. **Zotero MCP**:只在你已经使用 Zotero 时安装。用途:查找本地论文、获取元数据、整理论文笔记。

4. **arXiv MCP**:检索论文、获取 arXiv 元数据、下载论文。

如果配置 MCP 超过一个小时,直接放弃可选项,使用 arXiv 网站和 Zotero 即可。

---

## 五、Claude Code 与 Codex 分工

**Claude Code 作为"主研究员和架构师"**,负责:
- 维护项目总体状态;
- 阅读论文;
- 生成文献矩阵;
- 分析创新候选;
- 设计系统架构;
- 分析失败案例;
- 重构跨模块代码;
- 撰写实验报告;
- 模拟审稿。

**Codex 作为"实现和测试工程师"**,负责:
- 实现数据加载器;
- 实现 Chunking;
- 实现 FAISS Retriever;
- 实现 BM25 与 RRF;
- 实现指标;
- 编写 pytest;
- 修复明确 Bug;
- 编写 CLI;
- 检查实验代码。

**并行规则**:不要让 Claude Code 和 Codex 同时修改同一个文件。

推荐:
- Claude Code:主分支或 feature/architecture
- Codex:feature/retriever、feature/evaluation 等独立分支
- 或者使用 Git Worktree。

**每次任务遵循**:

```
你创建 Issue
→ Agent 输出计划
→ 你确认
→ Agent 实现
→ Agent 运行测试
→ 你查看 Diff
→ 你手工运行
→ Git 提交
```

---

## 六、项目目录

```
rag-paper-assistant/
├── README.md
├── PROJECT_STATE.md
├── requirements.txt
├── .env.example
├── configs/
│   ├── dense.yaml
│   ├── hybrid.yaml
│   └── hybrid_rerank.yaml
├── data/
│   ├── raw/
│   │   └── papers/
│   ├── processed/
│   └── evaluation/
├── research/
│   ├── scope/
│   ├── paper_cards/
│   ├── literature_matrix.csv
│   ├── synthesis.md
│   ├── novelty_audit.md
│   └── experiment_plan.md
├── src/
│   ├── ingestion/
│   │   ├── loaders.py
│   │   ├── cleaner.py
│   │   └── splitter.py
│   ├── retrieval/
│   │   ├── dense.py
│   │   ├── bm25.py
│   │   ├── fusion.py
│   │   └── reranker.py
│   ├── generation/
│   │   ├── prompts.py
│   │   └── generator.py
│   ├── evaluation/
│   │   ├── retrieval_metrics.py
│   │   ├── generation_metrics.py
│   │   └── error_analysis.py
│   └── pipeline.py
├── scripts/
│   ├── build_index.py
│   ├── query.py
│   ├── run_experiment.py
│   └── evaluate.py
├── tests/
├── outputs/
│   ├── experiments/
│   ├── figures/
│   └── logs/
├── paper/
│   ├── outline.md
│   ├── manuscript.md
│   └── references.bib
└── app.py
```

---

## 七、每天统一工作流程

**每天开始**:

```
1. 阅读 PROJECT_STATE.md
2. 阅读当天 GitHub Issue
3. 确认当天唯一主要目标
4. 调用一个主要 Skill
5. Agent 先输出计划
6. 你确认后再执行
```

**每天结束**:

```
1. 运行测试
2. 保存实验或研究产物
3. 使用 project-review 检查
4. 更新 PROJECT_STATE.md
5. Git 提交
6. 写 100～300 字实验日志
```

不要一天同时推进论文检索、代码重构、前端和论文写作四件事。

---

## 八、完整 20 天计划

### Day 1:搭建项目和科研工作区

**目标**:搭好环境,不研究复杂方法。

**使用**:Claude Code;GitHub MCP;project-review;暂时不使用 deep-research。

**任务**:
- 创建 GitHub 仓库;
- 创建目录结构;
- 创建虚拟环境;
- 安装基础依赖;
- 配置 Skills;
- 配置 GitHub MCP 和 Context7;
- 创建 GitHub Project 或 Issues;
- 创建 PROJECT_STATE.md。

**GitHub Issues**:
- #1 Literature collection
- #2 Paper parsing
- #3 Dense baseline
- #4 Evaluation dataset
- #5 Hybrid retrieval
- #6 Reranker
- #7 Ablation study
- #8 Demo
- #9 Research report

**当天产物**:README.md、PROJECT_STATE.md、项目目录、GitHub Issues。

**结束 Prompt**:使用 project-review Skill 检查当前仓库。检查:① 目录是否合理;② 是否存在密钥;③ 环境能否正常启动;④ README 是否说明项目目标;⑤ 接下来 19 天是否存在明显风险。只输出检查报告,不自动修改文件。

### Day 2:确定研究问题

**目标**:确定项目主问题和可验证假设。

**使用**:deep-research:socratic 模式;novelty-audit:暂时只建立模板。

**Prompt**:使用 deep-research 的 socratic 模式指导收缩 RAG 研究问题。限制:总时间 20 天;单机运行;论文知识库 10～15 篇;不训练大模型;可以使用 Embedding 和 Reranker;需要完成可复现实验。重点考虑:Dense 与 Hybrid Retrieval;Reranker;Chunking;Top-K;引用正确性。通过提问帮助形成:① 一个主要研究问题;② 两个附加问题;③ 三到四个可证伪假设;④ 最小实验范围;⑤ 主要风险。不要直接声称存在创新。

**推荐冻结的研究问题**:
- RQ1:Dense、Hybrid 和 Hybrid+Reranker 在小规模 RAG 论文知识库上的检索质量和生成质量有何差异?
- RQ2:固定 Token 切块和章节感知切块有何差异?
- RQ3:Top-K 增加是否一定提高回答质量?

**当天产物**:`research/scope/research_questions.md`、`research/scope/hypotheses.md`。

**人工关卡**:你亲自确认研究问题,不让 Skill 自动决定。

### Day 3:快速检索核心论文

**目标**:找到 10～15 篇可靠论文。

**使用**:deep-research:three-way-scan;paper-lookup;Zotero;arXiv/Semantic Scholar;可选 arXiv MCP。

**Prompt**:使用 deep-research 的 three-way-scan 和 paper-lookup,围绕以下主题查找种子论文:Retrieval-Augmented Generation、Dense Passage Retrieval、Hybrid Retrieval、Reranking for RAG、RAG Evaluation、Chunking for RAG、Long Context。按 WHY/HOW/WHAT 整理。要求:① 核验标题、作者和 arXiv/DOI;② 优先原始论文和正式论文;③ 输出 15 篇以内;④ 标记奠基论文、综述、方法论文和评估论文;⑤ 不得生成无法验证的引用。

**推荐论文**:至少包含 RAG 原始论文、DPR、RAG Survey、Lost in the Middle、Ragas、HyDE、CRAG、CRUD-RAG、一两篇 Reranker 或 Hybrid Retrieval 工作。

**当天产物**:`research/literature_matrix.csv`、Zotero/RAG 项目集合、`data/raw/papers/`。

### Day 4:精读三篇基础论文

**目标**:真正理解 RAG、DPR 和评估。

**使用**:pdf;deep-research:review 或 three-way-scan。

**精读**:① RAG;② DPR;③ RAG Survey。

**Prompt**:使用 pdf Skill 读取论文。生成 Paper Card:① 研究问题;② 现有方法不足;③ 核心方法;④ 输入和输出;⑤ 训练方式;⑥ 推理方式;⑦ 数据集;⑧ 指标;⑨ 主要结果;⑩ 局限性;⑪ 与我的项目关系。每一项必须标注页码或章节。论文未明确说明的内容标记为"论文未明确说明"。

**当天产物**:`research/paper_cards/rag.md`、`research/paper_cards/dpr.md`、`research/paper_cards/rag_survey.md`。

### Day 5:文献综合与创新点审计

**目标**:找到适合小项目的"研究贡献",不要强行发明算法。

**使用**:deep-research:lit-review;deep-research:fact-check;novelty-audit。

**推荐贡献定位**:实验型贡献(系统比较 Dense、Hybrid、Reranker);评估型贡献(同时评估检索质量、答案忠实度、引用正确率和拒答率);分析型贡献(对失败案例进行分层归因)。不要声称"首次提出新的 RAG 框架"。

**Prompt**:使用 lit-review 模式综合 literature_matrix.csv 和 paper_cards。分析:① 现有工作如何比较 Dense 和 Sparse;② 是否使用 Reranker;③ 如何评估检索;④ 如何评估 Faithfulness;⑤ Chunking 通常如何设置;⑥ 还有哪些没有充分报告的变量。然后使用 novelty-audit 检查候选贡献。所有结论分为:文献明确支持 / 合理推断 / 尚未验证。

**当天产物**:`research/synthesis.md`、`research/novelty_audit.md`、`research/experiment_plan.md`。

**人工关卡**:冻结研究问题、Baseline、主要实验、指标、不做的内容。

### Day 6:处理论文语料

**目标**:把论文转换成结构化知识库。

**使用**:pdf;Claude Code;Codex;Context7 MCP。

**Claude Code 负责**设计文档对象:

```json
{
  "paper_id": "rag_2020",
  "title": "论文标题",
  "section": "3. Method",
  "page": 5,
  "text": "文本内容",
  "source": "arXiv URL"
}
```

**Codex 负责**编写 Loader、编写清洗函数、编写元数据测试。

**当天验收**:10～15 篇论文成功解析;章节信息存在;文本顺序基本正确;没有大量页眉页脚;Chunk 来源可追踪。

**当天产物**:`data/processed/documents.jsonl`、`src/ingestion/loaders.py`、`src/ingestion/cleaner.py`、`tests/test_loaders.py`。

### Day 7:实现两种 Chunking

**目标**:实现 A:固定 Token 切块;B:章节感知切块。

**使用**:Claude Code:设计接口;Codex:实现与测试;Context7:查 Tokenizer API。

**配置**:

```yaml
fixed:
  chunk_size: 512
  overlap: 80

section_aware:
  max_chunk_size: 512
  overlap: 80
```

**测试**:Chunk 不能为空;Chunk ID 唯一;Metadata 不丢失;Section 信息保留;超长章节能继续拆分;短段落能合理合并。

**当天产物**:`src/ingestion/splitter.py`、`tests/test_splitter.py`、`outputs/chunk_statistics.json`。

### Day 8:Dense Retrieval Baseline

**目标**:完成不依赖 LangChain 的 Dense Retriever。

**使用**:sentence-transformers;faiss;Claude Code;Codex;Context7。

**Claude Code 负责**:Retriever 接口、配置设计、数据流检查。

**Codex 负责**:Embedding 批处理、FAISS 索引、保存和加载、Top-K 检索、单元测试。

**必须打印**:问题、Chunk ID、论文标题、章节、相似度、原文。

**当天产物**:`src/retrieval/dense.py`、`scripts/build_index.py`、`scripts/query.py`、`tests/test_dense_retriever.py`。

### Day 9:接入 LLM 与引用

**目标**:完成第一个可用 RAG 闭环。

**使用**:Claude Code:Prompt 和架构;Codex:生成接口和解析器。

**流程**:问题 → Dense Top-5 → Prompt → LLM → 答案 → 引用。

**Prompt 要求**:只根据上下文回答;无证据时拒答;不伪造论文;返回论文和章节;引用必须对应真实 Chunk ID。

**当天产物**:`src/generation/prompts.py`、`src/generation/generator.py`、`src/pipeline.py`。

**验收**:终端能够完成 `python scripts/query.py --question "RAG-Sequence是什么?"`。

### Day 10:构建评估集与指标

**目标**:建立 40～60 个问题。

**使用**:Claude Code:生成候选问题;Codex:实现指标;pdf:检查标准答案。

AI 可以生成问题候选,但标准答案和相关 Chunk 必须由你人工确认。

**问题组成**:

| 类型 | 数量 |
| --- | --- |
| 事实型 | 15 |
| 方法理解型 | 10 |
| 论文对比型 | 10 |
| 跨章节型 | 5 |
| 无答案型 | 10 |

**指标**:Hit@1、Hit@3、Hit@5、MRR、平均延迟、拒答率。

**当天产物**:`data/evaluation/questions.jsonl`、`src/evaluation/retrieval_metrics.py`、`tests/test_metrics.py`。

**重要规则**:Skill 和 Agent 不得修改 `reference_answer`、`relevant_chunk_ids`、`answerable`,除非你人工批准。

### Day 11:运行 Dense Baseline

**目标**:获得第一组正式结果。

**使用**:rag-experiment;MLflow 或 W&B。

**实验配置**:retrieval=dense;chunking=fixed_512;top_k=5;reranker=false。

**Prompt**:使用 rag-experiment 运行 Dense Baseline。要求:① 保存实验配置;② 保存 Git commit;③ 保存逐问题召回结果;④ 计算 Hit@1、Hit@3、Hit@5 和 MRR;⑤ 记录平均延迟;⑥ 不覆盖旧实验;⑦ 不自动修改论文结论。

**当天产物**:`outputs/experiments/e01_dense/`。

### Day 12:实现 BM25 和 Hybrid Retrieval

**目标**:完成 Dense、BM25、Dense + BM25 + RRF。

**使用**:Claude Code:融合设计;Codex:BM25 和 RRF 实现;rag-experiment:运行实验。

**实验**:E2:BM25;E3:Hybrid。

**当天产物**:`src/retrieval/bm25.py`、`src/retrieval/fusion.py`、`outputs/experiments/e02_bm25/`、`outputs/experiments/e03_hybrid/`。

### Day 13:加入 Reranker

**目标**:实现 Hybrid Top-20 → CrossEncoder Reranker → Top-5。

**使用**:sentence-transformers;Claude Code;Codex;rag-experiment。

**实验**:E4:Hybrid + Reranker。

**记录**:精排前排名;精排后排名;Reranker 分数;延迟变化;是否把正确 Chunk 排高或排低。

**当天产物**:`src/retrieval/reranker.py`、`outputs/experiments/e04_hybrid_rerank/`。

### Day 14:Chunk 消融实验

**目标**:比较 256 tokens/overlap 50、512 tokens/overlap 80、Section-aware。

**使用**:rag-experiment;MLflow/W&B。

**控制变量**:保持不变 —— Embedding 模型、Retriever、Top-K、Reranker、评估集。

**当天产物**:`outputs/experiments/e05_chunk_ablation/`。

### Day 15:Top-K、拒答和最终实验

**目标**:完成 Top-K=3、5、8;无答案拒答测试;引用正确率测试。

**使用**:rag-experiment;Ragas 可选。

**指标**:Hit@K;MRR;Faithfulness;引用正确率;无答案拒答率;延迟;可选调用成本。

Ragas 提供 Context Precision、Context Recall、Response Relevancy 和 Faithfulness 等指标,但自动评分需要人工抽查。

**当天产物**:`outputs/experiments/e06_topk/`、`outputs/experiments/final_results.csv`。

### Day 16:错误分析和绘图

**目标**:分析系统为什么失败。

**使用**:rag-error-analysis;scientific-visualization;academic-plotting;Claude Code。

**错误分类**:source_missing、parsing_error、chunking_error、dense_retrieval_error、bm25_error、fusion_error、reranking_error、generation_error、citation_error、evaluation_label_error。

**图表**:① 各方法 Hit@K 对比;② 各方法 MRR 对比;③ Chunk 策略对比;④ 延迟对比;⑤ 错误类型分布。

**当天产物**:`outputs/figures/`、`research/error_analysis.md`、`research/claim_evidence_matrix.csv`。

### Day 17:完成 Gradio Demo

**目标**:让项目可以展示。

**使用**:Claude Code:页面结构;Codex:实现和测试;可选 Playwright MCP。

**页面功能**:选择 Retriever;选择 Top-K;是否使用 Reranker;输入问题;显示回答;显示引用;展开检索 Chunk;显示分数和耗时。

**可选 Playwright 测试**:页面能打开;输入问题能返回回答;引用区域正常;无答案问题能拒答。

**当天产物**:`app.py`、Demo 截图。

### Day 18:写研究报告

**目标**:完成完整初稿。

**使用**:academic-paper:outline-only;academic-paper;ml-paper-writing;academic-plotting。

**先生成提纲**:Introduction → Related Work → System Design → Experimental Setup → Results → Error Analysis → Limitations → Conclusion。

**写作顺序**:Method → Experimental Setup → Results → Error Analysis → Related Work → Introduction → Limitations → Conclusion → Abstract。

**Prompt**:使用 academic-paper 的 outline-only 模式,基于 research_questions.md、synthesis.md、novelty_audit.md、experiment_plan.md、final_results.csv、error_analysis.md、claim_evidence_matrix.csv 建立报告提纲。要求:① 每个 Claim 绑定实验或文献;② 未被支持的结论不得进入摘要;③ 不得生成不存在的实验数字;④ 必须报告负面结果;⑤ 必须包含局限性。

**当天产物**:`paper/outline.md`、`paper/manuscript.md`。

### Day 19:引用检查、审稿和修改

**目标**:模拟一次正式审稿。

**使用**:academic-paper:citation-check;deep-research:fact-check;academic-paper-reviewer:methodology-focus;academic-paper-reviewer:full。

**推荐跨模型**:Claude Code 撰写;Codex 在新上下文中检查代码和实验一致性;academic-paper-reviewer 只读取冻结后的论文。

**检查顺序**:① 引用真实性;② 引用是否支持 Claim;③ 方法与代码是否一致;④ 表格与原始结果是否一致;⑤ 创新声明是否夸大;⑥ Baseline 是否公平;⑦ 是否存在数据泄漏;⑧ 是否可复现。

**当天产物**:`paper/citation_audit.md`、`paper/review_round_1.md`、`paper/revision_matrix.md`、`paper/manuscript_v2.md`。

### Day 20:复现、收尾与展示

**目标**:让别人能够运行项目。

**使用**:project-review;academic-paper-reviewer:re-review;Claude Code;Codex;GitHub MCP。

**从零复现**:重新克隆仓库:安装环境 → 准备论文 → 文档处理 → 构建索引 → 运行评估 → 启动 Demo。

**README 必须包含**:项目背景;系统架构图;环境安装;数据准备;建库命令;查询命令;评估命令;实验结果;错误分析;Demo 截图;局限性;复现说明。

**最终产物**:最终 GitHub 仓库;最终研究报告;Demo;实验数据;3～5 分钟演示视频。

---

## 九、每天阅读论文的安排

每天不需要花太多时间,控制在 60～90 分钟。

| 天数 | 论文 |
| --- | --- |
| Day 3 | RAG 原始论文导论和方法 |
| Day 4 | RAG、DPR、RAG Survey |
| Day 5 | Lost in the Middle |
| Day 6 | Ragas |
| Day 7 | HyDE |
| Day 8 | CRAG |
| Day 9 | CRUD-RAG |
| Day 10 以后 | 与 Hybrid、Reranker、Chunk 相关论文 |

最终精读 6 篇,泛读 5～10 篇即可。

---

## 十、进度落后时怎么砍功能

**优先删除**:Phoenix;Playwright MCP;自动 PDF 上传;Docker;Qdrant;本地大模型;Ragas 自动评分;复杂对话历史。

**不能删除**:Dense Baseline;Hybrid 对比;评估集;检索指标;错误分析;README;实验报告。

如果到 Day 13 还没有完成 Dense 和 Hybrid,就直接取消 Reranker,把精力投入评估和报告。

---

## 十一、Skills 的正确调用方式

不要这样调用:"使用所有科研 Skills,帮我完成今天的研究。"

应该这样:

```
当前阶段:Dense Baseline
当前目标:实现 FAISS Retriever
主要 Skill:sentence-transformers、faiss
输入文件:documents.jsonl
输出文件:dense.py 和测试
禁止事项:不修改评估集,不加入 Reranker,不自动提交
验收条件:Top-K 结果包含 Chunk ID、来源、章节和分数
```

每次只指定:一个阶段、一个主要目标、一到两个主要 Skill、明确输入、明确输出、明确禁止事项、明确验收条件。

**最终的完整协作链路**:

```
deep-research 帮助确定问题和文献
        ↓
paper-lookup / pdf 帮助获取和阅读论文
        ↓
sentence-transformers / faiss 帮助实现 RAG
        ↓
rag-experiment 规范实验
        ↓
rag-error-analysis 分析失败
        ↓
academic-plotting 生成图表
        ↓
academic-paper 生成研究报告
        ↓
fact-check / citation-check 核验事实和引用
        ↓
academic-paper-reviewer 独立审稿
        ↓
project-review 检查最终可复现性
```
