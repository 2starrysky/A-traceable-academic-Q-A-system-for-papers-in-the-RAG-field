"""
E7 结果可视化
=============
读取 e7_prompt_ablation_results.json，生成对比图表。

图表:
  fig7_prompt_ablation.png  — 各子实验 Support Rate 对比柱状图
  fig8_prompt_heatmap.png   — 策略 x 题型 热力图（Score）
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np

# ── 中文字体 ──────────────────────────────────────────────────────────
_FONT_CANDIDATES = [
    "C:/Windows/Fonts/msyh.ttc",
    "C:/Windows/Fonts/simhei.ttf",
    "C:/Windows/Fonts/simsun.ttc",
]
_font_path = None
for fp in _FONT_CANDIDATES:
    if Path(fp).exists():
        _font_path = fp
        break

if _font_path:
    _prop = fm.FontProperties(fname=_font_path)
    plt.rcParams["font.family"] = _prop.get_name()
    fm.fontManager.addfont(_font_path)
else:
    plt.rcParams["font.family"] = "DejaVu Sans"

plt.rcParams["axes.unicode_minus"] = False

OUTPUTS_DIR = ROOT / "outputs"
FIG_DIR = OUTPUTS_DIR / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)


def load_results():
    with open(OUTPUTS_DIR / "e7_prompt_ablation_results.json", encoding="utf-8") as f:
        return json.load(f)


def plot_support_rate_comparison(data: dict):
    """fig7: 各子实验 Support Rate 对比柱状图。"""
    experiments = data["experiments"]

    fig, axes = plt.subplots(2, 3, figsize=(16, 10))
    fig.suptitle("E7 Prompt 设计对比 — Support Rate", fontsize=14, fontweight="bold")

    colors = ["#4C72B0", "#DD8452", "#55A868", "#C44E52", "#8172B3", "#937860"]

    for idx, (exp_id, summary) in enumerate(experiments.items()):
        ax = axes[idx // 3][idx % 3]
        strategies = list(summary.keys())
        support_rates = [summary[s]["support_rate"] for s in strategies]
        partial_rates = [summary[s]["partial_rate"] for s in strategies]
        refuse_rates = [summary[s]["refuse_rate"] for s in strategies]

        x = np.arange(len(strategies))
        width = 0.25

        ax.bar(x - width, support_rates, width, label="Support", color="#55A868")
        ax.bar(x, partial_rates, width, label="Partial", color="#DD8452")
        ax.bar(x + width, refuse_rates, width, label="Refuse", color="#C44E52")

        ax.set_title(f"{exp_id}", fontsize=11, fontweight="bold")
        ax.set_xticks(x)
        ax.set_xticklabels(strategies, rotation=15, ha="right", fontsize=8)
        ax.set_ylabel("Rate (%)")
        ax.set_ylim(0, 100)
        ax.legend(fontsize=7, loc="upper right")
        ax.grid(axis="y", alpha=0.3)

    plt.tight_layout(rect=[0, 0, 1, 0.95])
    out = FIG_DIR / "fig7_prompt_ablation.png"
    fig.savefig(out, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"  [OK] {out.name}")


def plot_score_heatmap(data: dict):
    """fig8: 策略 x 子实验 平均 Score 热力图。"""
    experiments = data["experiments"]

    # 构建矩阵
    all_strategies = []
    seen = set()
    for summary in experiments.values():
        for s in summary:
            if s not in seen:
                all_strategies.append(s)
                seen.add(s)

    matrix = []
    exp_ids = []
    for exp_id, summary in experiments.items():
        exp_ids.append(exp_id)
        row = [summary.get(s, {}).get("avg_score", 0) for s in all_strategies]
        matrix.append(row)

    matrix = np.array(matrix)

    fig, ax = plt.subplots(figsize=(12, 6))
    im = ax.imshow(matrix, cmap="YlOrRd", aspect="auto", vmin=0, vmax=100)

    ax.set_xticks(np.arange(len(all_strategies)))
    ax.set_xticklabels(all_strategies, rotation=30, ha="right", fontsize=9)
    ax.set_yticks(np.arange(len(exp_ids)))
    ax.set_yticklabels(exp_ids, fontsize=10)

    # 标注数值
    for i in range(len(exp_ids)):
        for j in range(len(all_strategies)):
            val = matrix[i, j]
            color = "white" if val > 60 else "black"
            ax.text(j, i, f"{val:.0f}", ha="center", va="center",
                    fontsize=9, color=color, fontweight="bold")

    ax.set_title("E7 策略 x 子实验 平均 Score 热力图", fontsize=13, fontweight="bold")
    fig.colorbar(im, ax=ax, label="Avg Score", shrink=0.8)

    plt.tight_layout()
    out = FIG_DIR / "fig8_prompt_heatmap.png"
    fig.savefig(out, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"  [OK] {out.name}")


def main():
    print("E7 结果可视化")
    data = load_results()

    print("\n生成图表...")
    plot_support_rate_comparison(data)
    plot_score_heatmap(data)
    print("\n[OK] Done")


if __name__ == "__main__":
    main()
