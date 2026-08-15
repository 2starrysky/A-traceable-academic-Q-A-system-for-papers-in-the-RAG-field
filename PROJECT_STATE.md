# PROJECT_STATE

> 此文件跟踪项目进度,供日常开发与 `project-review` 技能参考。**请随进展更新。**
> 完整 20 天计划见 [`research/plan_20days.md`](research/plan_20days.md)(用户人工确认版,以它为准)。

## 当前阶段

- [x] **Day 1 · 搭建项目与科研工作区**(2026-08-12):脚手架 / git / README / PROJECT_STATE / configs / Skills
- [x] **Day 2 · 确定研究问题**(2026-08-12):RQ1/RQ2/RQ3 + H1~H4 已收敛(`research/scope/`)
- [x] **Day 3 · 快速检索核心论文**(2026-08-13):12 篇定稿 + 文献矩阵 + 论文卡片 + 4 篇 PDF 落盘
- [x] **Day 4 · 精读三篇基础论文**:RAG / DPR / RAG Survey
- [x] **Day 5 · 文献综合与创新点审计**
- [x] **Day 6 · 处理论文语料**
- [x] **Day 7 · 实现两种 Chunking**
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

## Day 5 进展(2026-08-14)

- **研究设计已冻结(用户人工关卡确认)** ✅:RQ1-3、Baseline(E1 Dense)、E1-E6 实验矩阵、指标(双层引用正确率为北极星)、不做范围,全部锁定于 `research/experiment_plan.md`。
- **深读 Lost in the Middle**(Day 5 阅读安排):U 型曲线 + "生成性能早于检索召回饱和"(50 vs 20 篇仅 +1.5%),直接支撑 H4/RQ3 与重排动机。
- **三份产物落盘**:
  - `research/synthesis.md` — 6 个分析问题综合,结论分级(🟢文献明确支持/🟡合理推断/🔴尚未验证);
  - `research/novelty_audit.md` — 3 候选贡献(C1 实验型/C2 评估型/C3 分析型)+ 与 12 篇对照 + 防过度声称清单;结论:新在"组合与评测",不在算法;
  - `research/experiment_plan.md` — E1-E6 矩阵、冻结项、评估集设计、神谕检索归因、可追溯性。
- **先验信心**:H1~H4 均保持 Day 2 原值(用户决定)。H4 虽获 LitM 文献强支撑,用户选择保守保持 5/10,决策已记录于 `hypotheses.md` 各假设"Day 5 记录"。

## Day 5 实验日志(2026-08-14,约 230 字)

Day 5 把 Day 4 的三篇 + Lost in the Middle 的文献底子,综合成研究设计并冻结。深读 LitM 收获最大:U 型位置曲线和"生成饱和早于召回"直接坐实了 RQ3 与重排动机,也让 H4 有了文献方向性支撑。synthesis 把 12 篇按 6 个问题归类,结论分级让我知道哪些是"有出处的"(dense 胜 BM25、重排是标准优化),哪些是"得自己测的"(小语料胜负、章节感知切块、真误拒答拆分)。novelty 审计最关键的一句话:我们的新不在算法,而在"小库+双层引用+拒答拆分+神谕归因"的组合——这守住了不过度声称的底线。用户冻结了设计但选择 H4 信心保持 5/10,尊重保守判断,记录在案。风险提醒自己:Ragas/CRUD/RGB 等 8 篇还是摘要级,Day 6 后要逐篇加深,届时 synthesis 可再升级。

## Day 6 进展(2026-08-15)

- **论文语料处理完成**:12 篇 PDF → `data/processed/documents.jsonl`(1888 条,0 空段,约 73 万字符)。`.gitignore` 忽略 `data/processed/*`,文档库可从 PDF 复现,不入库。
- **文档 schema**(plan 定义):`paper_id/title/section/page/text/source`;粒度=页内段落(空行/章节标题/满行句号结尾切分),source 由 literature_matrix.csv 的 arxiv_id 生成。
- **产物**:`src/ingestion/loaders.py`(元数据/逐页提取/语料校验/组装 Document)、`src/ingestion/cleaner.py`(页眉页脚/页码/arXiv 戳记删除、断行连字符合并、空白折叠、章节检测三模式:层级编号/单层编号+词表/罗马数字)、`scripts/build_documents.py`(生成入口+统计)、`tests/test_loaders.py`(16 项全过)。
- **Codex 不在本机**:Loader/清洗/测试均由本会话实现(用户确认)。
- **质量要点**:页序单调 OK;crudrag ACM 页眉(页码变体)用"数字归一模板"删除清零;参考文献中的 arXiv 引用(合法内容)保留;双栏顺序实测正确(RAG/DPR/colbert/litm)。
- **已知噪声**(Day 16 错误分析可归类,不阻塞):pypdf 超链接乱序(colbert "h/t_tps://…")、表格/图内文本(RAG 架构图、survey TABLE I)、个别 section 名被 pypdf 截行(verifiability "4.3 Citation Precision is Inversely Related to")。

## Day 6 实验日志(2026-08-15,约 240 字)

