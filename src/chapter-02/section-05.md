# 2.5 成本优化策略

## 场景引入

某电商企业在双 11 大促期间部署了智能客服系统，使用通义千问大模型处理用户咨询。活动结束后，财务部门发现大模型 API 费用远超预算：

- 预期月度费用：¥50,000
- 实际月度费用：¥180,000
- 超支原因：重复查询未缓存、Prompt 设计冗余、未使用批量调用优惠

技术团队面临的核心问题是：如何在不影响用户体验的前提下，将大模型应用成本控制在合理范围内？

本节将系统地解答这个问题，提供一套完整的成本优化方法论。

---

## 2.5.1 成本构成分析

### 大模型应用的成本组成

```
┌──────────────────────────────────────────────┐
│          大模型应用总成本                      │
├──────────────────────────────────────────────┤
│                                              │
│  1. 模型推理成本 (60-80%)                     │
│     ├── 输入 Tokens                          │
│     └── 输出 Tokens                          │
│                                              │
│  2. 基础设施成本 (10-20%)                     │
│     ├── GPU/CPU 计算资源                      │
│     ├── 存储（OSS、数据库）                    │
│     └── 网络（带宽、CDN）                     │
│                                              │
│  3. 运维成本 (5-15%)                          │
│     ├── 监控与告警                            │
│     ├── 日志存储与分析                        │
│     └── 人力成本                              │
│                                              │
└──────────────────────────────────────────────┘
```

**关键洞察：**

- 模型推理成本占总成本的 60-80%，是优化的重点
- 输入 Tokens 通常远多于输出 Tokens（因为包含 System Prompt、上下文历史等）
- 通过优化 Prompt 设计和缓存策略，可以显著降低输入 Tokens

### 百炼平台计费模式

百炼平台提供多种计费模式：

| 计费模式 | 适用场景 | 价格优势 |
|---------|---------|---------|
| **按量付费** | 低频调用、测试环境 | 灵活，无最低消费 |
| **资源包** | 中高频调用、可预测用量 | 比按量付费低 30-50% |
| **Coding Plan** | 高频编程场景 | 固定月费，不限次数 |
| **企业定制** | 超大用量（亿级 Tokens/月） | 协商定价，专属支持 |

**Qwen3.6-Plus 价格示例（2026 年 4 月）：**

| 项目 | 价格（元/百万 Tokens） |
|-----|----------------------|
| 输入 | 2.00 |
| 输出 | 12.00 |

**Qwen2.5-7B 价格示例：**

| 项目 | 价格（元/百万 Tokens） |
|-----|----------------------|
| 输入 | 0.50 |
| 输出 | 1.00 |

---

## 2.5.2 Prompt 优化技巧

### 技巧一：精简 System Prompt

System Prompt 会在每次请求中重复发送，是 Token 消耗的大户。

**❌ 冗长的 System Prompt：**

```python
system_prompt = """
你是一个专业的客服助手，名叫小智。你的职责是帮助用户解决各种问题。
请遵守以下规则：
1. 始终使用礼貌、专业的语气
2. 回答要简洁明了，不要啰嗦
3. 如果不知道答案，请诚实地告诉用户
4. 不要提供任何违法、有害或不适当的内容
5. 对于技术问题，尽量给出详细的步骤和示例
6. 如果用户的问题模糊不清，请主动询问澄清
7. 尊重用户的隐私，不要索取敏感信息
8. 对于超出你能力范围的问题，建议用户联系人工客服
...（更多规则）
"""
```

**✅ 精简的 System Prompt：**

```python
system_prompt = """你是小智，专业客服助手。要求：礼貌专业、简洁准确、不知则承认、不越界。"""
```

**效果对比：**

| 指标 | 冗长版 | 精简版 | 节省 |
|-----|-------|-------|------|
| System Prompt Tokens | ~300 | ~30 | 90% |
| 单次请求总 Tokens | 500 | 230 | 54% |
| 月度成本（100 万次请求） | ¥1,000 | ¥460 | 54% |

### 技巧二：压缩上下文历史

多轮对话中，历史消息会累积占用大量 Tokens。

**策略一：滑动窗口**

只保留最近 N 轮对话：

