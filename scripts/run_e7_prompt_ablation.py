"""
E7 — Prompt 设计对比实验
========================
同一检索管线(BM25+向量混合 Top-5，沿用 E4 结果)，只改 LLM 提示词，对比回答质量。

子实验:
  E7.1  Zero-shot / Few-shot(2例) / CoT 三档对比
  E7.2  Few-shot 示例数量: 1 / 2 / 3 例
  E7.3  Few-shot 示例选择: 随机 / 语义相似 / 按主题
  E7.4  约束指令: 加 vs 不加"只基于检索内容回答"
  E7.5  CoT + 证据引用 vs 纯 CoT
  E7.6  最优组合 vs 基线(Zero-shot)

用法:
  python scripts/run_e7_prompt_ablation.py                  # 全量运行
  python scripts/run_e7_prompt_ablation.py --experiments E7.1  # 只跑某个子实验
  python scripts/run_e7_prompt_ablation.py --resume         # 断点续跑
"""

from __future__ import annotations

import json
import os
import sys
import time
import random
from pathlib import Path
from typing import List, Dict, Tuple
from collections import defaultdict

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from dotenv import load_dotenv
load_dotenv()

import os as _os
_API_KEY = _os.getenv("DEEPSEEK_API_KEY") or _os.getenv("OPENAI_API_KEY")
_API_BASE = _os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
_MODEL = _os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

if not _API_KEY:
    raise RuntimeError("未找到 LLM API key：请在 .env 设置 DEEPSEEK_API_KEY")

from openai import OpenAI
client = OpenAI(api_key=_API_KEY, base_url=_API_BASE)

# ── 路径 ──────────────────────────────────────────────────────────────
DATA_DIR = ROOT / "data" / "processed"
OUTPUTS_DIR = ROOT / "outputs"
E4_DIR = OUTPUTS_DIR / "experiments" / "e04_hybrid_rerank"

# -- E7 Prompt Ablation

FEW_SHOT_EXAMPLES = [
    {
        "id": "ex1",
        "topic": "retrieval",
        "question": "What is the difference between dense retrieval and sparse retrieval?",
        "answer": (
            "Dense retrieval uses neural encoders to map text into continuous vector spaces "
            "and retrieves via approximate nearest neighbor search, capturing semantic similarity. "
            "Sparse retrieval (e.g., BM25) uses term frequency and inverse document frequency to "
            "match exact or overlapping lexical tokens. Dense methods handle paraphrases better but "
            "require training; sparse methods are interpretable and fast but miss synonyms."
        ),
        "sources": [
            "Dense Passage Retrieval for Open-Domain Question Answering (Karpukhin et al., 2020)",
        ],
    },
    {
        "id": "ex2",
        "topic": "generation",
        "question": "How does Chain-of-Thought prompting improve question answering?",
        "answer": (
            "Chain-of-Thought (CoT) prompting asks the model to generate intermediate reasoning "
            "steps before producing a final answer. This decomposes complex questions into sub-problems, "
            "reduces reasoning errors, and improves accuracy on multi-hop and arithmetic tasks. "
            "CoT works best with large language models (>=100B parameters) and can be combined "
            "with few-shot examples showing the reasoning process."
        ),
        "sources": [
            "Chain-of-Thought Prompting Elicits Reasoning in Large Language Models (Wei et al., 2022)",
        ],
    },
    {
        "id": "ex3",
        "topic": "retrieval",
        "question": "What is hybrid retrieval and why is it effective?",
        "answer": (
            "Hybrid retrieval combines sparse (BM25) and dense (embedding-based) retrieval methods, "
            "typically via reciprocal rank fusion (RRF) or weighted score combination. It is effective "
            "because BM25 excels at exact keyword matching while dense retrieval captures semantic "
            "similarity; together they cover both lexical and semantic search spaces, improving "
            "recall and robustness."
        ),
        "sources": [
            "Hybrid Retrieval with Large Language Models (author, 2024)",
        ],
    },
    {
        "id": "ex4",
        "topic": "reranking",
        "question": "What is cross-encoder reranking in a retrieval pipeline?",
        "answer": (
            "Cross-encoder reranking takes the query and each candidate document as a concatenated "
            "input pair and scores their relevance using a transformer model. Unlike bi-encoders "
            "which encode query and document independently, cross-encoders capture fine-grained "
            "query-document interactions, producing more accurate relevance scores. The trade-off "
            "is computational cost: cross-encoders must score each pair independently, making them "
            "slower than bi-encoders for large candidate sets."
        ),
        "sources": [
            "Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks (Reimers & Gurevych, 2019)",
        ],
    },
    {
        "id": "ex5",
        "topic": "generation",
        "question": "What are the main challenges of hallucination in RAG systems?",
        "answer": (
            "Hallucination in RAG systems occurs when the generated answer contains information "
            "not supported by the retrieved context. Key challenges include: (1) the model relying "
            "on parametric knowledge instead of retrieved documents, (2) insufficient or irrelevant "
            "retrieved context, (3) the model over-generating beyond what the evidence supports. "
            "Mitigation strategies include faithfulness-constrained decoding, retrieval-augmented "
            "verification, and prompt engineering that explicitly instructs the model to cite sources."
        ),
        "sources": [
            "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks (Lewis et al., 2020)",
        ],
    },
]


