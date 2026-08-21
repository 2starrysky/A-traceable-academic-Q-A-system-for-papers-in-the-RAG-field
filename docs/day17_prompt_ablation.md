# Day 17：E7 Prompt 设计对比实验

## 目标
用同一套检索管线（BM25 + 向量混合 Top-5），只改 LLM 的提示词（Prompt），对比不同提示策略的回答质量，找出最优 Prompt 设计。

---

## 实验设计（6 个子实验）

所有子实验共享：BM25+向量混合检索 Top-5 → 送入 LLM → 评估。

| ID | 实验名 | 变量说明 |
|----|--------|----------|
| E7.1 | Zero-shot vs Few-shot vs CoT | **基础对比**：零样本 vs 带示例 vs 思维链 |
| E7.2 | Few-shot 示例数量 | 1 例 / 2 例 / 3 例，其他不变 |
| E7.3 | Few-shot 示例选择策略 | 随机选 vs 语义相似度选 vs 按主题选 |
| E7.4 | 约束指令 | 加「只基于检索内容回答，不要编造」vs 不加 |
| E7.5 | CoT + 证据引用 | 思维链 + 要求标注引用来源 vs 纯 CoT |
| E7.6 | 最优组合 vs 基线 | 最佳 Prompt 组合 vs E1 最佳管线 |

---

## 产出文件清单

| 文件 | 说明 |
|------|------|
| `scripts/run_e7_prompt_ablation.py` | E7 统一运行脚本 |
| `outputs/prompt_ablation_results.json` | E7.1~E7.5 全部实验原始结果 |
| `outputs/system_comparison_e7.csv` | E7 各实验的 Top-1/Top-3 对比表 |
| `outputs/prompt_analysis_report.md` | E7 分析报告（哪个 Prompt 最优、为什么） |
| `outputs/figures/fig7_prompt_ablation.png` | Prompt 对比柱状图 |
| `outputs/figures/fig8_prompt_heatmap.png` | Prompt × 题型 热力图 |

---

## 关键原则
1. **同一基线**：所有实验用相同的检索结果（或同一检索管线），确保变量唯一
2. **评估一致**：继续用 `evaluate.py` 的逻辑（section-level 判定）
3. **可追溯**：每个子实验的 Prompt 模板存 JSON，结果存结构化文件