```python
def truncate_history(messages: list, max_rounds: int = 5) -> list:
    """保留最近 N 轮对话"""
    # 保留 system message
    system_msg = [m for m in messages if m['role'] == 'system']
    
    # 保留最近 N 轮 user/assistant 对话
    conversation = [m for m in messages if m['role'] != 'system']
    truncated = conversation[-max_rounds * 2:]  # 每轮 2 条消息
    
    return system_msg + truncated

# 使用示例
messages = [
    {'role': 'system', 'content': '你是客服助手'},
    {'role': 'user', 'content': '问题 1'},
    {'role': 'assistant', 'content': '回答 1'},
    {'role': 'user', 'content': '问题 2'},
    {'role': 'assistant', 'content': '回答 2'},
    # ... 更多历史
    {'role': 'user', 'content': '当前问题'},
]

truncated = truncate_history(messages, max_rounds=3)
print(f"原始消息数: {len(messages)}, 截断后: {len(truncated)}")
```

**策略二：摘要压缩**

将早期对话压缩为摘要：

```python
def compress_history(messages: list, max_tokens: int = 2000) -> list:
    """将早期对话压缩为摘要"""
    system_msg = [m for m in messages if m['role'] == 'system'][0]
    conversation = [m for m in messages if m['role'] != 'system']
    
    # 估算当前 Tokens
    current_tokens = estimate_tokens(conversation)
    
    if current_tokens <= max_tokens:
        return messages  # 无需压缩
    
    # 找到需要压缩的部分
    keep_messages = []
    total_tokens = 0
    
    # 从后往前保留，直到达到阈值
    for msg in reversed(conversation):
        msg_tokens = estimate_tokens([msg])
        if total_tokens + msg_tokens <= max_tokens:
            keep_messages.insert(0, msg)
            total_tokens += msg_tokens
        else:
            break
    
    # 对剩余部分生成摘要
    compressed_messages = conversation[:-len(keep_messages)]
    if compressed_messages:
        summary = generate_summary(compressed_messages)
        summary_msg = {
            'role': 'system',
            'content': f"[历史对话摘要]\n{summary}"
        }
        keep_messages.insert(0, summary_msg)
    
    return [system_msg] + keep_messages

def generate_summary(messages: list) -> str:
    """使用小模型生成对话摘要"""
    conversation_text = "\n".join([
        f"{m['role']}: {m['content']}" for m in messages
    ])
    
    prompt = f"请用一句话总结以下对话的主要内容：\n\n{conversation_text}\n\n摘要："
    
    response = dashscope.Generation.call(
        model='qwen2.5-7b',  # 使用便宜的小模型
        prompt=prompt,
        max_tokens=100
    )
    
    return response.output.text.strip()
```

**效果对比：**

| 策略 | 平均 Tokens/请求 | 月度成本（100 万次） | 质量影响 |
|-----|----------------|-------------------|---------|
| 无优化 | 800 | ¥1,600 | - |
| 滑动窗口（5 轮） | 400 | ¥800 | 轻微 |
| 摘要压缩 | 250 | ¥500 | 中等 |

### 技巧三：结构化输出约束

通过指定输出格式，避免模型生成冗余内容：

```python
# ❌ 开放式提问
prompt = "请分析一下这个产品的优缺点"

# ✅ 结构化约束
prompt = """分析以下产品的优缺点，按 JSON 格式输出：
{
  "pros": ["优点 1", "优点 2"],
  "cons": ["缺点 1", "缺点 2"],
  "recommendation": "推荐指数 1-5"
}

产品：智能手表 X1
特点：心率监测、GPS 定位、IP68 防水
"""
```

**效果：**

- 减少无关内容，输出更精炼
- 便于程序解析，减少后处理成本
- Tokens 节省约 20-30%

---

## 2.5.3 缓存策略

### 缓存层级

```
┌──────────────────────────────────────────────┐
│              缓存层级架构                      │
├──────────────────────────────────────────────┤
│                                              │
│  L1: 应用层缓存（Redis）                      │
│  - 完全相同的请求直接返回                      │
│  - TTL: 1-24 小时                            │
│  - 命中率: 30-50%                            │
│                                              │
│  L2: 语义缓存（向量相似度）                    │
│  - 语义相似的请求复用结果                      │
│  - 相似度阈值: 0.95+                         │
│  - 命中率: 10-20%                            │
│                                              │
│  L3: 百炼上下文缓存                           │
│  - 复用 System Prompt 和知识库                │
│  - 官方支持，自动管理                         │
│  - 成本节省: 50%（缓存部分）                  │
│                                              │
└──────────────────────────────────────────────┘
```

