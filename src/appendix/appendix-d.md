# 附录 D：错误码速查与常见问题

> 本附录整理了使用阿里云大模型服务时的常见错误码、错误信息和解决方案，以及常见 FAQ。

## D.1 DashScope 错误码

### 认证与权限错误

| 错误码 | 错误信息 | 原因 | 解决方案 |
|--------|----------|------|----------|
| `InvalidApiKey` | API key is invalid | API Key 格式错误或已过期 | 检查 API Key 是否正确，必要时重新生成 |
| `MissingApiKey` | API key is required | 未提供 API Key | 在请求头中添加 `Authorization: Bearer <key>` |
| `QuotaExceeded` | Rate limit exceeded | 请求频率超限 | 降低请求频率，使用指数退避重试 |
| `AccessDenied` | Access denied | 账号欠费或权限不足 | 检查账号余额，确认产品权限开通 |

### 请求参数错误

| 错误码 | 错误信息 | 原因 | 解决方案 |
|--------|----------|------|----------|
| `InvalidParameter` | Invalid parameter: xxx | 参数格式或值错误 | 检查参数类型和范围，参考 API 文档 |
| `MissingParameter` | Required parameter missing | 缺少必要参数 | 添加缺失的参数 |
| `ParameterOutOfRange` | Parameter xxx out of range | 参数值超出范围 | 调整参数值到有效范围内 |
| `UnsupportedParameter` | Parameter not supported | 不支持的参数 | 移除不支持的参数 |

### 模型与配额错误

| 错误码 | 错误信息 | 原因 | 解决方案 |
|--------|----------|------|----------|
| `ModelNotFound` | Model not found: xxx | 模型名称错误 | 使用正确的模型名称，如 `qwen-plus` |
| `ModelNotAvailable` | Model temporarily unavailable | 模型暂时不可用 | 稍后重试，或切换到其他模型 |
| `TokenLimitExceeded` | Token limit exceeded | 输入超过上下文限制 | 减少输入文本，或使用支持更长上下文的模型 |
| `OutputLengthExceeded` | Output length limit exceeded | 输出超过长度限制 | 减少请求的 max_tokens 参数 |

### 服务端错误

| 错误码 | 错误信息 | 原因 | 解决方案 |
|--------|----------|------|----------|
| `InternalError` | Internal server error | 服务端内部错误 | 重试请求，如持续出现请联系支持 |
| `ServiceUnavailable` | Service temporarily unavailable | 服务暂时不可用 | 稍后重试 |
| `Timeout` | Request timeout | 请求超时 | 增加超时时间，或检查网络连接 |
| `TooManyRequests` | Too many requests | 请求过于频繁 | 使用请求限流或增加请求间隔 |

## D.2 函数计算 FC 错误码

| 错误码 | 含义 | 常见原因 | 解决方案 |
|--------|------|----------|----------|
| `FunctionNotFound` | 函数不存在 | 函数名或服务名错误 | 检查函数名和服务名 |
| `ResourceExhausted` | 资源耗尽 | 内存或执行时间超限 | 增加内存配置或超时时间 |
| `FunctionInactive` | 函数未激活 | 函数被禁用或正在更新 | 检查函数状态，重新部署 |
| `InvocationRateLimit` | 调用频率超限 | 并发调用过多 | 使用预置或降低并发 |
| `InvalidArgument` | 参数错误 | 请求参数格式错误 | 检查事件内容和格式 |

## D.3 OSS 错误码

| 错误码 | 含义 | 常见原因 | 解决方案 |
|--------|------|----------|----------|
| `AccessDenied` | 访问被拒绝 | Bucket 或文件权限不足 | 检查 RAM 权限策略 |
| `NoSuchBucket` | Bucket 不存在 | Bucket 名称错误 | 检查 Bucket 名称 |
| `NoSuchKey` | 文件不存在 | 文件路径错误 | 检查文件路径 |
| `RequestTimeTooSkewed` | 请求时间偏差过大 | 客户端时间不准 | 同步系统时间 |
| `SignatureDoesNotMatch` | 签名不匹配 | AccessKey 或签名算法错误 | 重新生成签名 |

