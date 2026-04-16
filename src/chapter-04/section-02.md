# 4.2 向量检索优化与重排序

## 4.2.1 混合检索（Hybrid Search）

单一的向量检索在处理专有名词或精确匹配时往往表现不佳。混合检索结合了关键词检索（BM25）和向量检索的优势：

*   **关键词检索**：擅长处理型号、编号等精确匹配。
*   **向量检索**：擅长理解语义相似性和同义词扩展。

通过 RRF（倒数排名融合）算法，可以将两路召回的结果进行科学融合。

## 4.2.2 重排序（Re-ranking）

初筛出的 Top-K 文档可能包含噪声。使用 Cross-Encoder 模型对候选集进行精细打分，可以显著提升最终答案的质量：

```python
from dashscope import TextRank

def rerank(query, documents, top_k=3):
    response = TextRank.call(
        model='gte-rerank',
        query=query,
        docs=[doc for doc in documents]
    )
    ranked_indices = [item['index'] for item in response.output['results']]
    return [documents[i] for i in ranked_indices[:top_k]]
```

## 4.2.3 阿里云 DashVector 性能调优

在阿里云 DashVector 中，可以通过以下参数优化检索性能：

*   **索引类型**：选择 HNSW 索引以平衡查询速度和内存占用。
*   **相似度度量**：根据 Embedding 模型特性选择余弦相似度（Cosine）或内积（IP）。
*   **过滤条件**：利用元数据过滤（如部门、文档类型）缩小检索范围，提升精度。

> **最佳实践**：在资源允许的情况下，建议开启“向量检索 + 关键词检索 + 重排序”的三级漏斗模式，这是目前企业级 RAG 系统的黄金标准。