# ══════════════════════════════════════════════════════════════════════
#  数据加载
# ══════════════════════════════════════════════════════════════════════

def load_chunks() -> Dict[str, Dict]:
    """加载 chunks_fixed.jsonl，返回 {chunk_id: chunk_dict}。"""
    chunks = {}
    path = DATA_DIR / "chunks_fixed.jsonl"
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                c = json.loads(line)
                chunks[c["chunk_id"]] = c
    print(f"  [OK] load {len(chunks)} chunks")
    return chunks


def load_questions() -> List[Dict]:
    """加载 questions.jsonl。"""
    path = ROOT / "data" / "evaluation" / "questions.jsonl"
    qs = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                qs.append(json.loads(line))
    print(f"  [OK] load {len(qs)} questions")
    return qs


def load_e4_results() -> Dict[str, List[Dict]]:
    """
    从 E4 per_question.jsonl 加载检索结果。
    返回 {question_id: [retrieved_chunk_dict, ...]}
    """
    path = E4_DIR / "per_question.jsonl"
    results = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            rec = json.loads(line)
            qid = rec["id"]
            retrieved = rec.get("real", {}).get("retrieved", [])
            results[qid] = retrieved
    print(f"  [OK] load E4 results: {len(results)} questions")
    return results


# ══════════════════════════════════════════════════════════════════════
#  Prompt 构建
# ══════════════════════════════════════════════════════════════════════

def _build_context(retrieved: List[Dict], chunks: Dict[str, Dict], top_k: int = 5) -> str:
    """将检索到的 chunk 拼成带编号的上下文字符串（与 prompts.py 格式一致）。"""
    lines = []
    for i, r in enumerate(retrieved[:top_k], 1):
        cid = r["chunk_id"]
        chunk = chunks.get(cid, {})
        title = chunk.get("title", "未知")
        paper_id = chunk.get("paper_id", "")
        section = chunk.get("section", "")
        page_start = chunk.get("page_start", "?")
        page_end = chunk.get("page_end", "?")
        pages = f"{page_start}-{page_end}" if page_start != page_end else str(page_start)
        text = chunk.get("text", "")[:1500]
        lines.append(f"[{i}] 论文:{title}({paper_id}) | 章节:{section} | 页码:{pages} | Chunk ID:{cid}")
        lines.append(f"原文:{text}")
        lines.append("")
    return "\n".join(lines)


def _format_examples(examples: List[Dict], with_cot: bool = False) -> str:
    """把 few-shot 示例格式化为字符串。"""
    lines = []
    for i, ex in enumerate(examples, 1):
        lines.append(f"示例 {i}:")
        lines.append(f"问题: {ex['question']}")
        if with_cot:
            lines.append(f"思考过程: {ex['answer']}")
        else:
            lines.append(f"回答: {ex['answer']}")
        lines.append(f"来源: {'; '.join(ex['sources'])}")
        lines.append("")
    return "\n".join(lines)