### L1: 应用层缓存

```python
import redis
import hashlib
import json

redis_client = redis.Redis(host='localhost', port=6379, db=0)

def get_cache_key(model: str, prompt: str) -> str:
    """生成缓存键"""
    content = f"{model}:{prompt}"
    hash_value = hashlib.md5(content.encode()).hexdigest()
    return f"llm_cache:{hash_value}"

def get_from_cache(model: str, prompt: str) -> str | None:
    """从缓存获取结果"""
    cache_key = get_cache_key(model, prompt)
    cached = redis_client.get(cache_key)
    if cached:
        return json.loads(cached)
    return None

def save_to_cache(model: str, prompt: str, response: str, ttl: int = 3600):
    """保存结果到缓存"""
    cache_key = get_cache_key(model, prompt)
    redis_client.setex(cache_key, ttl, json.dumps(response))

def call_with_cache(model: str, prompt: str, ttl: int = 3600) -> str:
    """带缓存的 API 调用"""
    # 尝试从缓存获取
    cached = get_from_cache(model, prompt)
    if cached:
        print("缓存命中")
        return cached
    
    # 调用 API
    response = dashscope.Generation.call(
        model=model,
        prompt=prompt
    )
    result = response.output.text
    
    # 保存到缓存
    save_to_cache(model, prompt, result, ttl)
    
    return result
```

**适用场景：**

- FAQ 问答（相同问题频繁出现）
- 标准化文档生成（模板化内容）
- 代码片段生成（常见编程任务）

**不适用场景：**

- 实时性要求高的内容（新闻、天气）
- 个性化内容（依赖用户历史）
- 创造性任务（每次期望不同结果）

### L2: 语义缓存

对于语义相似但措辞不同的问题，可以使用向量相似度进行缓存：

```python
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

class SemanticCache:
    """语义缓存"""
    
    def __init__(self, similarity_threshold: float = 0.95):
        self.similarity_threshold = similarity_threshold
        self.cache = []  # [(embedding, response), ...]
    
    def _generate_embedding(self, text: str) -> np.ndarray:
        """生成文本向量"""
        response = dashscope.TextEmbedding.call(
            model='text-embedding-v3',
            input=text
        )
        embedding = response.output['embeddings'][0]['embedding']
        return np.array(embedding)
    
    def search(self, query: str) -> str | None:
        """搜索语义相似的缓存"""
        query_embedding = self._generate_embedding(query)
        
        for cached_embedding, cached_response in self.cache:
            similarity = cosine_similarity(
                query_embedding.reshape(1, -1),
                cached_embedding.reshape(1, -1)
            )[0][0]
            
            if similarity >= self.similarity_threshold:
                print(f"语义缓存命中，相似度: {similarity:.3f}")
                return cached_response
        
        return None
    
    def store(self, query: str, response: str):
        """存储到语义缓存"""
        embedding = self._generate_embedding(query)
        self.cache.append((embedding, response))
        
        # 限制缓存大小
        if len(self.cache) > 10000:
            self.cache.pop(0)  # 移除最旧的

# 使用示例
semantic_cache = SemanticCache(similarity_threshold=0.95)

def call_with_semantic_cache(model: str, prompt: str) -> str:
    # 尝试语义缓存
    cached = semantic_cache.search(prompt)
    if cached:
        return cached
    
    # 调用 API
    response = dashscope.Generation.call(model=model, prompt=prompt)
    result = response.output.text
    
    # 存储到语义缓存
    semantic_cache.store(prompt, result)
    
    return result
```

**效果：**

| 查询 | 缓存中的问题 | 相似度 | 是否命中 |
|-----|------------|-------|---------|
| "如何重置密码？" | "怎么找回密码？" | 0.97 | ✅ |
| "如何重置密码？" | "如何修改邮箱？" | 0.72 | ❌ |
| "Python 列表去重" | "Python 如何去除列表重复元素" | 0.96 | ✅ |

### L3: 百炼上下文缓存

