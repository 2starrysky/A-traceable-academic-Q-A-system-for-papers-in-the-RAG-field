# ColBERT: Efficient and Effective Passage Search via Contextualized Late Interaction over BERT

- **paper_id**: colbert_khattab2020
- **作者**: Omar Khattab, Matei Zaharia
- **年份 / venue**: 2020 / SIGIR 2020
- **arXiv**: https://arxiv.org/abs/2004.12832

## 核心贡献

- **晚交互(late interaction)**:query 与 document 各自独立过 BERT,最后用一个廉价且强的相似度交互(MaxSim)建模细粒度匹配。
- 相比 cross-encoder 每对 query-doc 过一次网络,ColBERT 可离线预计算全部 doc 表示,查询时只需编码 query + 检索,快两个数量级、FLOPs 少四个数量级,同时效果与 BERT-based 模型持平。

## 方法

- query 的每个 token 与 doc 的每个 token 分别过 BERT,取逐 token 向量;相似度 = 每个 query token 与其最相似 doc token 的相似度求和(MaxSim)。
- 支持向量索引做端到端稠密检索;也可作为 reranker 对召回结果精排。

## 数据集

- MS MARCO、TREC-DL(两代 passage search)。

## 对项目可借鉴点

- **hybrid_rerank 配置的 reranker 理论基**:项目 rerank 环节(bge-reranker)与 ColBERT 同属"对召回集合精排"这一思想,ColBERT 是这一思想的经典表述。
- 晚交互"每个 token 都参与匹配"适合学术论文里术语密集的文本,是评估集"方法理解"题里对比 rerank 原理的好素材。
- 其"离线预计算 doc 表示"的思路对建索引性能有参考。

## 缺陷 / 开放问题

- doc 逐 token 向量导致存储开销大(比单向量稠密检索贵一个量级)。
- 晚交互的细粒度优势在小知识库上未必明显(与 H1 的"重排在小库上可能引入噪音"呼应)。