Day 6 把 12 篇 PDF 转成结构化知识库。最大的坑是 pypdf 提取质量:双栏顺序其实正常,但段落间没有空行,最初只切出 256 条巨型段落,加"满行+句号结尾"启发后才切出 1888 条合理段落;ACM 页眉带页码("111:16 Lyu, et al.")每页都变,精确匹配删不掉,改"数字归一模板"后清零;章节标题识别迭代了三轮(单层编号误判列表项→加词表;survey 的罗马数字全漏→加模式;同行标题+正文→截断)。16 项测试把行为固化。收获:摸清 pypdf 的文本线结构,是 Day 7 section-aware 切块的直接输入。风险:图/表格文本仍是噪声、个别 section 名被截断,已记入已知问题。下一步 Day 7:两种 Chunking。

## Day 7 进展(2026-08-15)

- **两种 Chunking 实现完成**:`src/ingestion/splitter.py` 的 `split_fixed(chunk_size=512, overlap=80)` 与 `split_section_aware(max 512/80)`。token 层滑窗(step = chunk_size - overlap = 432),tiktoken cl100k_base 计数(与 gpt-4o-mini 对齐)。
- **Chunk schema**:`chunk_id`(paper_id-序号,全局唯一)/ paper_id / title / section(主,窗口起始段落)/ sections(覆盖节列表)/ page_start / page_end / text / source / chunking / token_count。
- **产物**:`src/ingestion/splitter.py`、`scripts/build_chunks.py`(生成入口,读 documents.jsonl + 参数)、`tests/test_splitter.py`(10 项,**总计 26 项测试全过**)、`data/processed/chunks_fixed.jsonl`、`data/processed/chunks_section_aware.jsonl`、`outputs/chunk_statistics.json`。
- **统计**:fixed=439 chunks(avg 503.8 token,149 跨 section)、section_aware=505(avg 422,0 跨 section)。窗口 overlap 80 token 已逐对校验;chunk_id 唯一;超长章节组内续拆、短段合并;section-aware 不跨节。
- **已知**:fixed 切块会切断词/句子(固有,token 级);section_aware 存在极短 chunk(min 14 token,来自极短 section,如标题/致谢);两文件均在 `.gitignore` 忽略的 `data/processed/`,可从 documents.jsonl 复现。
- 新增依赖:tiktoken(已装,requirements.txt 登记)。

## Day 7 实验日志(2026-08-15,约 200 字)

Day 7 把 1888 条 document 切成可检索的 chunk。设计上用"段落拼 token 流 + 滑窗"统一两种策略:fixed 整篇滑窗(可跨 section),section-aware 先按 section 分组再组内滑窗(不跨节)。踩了两个坑:①滑窗 `while start<n` 会产生超短尾窗(10 token 流切出 4 块,尾块只有 1 token),改成"覆盖到 n 即停、剩余不足一步不再滑"后正确;②用 tiktoken 重新 encode chunk 文本验证 overlap 失败(判负),因为 decode→strip→re-encode 非无损,最后改用直接校验窗口 token 区间,确认相邻窗口 overlap 恰为 80。收获:section-aware 平均 422 token(fixed 503),说明 section 边界会牺牲填充率换语义完整,这正是 RQ2 要测的权衡。下一步 Day 8:Dense Retrieval Baseline。

## 待办(下一步)

- [x] **Day 3 尾巴**:12 篇 PDF 已全部归入 `data/raw/papers/`
- [x] **Zotero 集合**:用户已手动建"RAG 知识库"集合,12 篇论文(8 已有 + 4 新增)全部就位
- [x] **Day 4 · 精读三篇基础论文**:RAG / DPR / RAG Survey,每篇产出带页码标注的 Paper Card(11 字段),论文未明确说明的内容标"论文未明确说明"
- [x] **Day 5 · 文献综合与创新点审计**:`synthesis.md` + `novelty_audit.md` + `experiment_plan.md`,人工冻结研究问题 / Baseline / 主要实验 / 指标 / 不做内容
- [x] **Day 7 · 实现两种 Chunking**:`src/ingestion/splitter.py`(fixed 512/80 + section-aware)+ `scripts/build_chunks.py` + `tests/test_splitter.py`(10 项)+ `outputs/chunk_statistics.json`;chunk_id 唯一、metadata 不丢、超长章节续拆、短段合并;fixed 439 / section_aware 505 块
- [ ] **Day 8 · Dense Retrieval Baseline**:`src/retrieval/dense.py` + `scripts/build_index.py` + `scripts/query.py` + `tests/test_dense_retriever.py`;bge-m3 embedding 批处理、FAISS 索引、保存/加载、Top-K 检索,打印问题/Chunk ID/论文/章节/相似度/原文

## 已知问题

- Zotero MCP 无"添加条目"工具:12 篇 PDF 现全部由本会话从 arXiv 下载(统一 `paper_id` 命名),与 Zotero 条目彼此独立;Zotero 仅作论文元数据/全文来源。
- 论文卡片命名统一为 `paper_id`(如 rag_lewis2021.md),与 `literature_matrix.csv` 对齐;计划 Day 4 产物的短名(rag.md 等)按此约定执行。
- 部分 venue 未经权威核实(卡片已标注 arXiv 主编号,Day 5 精读时补正)。
