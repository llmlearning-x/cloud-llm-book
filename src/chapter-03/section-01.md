# 3.1 RESTful API 设计规范

## 场景引入

某电商平台计划将大模型能力集成到其商品搜索和客服系统中。技术团队面临的首要挑战是：如何设计一套规范、稳定且易于维护的 API 接口，既能满足前端多样化的调用需求，又能有效应对高并发下的性能压力？

本章将从阿里云百炼平台的 API 设计出发，深入探讨大模型场景下的 RESTful 规范适配。

---

## 3.1.1 大模型 API 的特殊性

传统的 RESTful API 设计遵循"资源导向"原则，但大模型 API 具有显著差异：

| 特性 | 传统 API | 大模型 API | 影响 |
|-----|---------|-----------|------|
| **会话状态** | 无状态 | 有状态（多轮对话） | 需维护上下文历史 |
| **响应确定性** | 确定 | 概率性生成 | 相同输入可能产生不同输出 |
| **延迟特征** | 毫秒级 | 秒级（流式首字快） | 需支持 SSE/WebSocket |
| **计费维度** | 调用次数 | Token 用量 | 需精确统计输入/输出量 |

## 3.1.2 端点（Endpoint）设计

阿里云百炼平台采用以下端点设计规范：

```
# 基础 URL
https://dashscope.aliyuncs.com/api/v1

# 文本生成
POST /services/aigc/text-generation/generation

# 多模态生成
POST /services/aigc/multimodal-generation/generation

# Embeddings 向量化
POST /services/embeddings/text-embedding/text-embedding
```

**设计要点：**
1. **版本化路径**：`/api/v1/` 明确标识 API 版本。
2. **服务分类**：按能力类型分组（如 `/aigc/`, `/embeddings/`）。
3. **动词语义**：使用具体动作（`generation`, `synthesis`）而非泛化的 `generate`。

## 3.1.3 请求体与响应体结构

标准的文本生成请求体应包含模型选择、消息历史和推理参数：

```json
{
  "model": "qwen3.6-plus",
  "input": {
    "messages": [
      {"role": "system", "content": "你是一个专业的编程助手。"},
      {"role": "user", "content": "请用 Python 写一个快速排序算法。"}
    ]
  },
  "parameters": {
    "temperature": 0.7,
    "top_p": 0.9,
    "max_tokens": 1024,
    "stream": false
  }
}
```

响应体中，`usage` 字段对于成本核算至关重要：

```json
{
  "output": {
    "text": "def quicksort(arr):...",
    "finish_reason": "stop"
  },
  "usage": {
    "input_tokens": 45,
    "output_tokens": 89,
    "total_tokens": 134
  }
}
```

## 3.1.4 错误处理规范

统一的错误响应格式有助于客户端快速定位问题：

| 错误码 | HTTP 状态码 | 说明 | 解决方案 |
|-------|-----------|------|---------|
| `InvalidParameter` | 400 | 参数格式错误 | 检查参数类型和取值范围 |
| `QuotaExhausted` | 403 | 配额已用尽 | 购买更多额度或等待重置 |
| `RateLimitExceeded` | 429 | 请求频率超限 | 降低调用频率或申请提升配额 |

> **最佳实践**：在客户端实现自动重试机制时，应针对 `429` 和 `5xx` 错误进行指数退避重试，而对于 `400` 类错误则应立即停止并重报给开发者。