def _get_examples(n: int, strategy: str, question: str = "",
                  pool: List[Dict] = None) -> List[Dict]:
    """根据策略从示例池中选 n 个。"""
    pool = pool or FEW_SHOT_EXAMPLES
    if strategy == "random":
        return random.sample(pool, min(n, len(pool)))
    elif strategy == "similarity":
        q_words = set(question.lower().split())
        scored = [(len(q_words & set(ex["question"].lower().split())), ex) for ex in pool]
        scored.sort(key=lambda x: -x[0])
        return [ex for _, ex in scored[:n]]
    elif strategy == "topic":
        topics = defaultdict(list)
        for ex in pool:
            topics[ex.get("topic", "general")].append(ex)
        selected = []
        for topic_exs in topics.values():
            if len(selected) >= n:
                break
            selected.append(topic_exs[0])
        return selected[:n]
    else:
        return pool[:n]


# ── 系统提示词（与 prompts.py 一致） ──
SYSTEM_PROMPT = (
    "你是一个学术问答助手，回答必须严格基于下面给出的论文片段（检索上下文）。\n"
    "硬性要求：\n"
    "1. 只能依据上下文中的内容回答，不得使用上下文之外的知识。\n"
    "2. 如果上下文不足以回答问题，直接回答\"无法从给定材料中回答\"，不要编造。\n"
    "3. 不得编造论文、章节或页码；章节与页码一律以上下文标注为准。\n"
    "4. 回答用中文。\n"
    "5. 引用来源时，在相应句末用方括号编号标注（编号取上下文各片段的编号，如 [1]、[2]），"
    "不要自创编号之外的来源。"
)


def build_user_prompt(question: str, context: str, strategy: str, **kwargs) -> str:
    """
    根据策略名称构建完整 user prompt。

    strategy 命名规则:
      zero_shot              — 无示例，无 CoT
      few_shot_{n}_{sel}     — n 例，sel = random/similarity/topic
      cot                    — CoT（无示例）
      few_shot_cot_{n}_{sel} — CoT + few-shot
      constrained            — 加约束指令
      cot_cite               — CoT + 要求标注引用来源
      optimal                — 最优组合 (few_shot_cot_2_similarity + constrained + cite)
    """
    n_examples = kwargs.get("n_examples", 2)
    selection = kwargs.get("selection", "similarity")
    constrain = kwargs.get("constrain", False)
    cite = kwargs.get("cite", False)

    parts = []

    # ── 约束前缀 ──
    if constrain:
        parts.append(
            "【重要指令】你必须完全基于下方提供的检索内容来回答问题。"
            "如果检索内容中没有足够信息，请明确说明「根据检索内容无法完全回答」。"
            "绝对不要编造或使用你的训练知识来补充答案。"
        )
        parts.append("")

    # ── Few-shot 示例 ──
    if "few_shot" in strategy or "optimal" in strategy:
        with_cot = "cot" in strategy or "optimal" in strategy
        if "optimal" in strategy:
            n_examples = 2
            selection = "similarity"
        examples = _get_examples(n_examples, selection, question)
        parts.append("以下是参考示例：")
        parts.append(_format_examples(examples, with_cot=with_cot))
        parts.append("")

    # ── CoT 引导 ──
    if "cot" in strategy or "optimal" in strategy:
        parts.append("请先逐步分析检索内容中的相关信息，然后给出回答。")
        parts.append("")

    # ── 引用要求 ──
    if cite or "cite" in strategy or "optimal" in strategy:
        parts.append("请在回答中用 [1][2][3] 等编号标注信息来源。")
        parts.append("")

    # ── 检索上下文 + 问题 ──
    parts.append("以下是检索到的论文片段（带编号）：")
    parts.append("")
    parts.append(context)
    parts.append("")
    parts.append(f"问题：{question}")
    parts.append("")
    parts.append("请依据上面的片段回答，并在引用处用 [编号] 标注。")

    return "\n".join(parts)


# ══════════════════════════════════════════════════════════════════════
#  LLM 调用
# ══════════════════════════════════════════════════════════════════════

