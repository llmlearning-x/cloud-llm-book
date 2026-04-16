# 第 7 章 大模型应用性能优化

> **本章导读**
> 
> 性能是大模型应用用户体验的关键指标。本章将深入讲解推理加速、缓存策略、批处理优化、模型压缩等性能优化技术，帮助技术决策者构建低延迟、高吞吐的大模型应用系统。
> 
> **核心议题：**
> - 推理延迟分析与优化
> - 多级缓存策略设计
> - 批处理（Batching）优化
> - 模型量化与蒸馏
> - 流式输出与增量渲染
> - 性能监控与调优

---

## 7.1 推理延迟分析

### 7.1.1 延迟构成

大模型推理延迟主要由以下部分组成：

```
总延迟 = 网络传输 + 排队等待 + Prefill + Decoding

- Prefill 阶段：处理输入 Prompt，并行计算所有 token
- Decoding 阶段：自回归生成输出 token，串行计算
```

**典型延迟分布（Qwen3.6-Plus，1000 输入 +500 输出）：**

| 阶段 | 耗时 | 占比 |
|-----|------|-----|
| 网络传输 | 20ms | 5% |
| 排队等待 | 50ms | 12% |
| Prefill | 100ms | 24% |
| Decoding | 250ms | 59% |
| **总计** | **420ms** | **100%** |

### 7.1.2 首 Token 延迟优化

首 Token 延迟（Time to First Token, TTFT）直接影响用户感知：

```python
# 使用流式输出降低感知延迟
def stream_response(question):
    responses = Generation.call(
        model='qwen3.6-plus',
        messages=[{'role': 'user', 'content': question}],
        stream=True
    )
    
    first_token_time = None
    for response in responses:
        if first_token_time is None:
            first_token_time = time.time()
            print(f"首 Token 延迟：{first_token_time - start_time:.2f}s")
        
        delta = response.output.choices[0].message.content
        print(delta, end='', flush=True)
```

**优化策略：**
- 启用流式输出，边生成边返回
- 优化网络链路，使用就近接入点
- 减少 Prefill 阶段的计算量（缩短 Prompt）

---

## 7.2 多级缓存策略

### 7.2.1 响应缓存

对于重复或相似问题，直接返回缓存结果：

```python
import hashlib
import redis
from datetime import timedelta

class ResponseCache:
    def __init__(self, redis_client):
        self.redis = redis_client
        self.ttl = timedelta(hours=24)
    
    def _get_cache_key(self, question):
        """生成缓存 Key"""
        return f"qa_cache:{hashlib.md5(question.encode()).hexdigest()}"
    
    def get(self, question):
        """获取缓存"""
        key = self._get_cache_key(question)
        cached = self.redis.get(key)
        if cached:
            return json.loads(cached)
        return None
    
    def set(self, question, answer):
        """设置缓存"""
        key = self._get_cache_key(question)
        self.redis.setex(
            key,
            self.ttl,
            json.dumps(answer, ensure_ascii=False)
        )

# 使用示例
cache = ResponseCache(redis.Redis())

def cached_qa(question):
    # 先查缓存
    cached_answer = cache.get(question)
    if cached_answer:
        return cached_answer
    
    # 缓存未命中，调用 API
    answer = call_llm_api(question)
    
    # 写入缓存
    cache.set(question, answer)
    
    return answer
```

### 7.2.2 语义缓存

使用向量相似度匹配相似问题：

```python
class SemanticCache:
    def __init__(self, dashvector_client, threshold=0.9):
        self.client = dashvector_client
        self.collection = client.get('qa_cache')
        self.threshold = threshold  # 相似度阈值
    
    def search(self, question):
        """搜索相似问题的缓存"""
        # 问题向量化
        query_vector = get_embedding(question)
        
        # 检索最相似的缓存
        result = self.collection.query(
            vector=query_vector,
            topk=1,
            include_fields=['question', 'answer']
        )
        
        if result.docs:
            doc = result.docs[0]
            similarity = doc.score
            
            if similarity >= self.threshold:
                return doc.fields['answer']
        
        return None
    
    def store(self, question, answer):
        """存储问答对"""
        vector = get_embedding(question)
        doc = Doc(
            id=f"cache_{int(time.time())}",
            vector=vector,
            fields={
                'question': question,
                'answer': answer
            }
        )
        self.collection.upsert([doc])

# 语义缓存可命中相似问题
# 用户问："如何重置密码？"
# 可命中缓存："密码忘了怎么办？"
```