百炼平台原生支持的上下文缓存，适合缓存 System Prompt 和知识库文档：

```python
response = dashscope.Generation.call(
    model='qwen3.6-plus',
    messages=[
        {'role': 'system', 'content': '很长的 System Prompt...'},
        {'role': 'user', 'content': '用户问题'}
    ],
    use_context_cache=True,  # 启用上下文缓存
    cache_ttl=86400  # 缓存有效期 24 小时
)

# 查看缓存命中情况
print(f"缓存命中率: {response.usage.context_cache_hit_rate}")
print(f"缓存节省 Tokens: {response.usage.context_cache_tokens}")
```

**计费优惠：**

- 缓存命中的部分按 50% 计费
- 对于长 System Prompt（1000+ Tokens），节省效果显著

---

## 2.5.4 批量调用优化

### Batch API 的优势

百炼平台提供 Batch API，将多个请求合并为一次调用，享受 50% 的价格折扣：

```python
# 单个调用
response1 = dashscope.Generation.call(model='qwen3.6-plus', prompt='问题 1')
response2 = dashscope.Generation.call(model='qwen3.6-plus', prompt='问题 2')
response3 = dashscope.Generation.call(model='qwen3.6-plus', prompt='问题 3')
# 总成本：3 次调用，全价

# 批量调用
requests = [
    {'prompt': '问题 1'},
    {'prompt': '问题 2'},
    {'prompt': '问题 3'},
]
responses = dashscope.Generation.batch_call(
    model='qwen3.6-plus',
    requests=requests
)
# 总成本：1 次批量调用，50% 折扣
```

**适用场景：**

- 离线批量处理（文档 Embedding、数据标注）
- 异步任务（邮件生成、报告撰写）
- 非实时场景（可以接受分钟级延迟）

**不适用场景：**

- 实时对话（需要秒级响应）
- 交互式应用（用户等待结果）

### 动态批处理

对于实时场景，可以通过队列积累请求，动态组成批次：

```python
import queue
import threading
import time
from concurrent.futures import Future

class BatchProcessor:
    """动态批处理器"""
    
    def __init__(self, model: str, batch_size: int = 10, max_wait_ms: int = 100):
        self.model = model
        self.batch_size = batch_size
        self.max_wait_ms = max_wait_ms
        self.request_queue = queue.Queue()
        self.worker_thread = threading.Thread(target=self._process_batches, daemon=True)
        self.worker_thread.start()
    
    def submit(self, prompt: str) -> Future:
        """提交请求"""
        future = Future()
        self.request_queue.put((prompt, future))
        return future
    
    def _process_batches(self):
        """处理批次"""
        while True:
            batch = []
            futures = []
            
            # 收集第一批请求
            prompt, future = self.request_queue.get()
            batch.append(prompt)
            futures.append(future)
            
            # 等待更多请求或达到批次大小
            start_time = time.time()
            while len(batch) < self.batch_size:
                elapsed_ms = (time.time() - start_time) * 1000
                if elapsed_ms >= self.max_wait_ms:
                    break
                
                try:
                    prompt, future = self.request_queue.get(timeout=0.01)
                    batch.append(prompt)
                    futures.append(future)
                except queue.Empty:
                    continue
            
            # 执行批量调用
            try:
                requests = [{'prompt': p} for p in batch]
                responses = dashscope.Generation.batch_call(
                    model=self.model,
                    requests=requests
                )
                
                # 分发结果
                for i, future in enumerate(futures):
                    future.set_result(responses[i].output.text)
                    
            except Exception as e:
                for future in futures:
                    future.set_exception(e)
```

**使用示例：**

```python
# 初始化批处理器（批次大小 10，最大等待 100ms）
batch_processor = BatchProcessor(model='qwen3.6-plus', batch_size=10, max_wait_ms=100)

# 提交请求（异步）
future1 = batch_processor.submit('问题 1')
future2 = batch_processor.submit('问题 2')
future3 = batch_processor.submit('问题 3')

# 获取结果（阻塞等待）
result1 = future1.result()
result2 = future2.result()
result3 = future3.result()
```

**效果：**

- 平均延迟增加：50-100ms（可接受范围内）
- 成本节省：50%（批量调用折扣）
- 适用于 QPS 较高的场景（>10 次/秒）

---

