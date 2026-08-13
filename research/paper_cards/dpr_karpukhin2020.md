# Dense Passage Retrieval for Open-Domain Question Answering

- **paper_id**: dpr_karpukhin2020
- **作者**: Vladimir Karpukhin, Barlas Oğuz, Sewon Min, Patrick Lewis, Ledell Wu, Sergey Edunov, Danqi Chen, Wen-tau Yih
- **年份 / venue**: 2020 / EMNLP 2020
- **arXiv**: https://arxiv.org/abs/2004.04906

## 核心贡献

- 证明稠密检索可以单独用于开放域 QA:双编码器(dual-encoder)从少量问答对学到 query/passage 向量。
- top-20 检索准确率比强 Lucene-BM25 高 9%–19%(绝对),推动端到端 QA 系统刷新多个基准。

## 方法

- query 与 passage 各用一个 BERT 编码成向量,用内积相似度检索。
- 训练用 in-batch negative + 一个 BM25 hard negative,损失为 NLL。
- 每个 passage 独立编码、可预计算,检索阶段用 FAISS。

## 数据集

- Natural Questions、TriviaQA、WebQuestions、CuratedTREC、SQuAD 迁移。

## 对项目可借鉴点

- **dense 检索配置的理论基**:项目 dense 路径(bge-m3 向量检索)正是本文双编码器范式的现代实现。
- "dense vs BM25 对比"是 RQ1 的核心:本文给出了 dense 在开放域 QA 上胜出的经典证据,但小规模、领域内语料上结论未必迁移——正是 H2 要验证的点。
- in-batch negative / hard negative 思想可参考评估集构建。

## 缺陷 / 开放问题

- 需要标注的 query-passage 相关性(本项目用 bge-m3 避开微调,见 HyDE 的零样本路径)。
- 域外泛化与可解释性有限。