### 7.2.3 上下文缓存

利用百炼平台的上下文缓存功能：

```python
# 对于固定的系统 Prompt 和知识库文档
response = Generation.call(
    model='qwen3.6-plus',
    messages=[
        {'role': 'system', 'content': LONG_SYSTEM_PROMPT},
        {'role': 'user', 'content': user_question}
    ],
    use_context_cache=True  # 开启上下文缓存
)

# 第二次调用时，系统 Prompt 部分直接从缓存读取
# 可节省约 50% 的成本和延迟
```

---

## 7.3 批处理优化

### 7.3.1 请求合并

将多个小请求合并为批量请求：

```python
import asyncio
from collections import deque

class BatchProcessor:
    def __init__(self, batch_size=10, max_wait_ms=100):
        self.batch_size = batch_size
        self.max_wait_ms = max_wait_ms
        self.queue = deque()
        self.lock = asyncio.Lock()
    
    async def submit(self, request):
        """提交请求"""
        future = asyncio.Future()
        self.queue.append((request, future))
        
        # 如果队列满了，立即处理
        if len(self.queue) >= self.batch_size:
            await self.process_batch()
        
        return await future
    
    async def process_batch(self):
        """处理一批请求"""
        async with self.lock:
            if not self.queue:
                return
            
            # 取出当前批次
            batch = list(self.queue)[:self.batch_size]
            del self.queue[:self.batch_size]
        
        requests = [r for r, _ in batch]
        futures = [f for _, f in batch]
        
        # 批量调用 API
        results = await self.batch_api_call(requests)
        
        # 设置结果
        for future, result in zip(futures, results):
            future.set_result(result)
    
    async def batch_api_call(self, requests):
        """实际调用批量 API"""
        # 使用 DashScope 的 batch 接口
        response = Generation.batch_call(
            model='qwen3.6-plus',
            requests=requests
        )
        return response

# 使用示例
processor = BatchProcessor(batch_size=10)

async def handle_user_question(question):
    result = await processor.submit({'messages': [{'role': 'user', 'content': question}]})
    return result
```

### 7.3.2 动态批处理

根据负载动态调整批大小：

```python
class DynamicBatcher:
    def __init__(self):
        self.current_batch_size = 10
        self.latency_history = []
    
    def adjust_batch_size(self, avg_latency):
        """根据延迟动态调整批大小"""
        target_latency = 200  # 目标延迟 200ms
        
        if avg_latency > target_latency * 1.5:
            # 延迟过高，减小批次
            self.current_batch_size = max(1, self.current_batch_size - 2)
        elif avg_latency < target_latency * 0.7:
            # 延迟较低，增大批次
            self.current_batch_size = min(50, self.current_batch_size + 2)
        
        return self.current_batch_size
```

---

## 7.4 模型压缩

### 7.4.1 量化（Quantization）

将模型权重从 FP32 转换为 INT8/INT4：

```
原始模型 (FP32): 每个参数 4 字节
INT8 量化后：每个参数 1 字节，体积减少 75%
INT4 量化后：每个参数 0.5 字节，体积减少 87.5%
```

**量化效果对比：**

| 量化精度 | 模型体积 | 推理速度 | 精度损失 |
|---------|---------|---------|---------|
| FP32 | 14GB | 1x | 0% |
| INT8 | 3.5GB | 2-3x | <1% |
| INT4 | 1.75GB | 3-4x | 1-3% |

### 7.4.2 知识蒸馏（Knowledge Distillation）

用大模型（教师）训练小模型（学生）：

```python
# 伪代码示例
def distill_loss(student_output, teacher_output, temperature=4.0):
    """
    知识蒸馏损失函数
    """
    # 软化概率分布
    student_soft = softmax(student_output / temperature)
    teacher_soft = softmax(teacher_output / temperature)
    
    # KL 散度
    kd_loss = kl_divergence(student_soft, teacher_soft)
    
    # 结合真实标签的交叉熵
    ce_loss = cross_entropy(student_output, true_labels)
    
    return kd_loss + ce_loss

# 训练后，小模型可达到大模型 90%+ 的效果
# 但推理速度快 3-5 倍
```

### 7.4.3 阿里云百炼模型优化

```python
# 百炼平台提供自动优化选项
response = Generation.call(
    model='qwen3.6-plus',
    messages=messages,
    optimization_config={
        'quantization': 'int8',  # INT8 量化
        'use_cache': True,       # 启用 KV Cache
        'max_batch_size': 32     # 最大批大小
    }
)
```

