# CRUD-RAG: A Comprehensive Chinese Benchmark for Retrieval-Augmented Generation of Large Language Models

- **paper_id**: crudrag_lyu2024
- **作者**: Yuanjie Lyu, Zhiyu Li, Simin Niu, Feiyu Xiong, Bo Tang, Wenjin Wang, Hao Wu, Huanyong Liu, Tong Xu, Enhong Chen
- **年份 / venue**: 2024 / arXiv
- **arXiv**: https://arxiv.org/abs/2401.17043

## 核心贡献

- **CRUD-RAG**:大规模中文 RAG 基准,把 RAG 应用场景划分为四类 **Create / Read / Update / Delete(CRUD)**:
  - Create:生成原创、多样内容;
  - Read:知识密集场景的复杂问答;
  - Update:修订既有文本中的错误/不一致;
  - Delete:把长文本浓缩为更精简的形式。
- 突破多数现有基准"只评问答、只看 LLM 组件"的局限:**评估 RAG 全组件**,包括检索器、上下文长度、知识库构建、LLM 各自的影响。
- 为不同场景提供 RAG 技术优化洞察。

## 方法

- 为 CRUD 四类分别构建评估数据集;通过消融分析各组件(检索器、上下文长度、知识库构建、LLM)的贡献。

## 数据集

- 中文 CRUD 四类场景数据。

## 对项目可借鉴点

- **"全组件评估"视角**:项目评估要区分"检索失败 vs 生成失败"(神谕检索消融),与 CRUD-RAG"评估检索器而不只看 LLM"的立场一致,提供方法背书。
- 中文语境:项目知识库是英文 RAG 论文,但评估协议可借鉴其中文基准的经验(如检索器对中文查询的影响)。
- Read 场景(知识密集复杂问答)与本项目问答定位最贴近。

## 缺陷 / 开放问题

- 中文语料、CRUD 的 Write/Update/Delete 场景与"可溯源学术问答"的重合度有限,可借鉴点集中在 Read 场景与组件消融设计。
- 主要评估 LLM 组件,检索指标(本项目核心的 Hit@K/MRR)非其重点。