## 2.5.5 模型路由与降级

### 混合模型策略

不是所有任务都需要使用最强的模型。根据任务难度选择合适的模型，可以大幅降低成本：

```python
def route_model(task_complexity: str) -> str:
    """根据任务复杂度选择模型"""
    if task_complexity == 'simple':
        return 'qwen2.5-7b'  # 简单任务，低成本
    elif task_complexity == 'medium':
        return 'qwen3.5-plus'  # 中等任务，平衡性能与成本
    else:
        return 'qwen3.6-plus'  # 复杂任务，高性能

def classify_task_complexity(user_query: str) -> str:
    """分类任务复杂度"""
    # 简单启发式规则
    if len(user_query) < 50 and '?' in user_query:
        return 'simple'
    elif any(keyword in user_query for keyword in ['代码', '编程', '算法', '架构']):
        return 'complex'
    else:
        return 'medium'

# 使用示例
user_query = "如何重置密码？"
complexity = classify_task_complexity(user_query)
model = route_model(complexity)

response = dashscope.Generation.call(
    model=model,
    prompt=user_query
)
```

**成本对比：**

| 任务类型 | 推荐模型 | 输入价格 | 输出价格 | 月度占比 |
|---------|---------|---------|---------|---------|
| 简单（FAQ） | Qwen2.5-7B | ¥0.5/M | ¥1/M | 50% |
| 中等（一般问答） | Qwen3.5-Plus | ¥2/M | ¥8/M | 30% |
| 复杂（代码、推理） | Qwen3.6-Plus | ¥2/M | ¥12/M | 20% |

**综合成本：**

- 全部使用 Qwen3.6-Plus：¥1,000/月（基准）
- 混合模型策略：¥350/月（节省 65%）

### 降级策略

在高峰期或资源紧张时，自动降级到轻量模型：

```python
class ModelFallback:
    """模型降级"""
    
    def __init__(self):
        self.primary_model = 'qwen3.6-plus'
        self.fallback_models = ['qwen3.5-plus', 'qwen2.5-14b', 'qwen2.5-7b']
    
    def call_with_fallback(self, prompt: str, max_retries: int = 3) -> str:
        """带降级的 API 调用"""
        models_to_try = [self.primary_model] + self.fallback_models[:max_retries]
        
        for model in models_to_try:
            try:
                response = dashscope.Generation.call(
                    model=model,
                    prompt=prompt,
                    timeout=30  # 超时时间
                )
                
                if response.status_code == 200:
                    print(f"使用模型: {model}")
                    return response.output.text
                else:
                    print(f"模型 {model} 返回错误: {response.code}")
                    
            except Exception as e:
                print(f"模型 {model} 调用失败: {e}")
                continue
        
        raise Exception("所有模型调用均失败")

# 使用示例
fallback = ModelFallback()
result = fallback.call_with_fallback("用户问题")
```

**触发降级的条件：**

- API 返回限流错误（HTTP 429）
- 响应延迟超过阈值（如 P99 > 1000ms）
- 错误率超过阈值（如 >5%）

---

## 2.5.6 成本监控与告警

### 实时监控看板

建议使用阿里云云监控（CloudMonitor）建立实时监控看板：

**核心指标：**

| 指标 | 说明 | 告警阈值 |
|-----|------|---------|
| `daily_cost` | 当日累计费用 | > 预算的 80% |
| `tokens_per_minute` | 每分钟 Token 用量 | 突增 200% |
| `error_rate` | API 错误率 | > 5% |
| `avg_latency` | 平均响应延迟 | > 500ms |
| `cache_hit_rate` | 缓存命中率 | < 20%（可能缓存失效） |

### 预算告警

