# 附录 B：常用工具与资源

> 本附录整理了开发大模型应用过程中常用的工具、SDK、命令行工具和参考资料。

## B.1 DashScope SDK

### Python SDK

```bash
# 安装
pip install dashscope
```

```python
from dashscope import DashScope

# 初始化
client = DashScope(api_key='your-api-key')

# 同步调用
response = client.call(
    model='qwen-plus',
    messages=[{'role': 'user', 'content': '你好'}]
)

# 异步调用
async_client = DashScope(async_mode=True)
```

### JavaScript/TypeScript SDK

```bash
# npm
npm install @alibaba/dashscope

# 或 yarn
yarn add @alibaba/dashscope
```

```typescript
import { DashScope } from '@alibaba/dashscope';

const client = new DashScope({ apiKey: 'your-api-key' });
const response = await client.chat.completions.create({
  model: 'qwen-plus',
  messages: [{ role: 'user', content: '你好' }]
});
```

## B.2 阿里云 CLI

```bash
# 安装 (macOS)
brew install aliyuncli

# 安装 (Linux)
curl -sSL https://aliyuncli.cn | sh

# 配置
aliyun configure

# 使用示例
aliyun oss ls oss://your-bucket/
aliyun fc invoke function-name
aliyun rds describe-db-instances
```

## B.3 Docker

### 常用命令

```bash
# 构建镜像
docker build -t my-app:latest .

# 运行容器
docker run -p 8080:8080 my-app:latest

# Docker Compose 启动
docker-compose up -d

# 查看日志
docker logs -f container_name

# 进入容器
docker exec -it container_name /bin/bash
```

### GPU 支持

```bash
# NVIDIA Docker 安装
docker pull nvidia/cuda:12.1-runtime-ubuntu22.04
nvidia-docker run --gpus all your-gpu-image
```

### 多阶段构建示例

```dockerfile
# 构建阶段
FROM python:3.11-slim as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --user -r requirements.txt

# 运行阶段
FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY . .
ENV PATH=/root/.local/bin:$PATH
CMD ["python", "app.py"]
```

## B.4 Kubernetes kubectl

```bash
# 安装
brew install kubectl

# 集群配置
kubectl config get-contexts
kubectl config use-context your-cluster

# 常用操作
kubectl get pods -n namespace
kubectl describe pod pod-name -n namespace
kubectl logs -f pod-name -n namespace
kubectl exec -it pod-name -- /bin/bash

# 扩缩容
kubectl scale deployment app-name --replicas=3

# 应用配置
kubectl apply -f deployment.yaml
kubectl delete -f deployment.yaml
```

## B.5 Serverless Devs

```bash
# 安装
npm install -g @serverless-devs/s

# 配置
s config add

# 部署函数计算
s deploy

# 、本地调用
s local invoke

# 查看日志
s logs -t
```

## B.6 Python 常用库

| 库名 | 用途 | 安装命令 |
|------|------|----------|
| `dashscope` | DashScope API | `pip install dashscope` |
| `fastapi` | Web 框架 | `pip install fastapi uvicorn` |
| `gradio` | UI 界面 | `pip install gradio` |
| `langchain` | LLM 应用框架 | `pip install langchain` |
| `langchain-community` | LangChain 集成 | `pip install langchain-community` |
| `pymilvus` | Milvus 客户端 | `pip install pymilvus` |
| `faiss-cpu` / `faiss-gpu` | 向量检索 | `pip install faiss-cpu` |
| `sentence-transformers` | Embedding 模型 | `pip install sentence-transformers` |
| `pymysql` | MySQL 连接 | `pip install pymysql` |
| `redis` | Redis 连接 | `pip install redis` |
| `oss2` | OSS 操作 | `pip install oss2` |
| `prometheus-client` | 监控指标 | `pip install prometheus-client` |
| `structlog` | 结构化日志 | `pip install structlog` |

## B.7 JavaScript/Node.js 常用包

| 包名 | 用途 | 安装命令 |
|------|------|----------|
| `@alibaba/dashscope` | DashScope SDK | `npm i @alibaba/dashscope` |
| `express` | Web 框架 | `npm i express` |
| `ws` | WebSocket | `npm i ws` |
| `ioredis` | Redis 客户端 | `npm i ioredis` |
| `mysql2` | MySQL 客户端 | `npm i mysql2` |
| `dotenv` | 环境变量 | `npm i dotenv` |
| `zod` | Schema 验证 | `npm i zod` |

## B.8 开发工具推荐

### IDE / 编辑器

| 工具 | 说明 |
|------|------|
| **VS Code** | 免费、轻量、插件丰富 |
| **PyCharm** | Python 专业开发 |
| **IntelliJ IDEA** | Java/Kotlin 开发 |
| **Cursor** | AI 增强的代码编辑器 |
| **Warp** | 现代化终端 |

### API 测试

| 工具 | 说明 |
|------|------|
| **Postman** | 全功能 API 客户端 |
| **Apifox** | API 管理和测试 |
| **curl** | 命令行 HTTP 工具 |

### 数据库工具

| 工具 | 说明 |
|------|------|
| **DBeaver** | 跨平台数据库客户端 |
| **RedisInsight** | Redis 可视化管理 |
| **DMS** | 阿里云数据库管理 |

## B.9 官方文档链接

### 阿里云产品文档

| 产品 | 文档地址 |
|------|----------|
| DashScope | https://help.aliyun.com/zh/dashscope |
| 函数计算 FC | https://help.aliyun.com/zh/fc |
| 容器服务 ACK | https://help.aliyun.com/zh/ack |
| PAI 机器学习 | https://help.aliyun.com/zh/pai |
| 对象存储 OSS | https://help.aliyun.com/zh/oss |
| 日志服务 SLS | https://help.aliyun.com/zh/sls |
| API 网关 | https://help.aliyun.com/zh/api-gateway |

### 开源项目

| 项目 | 地址 |
|------|------|
| LangChain | https://python.langchain.com |
| LlamaIndex | https://www.llamaindex.ai |
| Milvus | https://milvus.io/docs |
| FastAPI | https://fastapi.tiangolo.com |
| Gradio | https://gradio.app/docs |
| Ollama | https://github.com/ollama/ollama |

## B.10 学习资源

| 资源类型 | 推荐链接 |
|----------|----------|
| 阿里云开发者社区 | https://developer.aliyun.com |
| 通义千问体验 | https://tongyi.aliyun.com |
| ModelScope | https://modelscope.cn |
| Hugging Face | https://huggingface.co |
| OpenAI Cookbook | https://github.com/openai/openai-cookbook |