## D.4 常见问题 FAQ

### Q1: DashScope API 调用返回 401 错误

**问题描述**：
```
Error: 401 Client Error: Unauthorized
```

**可能原因**：
1. API Key 错误或已失效
2. API Key 未正确设置在请求头中
3. 账号欠费导致服务被暂停

**解决方案**：
```python
# 正确设置 API Key
import os
os.environ['DASHSCOPE_API_KEY'] = 'sk-xxxxxxxxxxxxxxxx'

# 或在初始化时传入
from dashscope import DashScope
client = DashScope(api_key='sk-xxxxxxxxxxxxxxxx')
```

---

### Q2: 模型响应很慢或超时

**问题描述**：API 调用等待时间过长，偶尔超时。

**可能原因**：
1. 网络延迟
2. 模型负载高
3. 输入文本过长

**解决方案**：
```python
# 设置超时时间
response = client.call(
    model='qwen-plus',
    messages=[...],
    options={'request_timeout': 60}  # 60秒超时
)

# 使用流式输出改善体验
for chunk in client.call_stream(model='qwen-plus', messages=[...]):
    print(chunk)
```

---

### Q3: 向量检索召回结果不准确

**问题描述**：语义检索返回的结果与查询意图不相关。

**可能原因**：
1. Embedding 模型选择不当
2. 文本分块策略不合理
3. 向量维度不匹配

**解决方案**：
```python
# 使用混合检索
results = vector_db.search(
    query='用户问题',
    top_k=10,
    search_type='hybrid',  # 混合向量和关键词检索
    alpha=0.7  # 向量权重
)

# 使用重排序
reranked = rerank_model.rerank(query, results)
```

---

### Q4: 函数计算冷启动慢

**问题描述**：首次调用函数响应时间很长。

**可能原因**：
1. 函数未预热
2. 代码包过大
3. 依赖安装耗时

**解决方案**：
```yaml
# serverless.yaml 配置
service: my-service
provider:
  name: aliyun
  runtime: python3.11
  memorySize: 512
  timeout: 30
  
function:
  handler: index.handler
  # 使用定时触发器预热
  events:
    - schedule:
        rate: cron(0 0/30 * * * *)
        name: warmer
```

---

### Q5: Docker 容器内存占用过高

**问题描述**：应用容器内存持续增长。

**可能原因**：
1. 内存泄漏
2. 缓存未清理
3. 大模型推理显存占用大

**解决方案**：
```dockerfile
# 添加内存限制
docker run -m 2g --memory-swap 2g my-app:latest

# 定期清理缓存
RUN apt-get update && apt-get install -y \
    && rm -rf /var/lib/apt/lists/*

# 使用多阶段构建减小镜像
```

---

### Q6: PAI 微调训练失败

**问题描述**：LoRA 微调任务运行失败。

**可能原因**：
1. 数据格式错误
2. GPU 显存不足
3. 超参配置不当

**解决方案**：
```python
# 检查数据格式
# 正确格式：JSONL，每行一个样本
{"instruction": "问题", "input": "上下文", "output": "答案"}

# 降低显存占用
training_args = TrainingArguments(
    per_device_train_batch_size=2,  # 减小 batch size
    gradient_accumulation_steps=4,
    max_grad_norm=0.3,
    fp16=True,  # 启用混合精度
)
```

---

### Q7: API 被恶意调用

**问题描述**：API 调用量异常增高，费用激增。

**解决方案**：
1. **启用 API 限流**
```yaml
# API 网关配置
throttling:
  default: 100  # 每秒 100 请求
  special:
    - max: 10
      api: /v1/chat/completions
```

2. **使用 API Key + 签名认证**
```python
import hmac
import hashlib

def sign_request(secret, params):
    sorted_params = sorted(params.items())
    sign_str = '&'.join(f'{k}={v}' for k, v in sorted_params)
    signature = hmac.new(
        secret.encode(),
        sign_str.encode(),
        hashlib.sha256
    ).hexdigest()
    return signature
```

