# PROJECT_STATE

> 此文件跟踪项目进度。完整 20 天计划见 `research/plan_20days.md`。
> **最终状态:Day 20 全部完成(2026-08-21)。**

## 完成状态

- [x] Day 1 · 搭建项目与科研工作区
- [x] Day 2 · 确定研究问题(RQ1-RQ3 + H1-H4)
- [x] Day 3 · 快速检索核心论文(12 篇定稿)
- [x] Day 4 · 精读三篇基础论文(RAG/DPR/RAG Survey)
- [x] Day 5 · 文献综合与创新点审计
- [x] Day 6 · 处理论文语料(1888 段落)
- [x] Day 7 · 实现两种 Chunking(439/505 块)
- [x] Day 8 · Dense Retrieval Baseline
- [x] Day 9 · 接入 LLM 与引用(第一个 RAG 闭环)
- [x] Day 10 · 构建评估集(50 题)
- [x] Day 11 · 运行 Dense Baseline(E1)
- [x] Day 12 · BM25 + Hybrid(E2/E3)
- [x] Day 13 · Reranker(E4)
- [x] Day 14 · Chunk 消融(E5)
- [x] Day 15 · Top-K 消融(E6) + 最终汇总
- [x] Day 16 · 错误分析 + 图表
- [x] Day 17 · E7 Prompt 消融(替代原计划 Gradio Demo)
- [x] Day 18 · 写研究报告初稿
- [x] Day 19 · 引用检查 + 审稿 + 修订(v2)
- [x] Day 20 · Gradio Demo + README + 收尾

## 最终实验结果(final_results.csv)

| 实验 | Hit@1 | Hit@5 | MRR | 引用正确率 | 误拒答率 | 延迟 |
|------|-------|-------|-----|-----------|---------|------|
| E1 Dense | 0.700 | 0.900 | 0.780 | 0.958 | 0.400 | 2.06s |
| E2 BM25 | 0.000 | 0.125 | 0.045 | 0.800 | 0.875 | 1.08s |
| E3 Hybrid | 0.650 | 0.875 | 0.735 | 0.957 | 0.425 | 1.89s |
| E4 Hybrid+Rerank | 0.675 | 0.875 | 0.767 | 0.962 | 0.350 | 307.83s |

## 研究结论

- **RQ1**: Dense 显著优于 BM25;Hybrid 召回增强但排序略损;Reranker 引用正确率最高但延迟 150 倍
- **RQ2**: 切块策略影响有限(Hit@5: 0.875-0.900);fixed 512/80 综合最优
- **RQ3**: 检索侧 Top-3 即饱和;生成侧越大越准;无 Lost-in-the-Middle 退化
- **E7 Prompt**: 约束指令是最高效杠杆(+26pp Support Rate);组合拳 76.8 vs 基线 46.1

## 最终交付物

| 产物 | 位置 |
|------|------|
| 研究报告 | `paper/manuscript_v2.md` + `references.bib` |
| 论文图表 | `paper/figures/`(5 张) |
| Gradio Demo | `app.py` |
| 实验数据 | `outputs/experiments/`(E1-E6) |
| Prompt 消融 | `outputs/e7_*.json` + `system_comparison_e7.csv` |
| 错误分析 | `outputs/error_analysis.json` + `research/error_analysis.md` |
| Claim-Evidence | `research/claim_evidence_matrix.csv` |
| 学习笔记 | `research/learning_notes.md`(Day 8-20 逐日讲解) |
| 审查报告 | `paper/citation_audit.md` + `review_round_1.md` + `revision_matrix.md` |

## 代码统计

- 测试:81 项全过
- 核心模块:ingestion(2)/retrieval(4)/generation(2)/evaluation(3)/pipeline(1)
- 脚本:build_documents/build_chunks/build_index/query/run_experiment/run_error_analysis/run_chunk_ablation/run_topk/run_e7_prompt_ablation/plot_e7_results