---

## 7.5 流式输出与增量渲染

### 7.5.1 服务端流式

```python
@app.route('/api/chat/stream')
def chat_stream():
    def generate():
        responses = Generation.call(
            model='qwen3.6-plus',
            messages=[{'role': 'user', 'content': request.args.get('q')}],
            stream=True,
            incremental_output=True
        )
        
        for response in responses:
            delta = response.output.choices[0].message.content
            yield f"data: {json.dumps({'delta': delta})}\n\n"
    
    return Response(generate(), mimetype='text/event-stream')
```

### 7.5.2 前端增量渲染

```javascript
// 前端 SSE 接收
const eventSource = new EventSource('/api/chat/stream?q=' + encodeURIComponent(question));

let fullAnswer = '';
eventSource.onmessage = (event) => {
    const data = JSON.parse(event.data);
    fullAnswer += data.delta;
    
    // 实时更新 UI
    document.getElementById('answer').innerHTML = marked.parse(fullAnswer);
    
    // 自动滚动到底部
    window.scrollTo(0, document.body.scrollHeight);
};
```

---

## 7.6 性能监控

### 7.6.1 关键指标

```python
metrics = {
    'latency_p50': 150,    # 中位数延迟
    'latency_p95': 300,    # P95 延迟
    'latency_p99': 500,    # P99 延迟
    'throughput_qps': 50,  # 每秒查询数
    'token_per_second': 1000,  # 每秒生成 token 数
    'cache_hit_rate': 0.35,    # 缓存命中率
    'error_rate': 0.001        # 错误率
}
```

### 7.6.2 Prometheus 监控

```python
from prometheus_client import Counter, Histogram, start_http_server

# 定义指标
REQUEST_COUNT = Counter('llm_requests_total', 'Total LLM requests')
REQUEST_LATENCY = Histogram('llm_request_latency_seconds', 'LLM request latency')
TOKEN_COUNT = Counter('llm_tokens_total', 'Total tokens', ['type'])

# 埋点
@REQUEST_LATENCY.time()
def call_llm_with_metrics(question):
    REQUEST_COUNT.inc()
    response = call_llm(question)
    TOKEN_COUNT.labels(type='input').inc(response.usage.input_tokens)
    TOKEN_COUNT.labels(type='output').inc(response.usage.output_tokens)
    return response

# 启动监控服务器
start_http_server(8000)
```

### 7.6.3 性能看板

使用 Grafana 搭建可视化看板：

```yaml
# dashboard.yaml
dashboard:
  title: "大模型应用性能监控"
  panels:
    - title: "请求延迟分布"
      type: "heatmap"
      query: "histogram_quantile(0.95, rate(llm_request_latency_seconds_bucket[5m]))"
    
    - title: "QPS 趋势"
      type: "graph"
      query: "rate(llm_requests_total[1m])"
    
    - title: "缓存命中率"
      type: "gauge"
      query: "rate(cache_hits_total[5m]) / rate(cache_requests_total[5m])"
    
    - title: "Token 生成速率"
      type: "graph"
      query: "rate(llm_tokens_total{type='output'}[1m])"
```

---

## 本章小结

本章系统讲解了大模型应用的性能优化：

1. **延迟分析**：理解 Prefill 和 Decoding 阶段的延迟构成，针对性优化
2. **多级缓存**：响应缓存、语义缓存、上下文缓存三层体系，可命中 30-50% 的请求
3. **批处理优化**：请求合并、动态批大小，提升吞吐量
4. **模型压缩**：量化、蒸馏等技术，在精度损失<3% 的情况下提速 3-4 倍
5. **流式输出**：服务端流式 + 前端增量渲染，大幅降低用户感知延迟
6. **性能监控**：建立完善的指标体系和可视化看板

性能优化是一个持续的过程。技术决策者应建立性能基线，定期评估优化效果，在成本、质量、速度之间找到最佳平衡点。

---

## 延伸阅读

1. [阿里云百炼性能优化指南](https://help.aliyun.com/zh/model-studio/performance-optimization)
2. 《Efficient NLP》- Hugging Face
3. vLLM 项目：https://github.com/vllm-project/vllm
4. ONNX Runtime 文档：https://onnxruntime.ai/

---

**下一章预告**：第 8 章将探讨大模型应用部署与运维，包括容器化部署、CI/CD 流程、灰度发布、监控告警、故障排查等生产环境必备技能。