def call_llm(prompt: str, max_retries: int = 3) -> str:
    """调用 LLM，带重试。"""
    for attempt in range(max_retries):
        try:
            resp = client.chat.completions.create(
                model=_MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.1,
                max_tokens=2048,
            )
            return resp.choices[0].message.content.strip()
        except Exception as e:
            if attempt < max_retries - 1:
                wait = 2 ** (attempt + 1)
                print(f"    [!] API error: {e}, retry in {wait}s...")
                time.sleep(wait)
            else:
                print(f"    [X] API failed: {e}")
                return f"[ERROR] {e}"


# ══════════════════════════════════════════════════════════════════════
#  Section-level 评估（复用项目 evaluate 逻辑）
# ══════════════════════════════════════════════════════════════════════

EVAL_SYSTEM = (
    "你是一个严格的学术评审专家。你需要判断模型的回答是否正确。\n"
    "逐条检查回答中的每个论断（claim），对照标准答案和来源论文，判断每个论断是否被支持。\n\n"
    "对每个论断给出以下判定之一：\n"
    "- SUPPORT：该论断被来源论文明确支持\n"
    "- PARTIAL：该论断部分正确但不完整或有偏差\n"
    "- REFUSE：该论断无法被来源论文支持，属于编造或错误\n\n"
    "然后给出整体判定（overall），判定规则：\n"
    "- 如果所有论断都是 SUPPORT → overall = SUPPORT\n"
    "- 如果有任何论断是 PARTIAL 但没有 REFUSE → overall = PARTIAL\n"
    "- 如果有任何论断是 REFUSE → overall = REFUSE\n\n"
    '严格按以下 JSON 格式输出（不要输出任何其他内容）：\n'
    '{"claims": [{"claim": "论断内容", "verdict": "SUPPORT/PARTIAL/REFUSE", "reason": "简短理由"}],'
    ' "overall": "SUPPORT/PARTIAL/REFUSE",'
    ' "score": 0-100}'
)


def eval_single(question: str, answer: str, reference: str,
                evidence_list: List[str]) -> Dict:
    """用 LLM 评估单个回答（section-level 判定）。"""
    eval_prompt = f"""请评估以下回答的质量。

问题：{question}

模型回答：
{answer}

标准答案：
{reference}

来源论文证据：
{chr(10).join(f'证据{i+1}: {e[:500]}' for i, e in enumerate(evidence_list))}

{EVAL_SYSTEM}"""

    # 评估用纯 user 消息（不加学术助手 system prompt）
    for attempt in range(3):
        try:
            resp = client.chat.completions.create(
                model=_MODEL,
                messages=[{"role": "user", "content": eval_prompt}],
                temperature=0.0,
                max_tokens=1024,
            )
            text = resp.choices[0].message.content.strip()
            break
        except Exception as e:
            if attempt < 2:
                time.sleep(2 ** (attempt + 1))
            else:
                return {"overall": "ERROR", "score": 0, "claims": [], "raw": str(e)}
    else:
        return {"overall": "ERROR", "score": 0, "claims": [], "raw": "max retries"}

    try:
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            return json.loads(text[start:end])
    except json.JSONDecodeError:
        pass
    return {"overall": "PARSE_ERROR", "score": 0, "claims": [], "raw": text}


# ══════════════════════════════════════════════════════════════════════
#  子实验定义
# ══════════════════════════════════════════════════════════════════════