```python
from alibabacloud_bssopenapi20171214.client import Client as BssClient
from alibabacloud_bssopenapi20171214.models import QueryAccountBalanceRequest

bss_client = BssClient(
    access_key_id=os.getenv('ALIBABA_CLOUD_ACCESS_KEY_ID'),
    access_key_secret=os.getenv('ALIBABA_CLOUD_ACCESS_KEY_SECRET')
)

def check_budget_usage(monthly_budget: float) -> dict:
    """检查预算使用情况"""
    # 查询当月已用费用
    balance_response = bss_client.query_account_balance(QueryAccountBalanceRequest())
    current_cost = get_current_month_cost()  # 自定义函数，从账单获取
    
    usage_ratio = current_cost / monthly_budget
    
    return {
        'monthly_budget': monthly_budget,
        'current_cost': current_cost,
        'usage_ratio': usage_ratio,
        'remaining': monthly_budget - current_cost,
        'alert_level': get_alert_level(usage_ratio)
    }

def get_alert_level(usage_ratio: float) -> str:
    """根据使用比例确定告警级别"""
    if usage_ratio >= 1.0:
        return 'CRITICAL'  # 超预算
    elif usage_ratio >= 0.8:
        return 'WARNING'  # 接近预算
    elif usage_ratio >= 0.5:
        return 'INFO'  # 正常
    else:
        return 'OK'  # 良好

# 每日检查
daily_report = check_budget_usage(monthly_budget=50000)
print(f"本月已用: ¥{daily_report['current_cost']:,.2f} / ¥{daily_report['monthly_budget']:,.2f}")
print(f"使用比例: {daily_report['usage_ratio']:.1%}")
print(f"告警级别: {daily_report['alert_level']}")
```

### 异常检测

自动检测异常消耗：

```python
def detect_anomalies(daily_costs: list, window: int = 7) -> list:
    """检测异常费用"""
    if len(daily_costs) < window:
        return []
    
    anomalies = []
    
    for i in range(window, len(daily_costs)):
        # 计算过去 N 天的平均值和标准差
        recent_costs = daily_costs[i-window:i]
        mean = np.mean(recent_costs)
        std = np.std(recent_costs)
        
        # 如果当天费用超过均值 + 3 倍标准差，视为异常
        if std > 0 and daily_costs[i] > mean + 3 * std:
            anomalies.append({
                'date': i,
                'cost': daily_costs[i],
                'mean': mean,
                'std': std,
                'deviation': (daily_costs[i] - mean) / std
            })
    
    return anomalies

# 使用示例
daily_costs = [1000, 1100, 950, 1050, 1000, 1100, 1050, 5000, 1000, 1050]
anomalies = detect_anomalies(daily_costs)

for anomaly in anomalies:
    print(f"日期 {anomaly['date']}: 费用 ¥{anomaly['cost']} (偏离均值 {anomaly['deviation']:.1f} 倍标准差)")
```

---

## 本节小结

本节系统介绍了大模型应用的成本优化策略：

1. **成本构成分析**：模型推理成本占 60-80%，是优化的重点；理解百炼平台的计费模式，选择合适的付费方式

2. **Prompt 优化**：精简 System Prompt、压缩上下文历史、结构化输出约束，可节省 30-60% 的 Tokens

3. **缓存策略**：三层缓存架构（应用层、语义、官方上下文缓存），命中率可达 40-70%，大幅降低成本

4. **批量调用**：Batch API 享受 50% 折扣，动态批处理在实时场景中也能受益

5. **模型路由与降级**：根据任务复杂度选择合适模型，混合策略可节省 50-70% 成本；高峰期自动降级保障可用性

6. **成本监控**：建立实时监控看板和预算告警，及时发现异常消耗

**成本优化黄金法则：**

- **先测量，再优化**：没有监控就没有优化
- **分层优化**：从 Prompt、缓存、模型选择等多个层面入手
- **平衡质量与成本**：不要为了省钱牺牲用户体验
- **持续迭代**：成本优化是一个持续的过程，需要定期回顾和调整

技术决策者应将成本优化纳入架构设计的核心考量，而不是事后补救。通过合理的架构设计和持续的优化迭代，可以在保证服务质量的前提下，将大模型应用成本控制在合理范围内。

---

## 延伸阅读

1. **官方文档**
   - [百炼平台计费说明](https://help.aliyun.com/zh/model-studio/pricing)
   - [成本管理最佳实践](https://help.aliyun.com/zh/cost-management/)

2. **行业报告**
   - 《2026 企业大模型应用成本优化白皮书》- 阿里云研究院
   - 《LLM Cost Optimization Strategies》- Anthropic

3. **实践案例**
   - 某电商平台智能客服成本优化实践（从 ¥180K/月降至 ¥50K/月）
   - 某金融机构 RAG 系统缓存策略设计
   - 某 SaaS 公司混合模型路由方案
