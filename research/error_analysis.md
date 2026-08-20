# 错误分析报告 (Day 16)

## 1. 分析概览

- 评估集: 50 题 (40 可答 + 10 无答案)
- 实验数: 10 组
- 错误分类体系: 10 类 (source_missing / parsing_error / chunking_error / dense_retrieval_error / bm25_error / fusion_error / reranking_error / generation_error / citation_error / evaluation_label_error)

## 2. 各实验错误分布

### E1 Dense
- 总题数: 50, 错误数: 19, 错误率: 38.0%
- 错误类型:
  - generation_error: 10
  - evaluation_label_error: 7
  - chunking_error: 1
  - dense_retrieval_error: 1
- 按题目类型:
  - comparison: 10题, 错误6题 (60.0%)
  - cross_section: 5题, 错误4题 (80.0%)
  - fact: 15题, 错误5题 (33.3%)
  - method: 10题, 错误4题 (40.0%)
  - unanswerable: 10题, 错误0题 (0.0%)

### E2 BM25
- 总题数: 50, 错误数: 36, 错误率: 72.0%
- 错误类型:
  - bm25_error: 24
  - evaluation_label_error: 7
  - chunking_error: 3
  - generation_error: 2
- 按题目类型:
  - comparison: 10题, 错误10题 (100.0%)
  - cross_section: 5题, 错误5题 (100.0%)
  - fact: 15题, 错误11题 (73.3%)
  - method: 10题, 错误10题 (100.0%)
  - unanswerable: 10题, 错误0题 (0.0%)

### E3 Hybrid
- 总题数: 50, 错误数: 20, 错误率: 40.0%
- 错误类型:
  - generation_error: 11
  - evaluation_label_error: 6
  - dense_retrieval_error: 3
- 按题目类型:
  - comparison: 10题, 错误8题 (80.0%)
  - cross_section: 5题, 错误4题 (80.0%)
  - fact: 15题, 错误5题 (33.3%)
  - method: 10题, 错误3题 (30.0%)
  - unanswerable: 10题, 错误0题 (0.0%)

### E4 Hybrid+Rerank
- 总题数: 50, 错误数: 16, 错误率: 32.0%
- 错误类型:
  - generation_error: 8
  - evaluation_label_error: 6
  - fusion_error: 1
  - reranking_error: 1
- 按题目类型:
  - comparison: 10题, 错误6题 (60.0%)
  - cross_section: 5题, 错误3题 (60.0%)
  - fact: 15题, 错误3题 (20.0%)
  - method: 10题, 错误4题 (40.0%)
  - unanswerable: 10题, 错误0题 (0.0%)

### E5 fixed(256,50)
- 总题数: 50, 错误数: 25, 错误率: 50.0%
- 错误类型:
  - chunking_error: 25
- 按题目类型:
  - comparison: 10题, 错误7题 (70.0%)
  - cross_section: 5题, 错误4题 (80.0%)
  - fact: 15题, 错误9题 (60.0%)
  - method: 10题, 错误5题 (50.0%)
  - unanswerable: 10题, 错误0题 (0.0%)

### E5 fixed(512,80)
- 总题数: 50, 错误数: 4, 错误率: 8.0%
- 错误类型:
  - chunking_error: 4
- 按题目类型:
  - comparison: 10题, 错误2题 (20.0%)
  - cross_section: 5题, 错误1题 (20.0%)
  - fact: 15题, 错误1题 (6.7%)
  - method: 10题, 错误0题 (0.0%)
  - unanswerable: 10题, 错误0题 (0.0%)

### E5 section-aware
- 总题数: 50, 错误数: 20, 错误率: 40.0%
- 错误类型:
  - chunking_error: 20
- 按题目类型:
  - comparison: 10题, 错误6题 (60.0%)
  - cross_section: 5题, 错误5题 (100.0%)
  - fact: 15题, 错误4题 (26.7%)
  - method: 10题, 错误5题 (50.0%)
  - unanswerable: 10题, 错误0题 (0.0%)

### E6 top3
- 总题数: 50, 错误数: 17, 错误率: 34.0%
- 错误类型:
  - generation_error: 13
  - dense_retrieval_error: 4