EXPERIMENTS = {
    "E7.1": {
        "name": "基础 Prompt 对比",
        "desc": "Zero-shot / Few-shot(2例) / CoT 三档",
        "strategies": [
            ("zero_shot", "Zero-shot", {}),
            ("few_shot_2_similarity", "Few-shot (2例)", {"n_examples": 2, "selection": "similarity"}),
            ("cot", "Chain-of-Thought", {}),
        ],
    },
    "E7.2": {
        "name": "Few-shot 示例数量",
        "desc": "1例 / 2例 / 3例",
        "strategies": [
            ("few_shot_1_similarity", "Few-shot 1例", {"n_examples": 1, "selection": "similarity"}),
            ("few_shot_2_similarity", "Few-shot 2例", {"n_examples": 2, "selection": "similarity"}),
            ("few_shot_3_similarity", "Few-shot 3例", {"n_examples": 3, "selection": "similarity"}),
        ],
    },
    "E7.3": {
        "name": "示例选择策略",
        "desc": "随机 / 语义相似 / 按主题",
        "strategies": [
            ("few_shot_2_random", "随机选择", {"n_examples": 2, "selection": "random"}),
            ("few_shot_2_similarity", "语义相似", {"n_examples": 2, "selection": "similarity"}),
            ("few_shot_2_topic", "按主题选择", {"n_examples": 2, "selection": "topic"}),
        ],
    },
    "E7.4": {
        "name": "约束指令",
        "desc": "加 vs 不加[只基于检索内容]",
        "strategies": [
            ("zero_shot", "无约束", {}),
            ("constrained", "有约束指令", {"constrain": True}),
        ],
    },
    "E7.5": {
        "name": "CoT + 证据引用",
        "desc": "CoT+引用 vs 纯 CoT",
        "strategies": [
            ("cot", "纯 CoT", {}),
            ("cot_cite", "CoT + 证据引用", {"cite": True}),
        ],
    },
    "E7.6": {
        "name": "最优组合 vs 基线",
        "desc": "最优 Prompt vs Zero-shot",
        "strategies": [
            ("zero_shot", "Zero-shot (基线)", {}),
            ("optimal", "最优组合", {"constrain": True, "cite": True}),
        ],
    },
}


# ══════════════════════════════════════════════════════════════════════
#  主运行逻辑
# ══════════════════════════════════════════════════════════════════════

def run_experiment(
    exp_id: str,
    exp_def: Dict,
    questions: List[Dict],
    chunks: Dict[str, Dict],
    e4_results: Dict[str, List[Dict]],
    resume: bool = False,
) -> List[Dict]:
    """运行单个子实验，返回结果列表。"""
    exp_name = exp_def["name"]
    out_file = OUTPUTS_DIR / f"e7_{exp_id}.json"

    # 断点续跑
    done = {}
    if resume and out_file.exists():
        with open(out_file, encoding="utf-8") as f:
            for r in json.load(f):
                done[r["question_id"]] = r
        print(f"  续跑: 已有 {len(done)} 题结果")

    results = []
    n_strategies = len(exp_def["strategies"])

    for qi, q in enumerate(questions):
        q_id = q["id"]

        # 已有结果就跳过（整个题的所有策略）
        if q_id in done:
            # 把之前的结果加入
            prev = [r for r in json.load(open(out_file, encoding="utf-8"))
                    if r["question_id"] == q_id]
            results.extend(prev)
            continue

        # 获取 E4 检索结果
        retrieved = e4_results.get(q_id, [])
        if not retrieved:
            for _, strat_label, _ in exp_def["strategies"]:
                results.append({
                    "question_id": q_id, "question": q["question"],
                    "answer": "", "eval": {"overall": "NO_CANDIDATES", "score": 0},
                    "strategy": "none", "strategy_label": strat_label,
                })
            continue

        # 构建上下文
        context = _build_context(retrieved, chunks, top_k=5)
        evidence_list = [chunks.get(r["chunk_id"], {}).get("text", "")[:500]
                         for r in retrieved[:5]]

        # 对每个策略生成回答并评估
        for strategy_key, strategy_label, params in exp_def["strategies"]:
            user_prompt = build_user_prompt(q["question"], context, strategy_key, **params)
            answer = call_llm(user_prompt)
            eval_result = eval_single(
                q["question"], answer, q.get("reference_answer", ""),
                evidence_list,
            )
            results.append({
                "question_id": q_id,
                "question": q["question"],
                "strategy": strategy_key,
                "strategy_label": strategy_label,
                "answer": answer,
                "eval": eval_result,
            })
            time.sleep(0.3)  # 控速

        done_count = len(results)
        print(f"  [{done_count:3d}] Q{qi+1:02d} "
              f"({', '.join(s[1] for s in exp_def['strategies'])})")

        # 每 10 题存断点
        if (qi + 1) % 10 == 0:
            with open(out_file, "w", encoding="utf-8") as f:
                json.dump(results, f, ensure_ascii=False, indent=2)

    # 最终保存
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"  [OK] saved: {out_file.name} ({len(results)} records)")
    return results


