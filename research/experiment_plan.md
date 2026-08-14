# 实验计划

> 生成:2026-08-14(Day 5),精化自 Day 2 占位版 + `research/scope/research_questions.md` + `research/synthesis.md`。
> **状态:已冻结**(Day 5 人工关卡确认 · 2026-08-14)。研究问题、Baseline、主要实验、指标、不做的内容由用户确认;后续实现与实验须以此为准,改动需人工批准。

---

## 1. 目标与假设

**RQ1**(主):三种检索配置(Dense / Hybrid / Hybrid+Reranker)对检索质量与生成质量分别有何差异?
**RQ2**(正式实验):固定 Token(512)与章节感知切块,哪种更适合学术论文 RAG?
**RQ3**(健壮性抽查):Top-K 从 5 增至 8,引用正确率是否一定提升?

对应假设(H1~H4 见 `research/scope/hypotheses.md`),并附**先验信心与可证伪条件**。防确认偏误清单须随实验执行。

## 2. 实验矩阵

| E# | 名称 | 检索配置 | top_k | 切块 | 天 |
|----|------|---------|-------|------|-----|
| E1 | Dense Baseline | dense(bge-m3) | 5 | fixed 512/80 | Day 11 |
| E2 | BM25 | bm25(rank-bm25) | 5 | fixed 512/80 | Day 12 |
| E3 | Hybrid | dense + bm25, RRF 0.5/0.5 | 5 | fixed 512/80 | Day 12 |
| E4 | Hybrid+Rerank | E3 召回 20 → bge-reranker-v2-m3 → 5 | 20→5 | fixed 512/80 | Day 13 |
| E5 | Chunk 消融 | dense | 5 | 256/50 · 512/80 · section-aware | Day 14 |
| E6 | Top-K + 拒答 | E1 配置 | 3/5/8 | fixed 512/80 | Day 15 |

- **E1/E3/E4 各附加一组"神谕检索(oracle)"**:不跑检索器,直接把标注好的标准答案 Chunk 喂给生成器 → 得到"检索完美时的生成天花板"。用于归因(见 §5)。
- E5 控制变量:embedding、retriever、top-k、评估集**全部不变**,只变切块。
- E6 控制变量:同 E1,只变 top_k(3/5/8);拒答测试用无答案题。

## 3. 冻结项(控制变量,全实验不可变)

| 项 | 设定 | 依据 |
|----|------|------|
| Embedding 模型 | `BAAI/bge-m3`(零样本,不微调) | scope §4;novelty_audit C1 |
| 生成模型 | `gpt-4o-mini`,temperature=0.2 | scope §4 |
| 提示词模板 | 只根据上下文回答;无证据拒答;引用对应真实 Chunk ID | scope §4 |
| 引用解析 | 返回论文 + 章节 + Chunk 原文;章节号随 Chunk 由检索器带回,**不由生成器猜** | scope §4(关键) |
| 切块(除 E5) | fixed,size=512,overlap=80 | 对齐 configs 与 plan Day 7 |
| 评估集 | 同一套,人工确认,不随实验改动 | scope §4 |
| 随机种子 / 采样 | 固定,逐题结果全存 | 可追溯 |

## 4. 评估集设计(Day 10 构建)

- **规模**:40~60 题,组成(比例可调):事实型 15 / 方法理解 10 / 论文对比 10 / 跨章节 5 / 无答案 10。
- **每字段**:`question`、`answerable(bool)`、`reference_answer`、`relevant_chunk_ids`、`paper_id`、`section`、`type`。
- **标注铁律**:AI 可生成问题候选;**`reference_answer`、`relevant_chunk_ids`、`answerable` 三项只由用户人工确认**,AI 不得自动修改(plan Day 10)。
- **拒答拆分依据**:`answerable=false` 的无答案题,系统拒答=**真拒答(正确)**;`answerable=true` 但系统拒答=**误拒答(检索失败)**。
- **章节级判定**:引用正确 = 论文对 **且** 章节对,两层都要求;仅论文对不算正确(scope §3)。

## 5. 指标与归因

**检索质量**(E1/E2/E3/E4):Hit@1、Hit@3、Hit@5、MRR。
**生成质量**(各主实验):引用正确率(双层)、Faithfulness、真拒答率、误拒答率、平均延迟。
**归因(神谕消融)**:
- 真实检索的引用正确率 < 神谕检索 → 差距 = **检索失败**贡献;
- 神谕检索本身引用正确率也低 → 问题出在**生成或评估集标注**(需人工复查)。
- Faithfulness 可用 Ragas 自动评分做交叉参考,**但不得作为唯一依据**(novelty_audit:人工双层为金标准)。

## 6. 可追溯性

- 每次实验:先 `git commit` → 跑 `scripts/run_experiment.py` → 产物存 `outputs/experiments/E0X_{config}/`。
- 记录:配置指纹、commit hash、数据(评估集)版本、时间戳、逐题结果 json(question → 检索 top-k → 分数 → 答案 → 引用 → 判定)。
- 不覆盖旧实验(E 编号递增)。

## 7. 风险与预案

| 风险 | 预案 |
|------|------|
| R1 确认偏误(期待"混合更好") | 防确认偏误清单:先写解读再看数据;每个"X 赢了"补"反过来怎么解释" |
| R2 RRF 未必赢 Dense | 如实报告;"混合没赢"是可发表负结果 |
| R3 章节边界解析失败 | 优先解析 + 人工校对;解析不出的论文不硬凑;E5 同时报告"章节解析成功率"以便归因(H3 反直觉预案) |
| R4 人工评估标准漂移 | 双层标准书面化;标注版本可追溯;必要时复标子集 |
| R5 指标打架(检索好但引用错) | 神谕消融强行拆分 |
| R6 LLM-judge 偏见 | Ragas 仅交叉参考,不单独下结论 |

## 8. 明确不做(计划冻结范围外)

- 训练/微调任何模型(含 Embedding、生成器)
- 新检索算法、新的融合/重排方法
- 多模型对比(生成模型固定 gpt-4o-mini)
- 对话历史 / 多轮
- 造新数据集或基准(12 篇为既有知识库)
- 除 Ragas 自动评分抽查外的复杂自动评估

---

*相关文件:`research/scope/research_questions.md`、`research/scope/hypotheses.md`、`research/synthesis.md`、`research/novelty_audit.md`、`configs/{dense,hybrid,hybrid_rerank}.yaml`。*