3. **启用 VPC 访问**
```python
# 仅允许内网调用
# 在 VPC 内的 ECS/ACK 上调用 DashScope
```

---

### Q8: RAG 检索不到相关内容

**问题描述**：即使知识库中有相关内容，也检索不到。

**排查步骤**：
1. 检查 Embedding 模型是否与查询语言匹配
2. 检查文档解析是否正确
3. 尝试多种检索策略

```python
# 多种检索策略对比
strategies = ['vector', 'keyword', 'hybrid', 'MMR']

for strategy in strategies:
    results = retriever.search(
        query=user_query,
        strategy=strategy,
        top_k=10
    )
    print(f"{strategy}: {len(results)} results")
```

---

### Q9: 如何估算 DashScope 成本？

**计费方式**：
- 按 Token 数计费（输入 + 输出）
- 不同模型价格不同

```python
# 成本估算示例
def estimate_cost(model, input_text, output_text):
    # 粗略估算：中文 ~1.5 token/字，英文 ~0.75 token/词
    input_tokens = len(input_text) * 1.5
    output_tokens = len(output_text) * 1.5
    
    prices = {
        'qwen-plus': {'input': 0.004, 'output': 0.012},  # 元/千token
        'qwen-turbo': {'input': 0.002, 'output': 0.006},
    }
    
    price = prices.get(model, prices['qwen-plus'])
    cost = (input_tokens / 1000) * price['input'] + \
           (output_tokens / 1000) * price['output']
    
    return cost

print(f"预计成本: {estimate_cost('qwen-plus', '你好', '你好！有什么可以帮你的？')} 元")
```

---

### Q10: 如何实现高可用部署？

**架构建议**：

```
用户请求
    ↓
负载均衡（SLB）
    ↓
┌─────────────────────────────────┐
│         Auto Scaling            │
│  ┌─────────┐  ┌─────────┐       │
│  │ 实例 1  │  │ 实例 2  │  ...  │
│  └─────────┘  └─────────┘       │
└─────────────────────────────────┘
    ↓
向量数据库（Milvus 集群）
    ↓
对象存储（OSS）
```

**关键配置**：
```yaml
# Kubernetes HPA 配置
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: llm-app-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: llm-app
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

## D.5 参考链接

### 官方文档

| 资源 | 链接 |
|------|------|
| DashScope 官方文档 | https://help.aliyun.com/zh/dashscope |
| DashScope API 调试 | https://dashscope.console.aliyun.com/apiKey |
| 函数计算 FC 文档 | https://help.aliyun.com/zh/fc |
| PAI 机器学习文档 | https://help.aliyun.com/zh/pai |
| OSS 对象存储文档 | https://help.aliyun.com/zh/oss |
| Milvus 向量数据库 | https://milvus.io/docs |
| Serverless Devs 文档 | https://www.serverless-devs.com |

### 技术博客

| 资源 | 链接 |
|------|------|
| 阿里云开发者社区 | https://developer.aliyun.com/article |
| 通义千问官方博客 | https://tongyi.aliyun.com/resource |
| LangChain 中文文档 | https://python.langchain.com.cn |
| RAG 技术详解 | https://arxiv.org/abs/2005.11401 |
| LoRA 论文 | https://arxiv.org/abs/2106.09685 |

### 开源项目

| 项目 | 链接 |
|------|------|
| LangChain | https://github.com/langchain-ai/langchain |
| LlamaIndex | https://github.com/run-llama/llama_index |
| QAnything (有问必答) | https://github.com/netease-youdao/QAnything |
| FastChat (部署聊天机器人) | https://github.com/lm-sys/FastChat |
| vLLM (高效推理) | https://github.com/vllm-project/vllm |
| Ollama (本地模型) | https://github.com/ollama/ollama |

### 社区与交流

| 资源 | 链接 |
|------|------|
| 阿里云 AI 交流群 | 钉钉搜索「阿里云百炼」 |
| GitHub Issues | 在各开源项目提 Issue |
| Stack Overflow | 搜索相关技术标签 |