def compute_metrics(results: List[Dict]) -> Dict:
    """计算子实验指标。"""
    metrics = defaultdict(lambda: {"support": 0, "partial": 0, "refuse": 0,
                                    "error": 0, "total": 0, "score_sum": 0})
    for r in results:
        s = r.get("strategy", "unknown")
        overall = r.get("eval", {}).get("overall", "ERROR")
        score = r.get("eval", {}).get("score", 0)
        metrics[s]["total"] += 1
        metrics[s]["score_sum"] += score
        key = overall.lower()
        if key in ("support", "partial", "refuse"):
            metrics[s][key] += 1
        else:
            metrics[s]["error"] += 1

    summary = {}
    for strat, m in metrics.items():
        t = m["total"]
        summary[strat] = {
            "total": t,
            "support_rate": round(m["support"] / t * 100, 1) if t else 0,
            "partial_rate": round(m["partial"] / t * 100, 1) if t else 0,
            "refuse_rate": round(m["refuse"] / t * 100, 1) if t else 0,
            "error_rate": round(m["error"] / t * 100, 1) if t else 0,
            "avg_score": round(m["score_sum"] / t, 1) if t else 0,
        }
    return summary


def main():
    import argparse
    parser = argparse.ArgumentParser(description="E7 Prompt 设计对比实验")
    parser.add_argument("--experiments", nargs="*", default=None,
                        help="指定子实验 ID，如 E7.1 E7.2；默认全部")
    parser.add_argument("--resume", action="store_true", help="断点续跑")
    args = parser.parse_args()

    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("E7 — Prompt 设计对比实验")
    print("=" * 60)

    # 加载数据
    print("\n加载数据...")
    chunks = load_chunks()
    questions = load_questions()
    e4_results = load_e4_results()

    # 选实验
    exp_ids = args.experiments or list(EXPERIMENTS.keys())
    print(f"\n运行子实验: {', '.join(exp_ids)}")

    # 逐个实验
    all_results = {}
    for exp_id in exp_ids:
        exp_def = EXPERIMENTS[exp_id]
        print(f"\n{'=' * 50}")
        print(f"> {exp_id}: {exp_def['name']} -- {exp_def['desc']}")
        print(f"  策略: {[s[1] for s in exp_def['strategies']]}")
        results = run_experiment(exp_id, exp_def, questions, chunks,
                                 e4_results, args.resume)
        all_results[exp_id] = results

    # 汇总指标
    print(f"\n{'=' * 60}")
    print("Summary")
    print(f"{'=' * 60}")
    all_summary = {}
    for exp_id, results in all_results.items():
        summary = compute_metrics(results)
        all_summary[exp_id] = summary
        print(f"\n{exp_id} ({EXPERIMENTS[exp_id]['name']}):")
        for strat, m in summary.items():
            print(f"  {strat}: Support={m['support_rate']}% "
                  f"Partial={m['partial_rate']}% Refuse={m['refuse_rate']}% "
                  f"AvgScore={m['avg_score']}")

    # 保存汇总
    summary_file = OUTPUTS_DIR / "e7_prompt_ablation_results.json"
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump({
            "experiments": all_summary,
            "raw_results": {k: v for k, v in all_results.items()},
        }, f, ensure_ascii=False, indent=2)
    print(f"\n[OK] summary saved: {summary_file.name}")

    # 生成对比 CSV
    _write_comparison_csv(all_summary)
    print("\n[OK] E7 all done!")


def _write_comparison_csv(all_summary: Dict):
    """写 E7 系统对比表 CSV。"""
    import csv
    rows = []
    for exp_id, summary in all_summary.items():
        exp_name = EXPERIMENTS[exp_id]["name"]
        for strat, m in summary.items():
            rows.append({
                "experiment": exp_id,
                "experiment_name": exp_name,
                "strategy": strat,
                "total_questions": m["total"],
                "support_rate": m["support_rate"],
                "partial_rate": m["partial_rate"],
                "refuse_rate": m["refuse_rate"],
                "error_rate": m["error_rate"],
                "avg_score": m["avg_score"],
            })

    csv_file = OUTPUTS_DIR / "system_comparison_e7.csv"
    with open(csv_file, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"  [OK] CSV: {csv_file.name}")


if __name__ == "__main__":
    main()
