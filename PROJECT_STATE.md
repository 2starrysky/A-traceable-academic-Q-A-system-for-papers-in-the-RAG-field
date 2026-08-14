# PROJECT_STATE

> 此文件跟踪项目进度,供日常开发与 `project-review` 技能参考。**请随进展更新。**
> 完整 20 天计划见 [`research/plan_20days.md`](research/plan_20days.md)(用户人工确认版,以它为准)。

## 当前阶段

- [x] **Day 1 · 搭建项目与科研工作区**(2026-08-12):脚手架 / git / README / PROJECT_STATE / configs / Skills
- [x] **Day 2 · 确定研究问题**(2026-08-12):RQ1/RQ2/RQ3 + H1~H4 已收敛(`research/scope/`)
- [x] **Day 3 · 快速检索核心论文**(2026-08-13):12 篇定稿 + 文献矩阵 + 论文卡片 + 4 篇 PDF 落盘
- [x] **Day 4 · 精读三篇基础论文**:RAG / DPR / RAG Survey
- [ ] **Day 5 · 文献综合与创新点审计**
- [ ] **Day 6 · 处理论文语料**
- [ ] **Day 7 · 实现两种 Chunking**
- [ ] **Day 8 · Dense Retrieval Baseline**
- [ ] **Day 9 · 接入 LLM 与引用**
- [ ] **Day 10 · 构建评估集与指标**
- [ ] **Day 11 · 运行 Dense Baseline**
- [ ] **Day 12 · BM25 和 Hybrid**
- [ ] **Day 13 · Reranker**
- [ ] **Day 14 · Chunk 消融**
- [ ] **Day 15 · Top-K、拒答与最终实验**
- [ ] **Day 16 · 错误分析和绘图**
- [ ] **Day 17 · Gradio Demo**
- [ ] **Day 18 · 写研究报告**
- [ ] **Day 19 · 引用检查、审稿和修改**
- [ ] **Day 20 · 复现、收尾与展示**

## Day 3 进展(2026-08-13)

- 知识库论文清单**定稿 12 篇**(用户确认),见 `research/literature_matrix.csv`、`research/paper_cards/`。
- 结构:检索 3(DPR/HyDE/ColBERT)·生成 3(RAG/FiD/RAG Survey)·检索纠错 1(CRAG)·引用与上下文 2(Lost in the Middle/Verifiability)·评估 3(Ragas/CRUD-RAG/RGB)。
- 补充 4 篇 PDF 已下载至 `data/raw/papers/`(colbert/fid/verifiability/rgb,arXiv 已验证)。Day 3 收尾后 12/12 全部落盘。
- 论文卡片目前为**摘要级**,Day 4 精读 RAG/DPR/RAG Survey 时升级为带页码的版本。

## Day 3 收尾与风险修复(2026-08-13)

- 12 篇论文 PDF 全部落盘 `data/raw/papers/`(arXiv 开放获取,统一 `paper_id` 命名,12/12 魔数校验通过)。
- 统一配置与 20 天计划(以 `plan_20days.md` 为准):overlap 64→80;top_k 10→5;rerank 候选 30/10→20/5;向量库 chromadb→faiss-cpu;Web 框架 streamlit→gradio;`research_questions.md` 方法冻结表 overlap 同步为 80。
- 论文卡片命名定为 `paper_id`(与 `literature_matrix.csv` 对齐)。

## Day 4 进展(2026-08-14)

- **精读三篇基础论文完成**:RAG(rag_lewis2021)/ DPR(dpr_karpukhin2020)/ RAG Survey(rag_survey_gao2024)。
- 三张卡片升级为 **11 字段 + 页码/章节标注**模板;综述的输入输出/训练/推理等未明确项标注"论文未明确说明"。文件命名沿用 paper_id 约定。
- 每张卡片末尾附 **第 12 节"小白大白话讲解"**(非模板,阅读辅助):给 RAG 零基础读者全篇大白话。
- **deep-research three-way-scan 交叉核验**落盘 `research/three_way_scan.md`:WHY/HOW/WHAT 逐篇提取 + 跨论文综合(RAG→DPR 依赖链、Survey 为上位坐标);未发现卡片事实/页码错误,仅 Survey 图 2 页码 p.2→p.2-3 精度修正。
- 阅读环境:venv 安装 `pypdf`(已在 requirements.txt 声明);Read 工具因缺 poppler 无法渲染 PDF,改用 pypdf 逐页提取文本。
- **关键洞见**:RAG 图 3(Top-K 峰值)支撑 RQ3;DPR"9–19% 完胜 BM25"但小语料结论未必迁移,支撑 H2;Survey 评估框架(质量分+四能力)对齐项目指标体系。

## Day 4 实验日志(2026-08-14,约 250 字)

Day 4 目标是把三篇基础论文真正读懂。用 pypdf 提取全文后逐页精读,把 RAG/DPR/RAG Survey 三张卡片从"摘要级"升级为"11 字段+页码标注",并给每篇补了大白话讲解(自认 RAG 零基础)。three-way-scan 交叉核验未发现错误,让我对卡片可信度有信心。收获:①RAG 的 RAG-Sequence/Token 与 Top-K 峰值直接支撑项目 RQ3;②DPR 证明稠密检索能完胜 BM25,但结论在 12 篇小语料上未必迁移(正是 H2);③Survey 的评估框架几乎就是项目指标体系的蓝图。风险:三篇都是方法/综述论文,具体数字不能当"绝对真理",Day 5 综合时要注意与评估类论文(Ragas/Verifiability)交叉。下一步:Day 5 文献综合+创新点审计,人工冻结设计。

## 待办(下一步)

- [x] **Day 3 尾巴**:12 篇 PDF 已全部归入 `data/raw/papers/`
- [x] **Zotero 集合**:用户已手动建"RAG 知识库"集合,12 篇论文(8 已有 + 4 新增)全部就位
- [x] **Day 4 · 精读三篇基础论文**:RAG / DPR / RAG Survey,每篇产出带页码标注的 Paper Card(11 字段),论文未明确说明的内容标"论文未明确说明"
- [ ] **Day 5 · 文献综合与创新点审计**:`synthesis.md` + `novelty_audit.md` + `experiment_plan.md`,人工冻结研究问题 / Baseline / 主要实验 / 指标 / 不做内容

## 已知问题

- Zotero MCP 无"添加条目"工具:12 篇 PDF 现全部由本会话从 arXiv 下载(统一 `paper_id` 命名),与 Zotero 条目彼此独立;Zotero 仅作论文元数据/全文来源。
- 论文卡片命名统一为 `paper_id`(如 rag_lewis2021.md),与 `literature_matrix.csv` 对齐;计划 Day 4 产物的短名(rag.md 等)按此约定执行。
- 部分 venue 未经权威核实(卡片已标注 arXiv 主编号,Day 5 精读时补正)。
