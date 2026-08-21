# E7 Prompt 设计对比实验 — 分析报告

## 实验概述

| 项目 | 内容 |
|------|------|
| 实验 ID | E7 |
| 目标 | 对比不同 Prompt 策略对 RAG 回答质量的影响 |
| 检索基线 | BM25 + 向量混合 Top-5（沿用 E4 结果） |
| LLM | DeepSeek Chat (deepseek-chat) |
| 评估方法 | LLM Judge (SUPPORT/PARTIAL/REFUSE + Score 0-100) |
| 评估集 | 30 题（与 E1-E6 一致） |

---

## 子实验列表

| ID | 变量 | 策略数 |
|----|------|--------|
| E7.1 | Zero-shot / Few-shot / CoT | 3 |
| E7.2 | Few-shot 示例数量 (1/2/3) | 3 |
| E7.3 | 示例选择策略 (随机/相似/主题) | 3 |
| E7.4 | 约束指令 (加/不加) | 2 |
| E7.5 | CoT + 证据引用 (加/不加) | 2 |
| E7.6 | 最优组合 vs 基线 | 2 |

---

## 结果汇总

> 运行 `python scripts/run_e7_prompt_ablation.py` 后填写。

### E7.1 基础 Prompt 对比

| 策略 | Support Rate | Partial Rate | Refuse Rate | Avg Score |
|------|-------------|-------------|-------------|-----------|
| Zero-shot | - | - | - | - |
| Few-shot (2例) | - | - | - | - |
| CoT | - | - | - | - |

**结论**: _待填写_

### E7.2 Few-shot 示例数量

| 策略 | Support Rate | Partial Rate | Refuse Rate | Avg Score |
|------|-------------|-------------|-------------|-----------|
| 1例 | - | - | - | - |
| 2例 | - | - | - | - |
| 3例 | - | - | - | - |

**结论**: _待填写_

### E7.3 示例选择策略

| 策略 | Support Rate | Partial Rate | Refuse Rate | Avg Score |
|------|-------------|-------------|-------------|-----------|
| 随机 | - | - | - | - |
| 语义相似 | - | - | - | - |
| 按主题 | - | - | - | - |

**结论**: _待填写_

### E7.4 约束指令

| 策略 | Support Rate | Partial Rate | Refuse Rate | Avg Score |
|------|-------------|-------------|-------------|-----------|
| 无约束 | - | - | - | - |
| 有约束 | - | - | - | - |

**结论**: _待填写_

### E7.5 CoT + 证据引用

| 策略 | Support Rate | Partial Rate | Refuse Rate | Avg Score |
|------|-------------|-------------|-------------|-----------|
| 纯 CoT | - | - | - | - |
| CoT + 引用 | - | - | - | - |

**结论**: _待填写_

### E7.6 最优组合 vs 基线

| 策略 | Support Rate | Partial Rate | Refuse Rate | Avg Score |
|------|-------------|-------------|-------------|-----------|
| Zero-shot | - | - | - | - |
| 最优组合 | - | - | - | - |

**结论**: _待填写_

---

## 关键发现

1. _待填写_
2. _待填写_
3. _待填写_

## 对系统的建议

- _待填写_

## 产出文件

| 文件 | 说明 |
|------|------|
| `outputs/e7_E7.1.json` | E7.1 原始结果 |
| `outputs/e7_E7.2.json` | E7.2 原始结果 |
| `outputs/e7_E7.3.json` | E7.3 原始结果 |
| `outputs/e7_E7.4.json` | E7.4 原始结果 |
| `outputs/e7_E7.5.json` | E7.5 原始结果 |
| `outputs/e7_E7.6.json` | E7.6 原始结果 |
| `outputs/e7_prompt_ablation_results.json` | 汇总指标 |
| `outputs/system_comparison_e7.csv` | 对比 CSV |
| `outputs/figures/fig7_prompt_ablation.png` | 柱状图 |
| `outputs/figures/fig8_prompt_heatmap.png` | 热力图 |
