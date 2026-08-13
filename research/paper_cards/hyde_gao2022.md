# Precise Zero-Shot Dense Retrieval without Relevance Labels

- **paper_id**: hyde_gao2022
- **作者**: Luyu Gao, Xueguang Ma, Jimmy Lin, Jamie Callan
- **年份 / venue**: 2022 / Findings of ACL 2023
- **arXiv**: https://arxiv.org/abs/2212.10496

## 核心贡献

- **HyDE(Hypothetical Document Embeddings)**:无需任何相关性标签即可做零样本稠密检索。
- 核心思想是"先改写问题为证据":指令 LLM 按查询生成一篇假设文档(捕捉相关性模式,但不真实、可能含虚假细节),再用无监督对比编码器(Contriever)把它编码成向量,在语料向量空间中找邻域召回真实文档。

## 方法

- 两阶段:① 零样本指令 LLM 生成假设文档 → ② 无监督编码器编码假设文档 → 向量相似度检索。
- 编码器的稠密瓶颈过滤假设文档里的错误细节,"落地"到真实语料。

## 数据集

- 多个任务(web search、QA、事实校验)与语言(sw、ko、ja 等)。

## 对项目可借鉴点

- **查询改写/增强**的经典代表,可与 DPR 直接对比(零样本 vs 有监督微调)。
- 若 bge-m3 在小语料上召回不佳,HyDE 是评估集里"方法理解"题的好素材,也可能作为后续检索增强的备选思路(超出当前最小范围,仅记录)。
- 体现"查询侧增强"这一检索改进维度,丰富 H2 的解读视角。

## 缺陷 / 开放问题

- 依赖 LLM 生成假设文档的质量;生成幻觉会传导到检索。
- 假设文档编码是额外一次 LLM 调用,增加延迟与成本(本项目评估含平均延迟指标,需权衡)。
