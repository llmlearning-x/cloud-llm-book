# 4.3 企业级 RAG 系统实现案例

## 4.3.1 系统架构设计

一个健壮的企业级 RAG 系统应包含以下核心组件：

*   **数据接入层**：支持定时同步数据库、文件服务器和钉钉文档。
*   **处理流水线**：异步任务队列（如 Celery）处理耗时的文档解析和向量化。
*   **检索服务**：提供统一的搜索接口，支持多路召回和重排序。
*   **应用网关**：处理用户鉴权、流式输出和日志审计。

## 4.3.2 核心代码实现

基于 Flask 和阿里云百炼的完整实现示例：

```python
@app.route('/api/rag/query', methods=['POST'])
def rag_query():
    question = request.json.get('question')
    
    # 1. 混合检索
    contexts = hybrid_search(question, top_k=10)
    
    # 2. 重排序
    final_contexts = rerank(question, contexts, top_k=5)
    
    # 3. 构建增强 Prompt
    prompt = build_rag_prompt(question, final_contexts)
    
    # 4. 调用 Qwen3.6-Plus 生成答案
    response = Generation.call(
        model='qwen3.6-plus',
        messages=[{'role': 'user', 'content': prompt}],
        stream=True
    )
    
    return Response(generate_stream(response), mimetype='text/event-stream')
```

## 4.3.3 效果评估与持续优化

上线后需重点关注以下指标：

*   **命中率**：用户点赞/点踩的比例。
*   **引用准确率**：生成的答案是否能准确追溯到原始文档片段。
*   **响应延迟**：从提问到首字输出的时间（TTFT）。

> **本章小结**：RAG 技术的落地不仅仅是算法问题，更是工程问题。通过合理的切分、混合检索和重排序策略，可以显著提升大模型在企业私有知识场景下的表现。