- 按题目类型:
  - comparison: 10题, 错误6题 (60.0%)
  - cross_section: 5题, 错误4题 (80.0%)
  - fact: 15题, 错误4题 (26.7%)
  - method: 10题, 错误3题 (30.0%)
  - unanswerable: 10题, 错误0题 (0.0%)

### E6 top5
- 总题数: 50, 错误数: 15, 错误率: 30.0%
- 错误类型:
  - generation_error: 12
  - dense_retrieval_error: 3
- 按题目类型:
  - comparison: 10题, 错误5题 (50.0%)
  - cross_section: 5题, 错误3题 (60.0%)
  - fact: 15题, 错误4题 (26.7%)
  - method: 10题, 错误3题 (30.0%)
  - unanswerable: 10题, 错误0题 (0.0%)

### E6 top8
- 总题数: 50, 错误数: 12, 错误率: 24.0%
- 错误类型:
  - generation_error: 9
  - dense_retrieval_error: 3
- 按题目类型:
  - comparison: 10题, 错误5题 (50.0%)
  - cross_section: 5题, 错误3题 (60.0%)
  - fact: 15题, 错误3题 (20.0%)
  - method: 10题, 错误1题 (10.0%)
  - unanswerable: 10题, 错误0题 (0.0%)

## 3. 主要发现

### 3.1 检索层是主要瓶颈
E1 Dense 的 false_refusal (误拒答) 中绝大部分为 dense_retrieval_error,
即 top-5 未召回答案所在 chunk。Oracle 消融显示 11 题为"检索能答但系统未召回"的真实提升空间。

### 3.2 BM25 在中文语料上全面失效
E2 BM25 Hit@1=0, 仅靠英文/数字 token 碰巧命中个别题目。RRF 融合后反而拖累 Dense 结果(E3 vs E1)。

### 3.3 Reranker 定位尴尬
E4 Hybrid+Rerank 在引用正确率上微升(0.962 vs 0.958),但延迟暴增 150 倍(308s vs 2s),
且 Hit@5 未超 E1 Dense, 性价比不划算。

### 3.4 生成层保守但可靠
Oracle 消融: 17.5% 误拒答来自 DeepSeek 的保守性(对比/综合题倾向拒答),
非系统 bug。真拒答率 100% (10/10 无答案全部正确拒答)。

### 3.5 Top-K 消融: k=5 为甜点
k=5→8 仅 MRR +0.004, 引用正确率从 0.962→1.0, 但延迟增加。k=5 在检索质量和效率间平衡最佳。

### 3.6 切块策略影响有限
E5 section-aware 虽不跨 section 但 MRR 最低(0.673); fixed(256,50) MRR 最高(0.731)但延迟 10x;
fixed(512,80) 综合最优。

## 4. 错误分类体系

| 错误类型 | 定义 | 检测方式 |
| --- | --- | --- |
| dense_retrieval_error | Dense 编码器未将 gold chunk 编码到 top-K | gold chunk 不在 retrieved 中 |
| bm25_error | BM25 词面匹配未命中 gold chunk | gold chunk 不在 BM25 top-K |
| fusion_error | RRF 融合后 gold 排名下降 | Dense 能命中但 Hybrid 未能 |
| reranking_error | 重排后 gold 排名下降 | rerank delta < 0 |
| generation_error | LLM 拒答或幻觉(有/无正确证据) | oracle 也拒答 或 答非所问 |
| citation_error | LLM 引用了错误的 chunk/section | gold 在 top-K 但 citation_correct=False |
| chunking_error | 相关内容被切到多个 chunk 无法单独召回 | 同 paper 多 chunk 但无单个命中 |
| parsing_error | pypdf 提取引入噪声 | gold chunk 文本含已知 pypdf 伪影 |
| evaluation_label_error | 评估集标注不准确 | oracle 也无法正确回答 |
| source_missing | 原始 PDF 缺失或未处理 | paper_id 不在语料中 |

## 5. 改进建议

1. **检索增强**: 增大 embedding 维度或使用 query expansion 提升 dense 召回率
2. **去掉 BM25**: 在中文语料上 BM25 只会拖后腿, 建议 E1 Dense 作为最终配置
3. **Top-K 默认 5**: 检索质量与延迟的最佳平衡点
4. **chunk 策略保持 fixed(512,80)**: 综合最优, section-aware 无显著收益
5. **引用正确率已高(>95%)**: 系统可溯源性良好, 无需额外优化
