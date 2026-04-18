# 第 3 章：阿里云核心产品（下）

> "工欲善其事，必先利其器。" —— 容器服务、数据库、日志监控是生产级 AI 应用不可或缺的基础设施。本章将带你掌握这些运维利器。

## 本章内容

- 容器服务 ACK/ASK：Kubernetes 容器编排
- 数据库服务 RDS/PolarDB：结构化数据存储
- 日志与监控服务 SLS/ARMS：可观测性建设

---

## 3.1 容器服务 ACK/ASK

### 3.1.1 什么是容器

在深入容器服务之前，先理解什么是**容器（Container）**。

容器是一种轻量级的虚拟化技术，它将应用及其依赖打包成一个独立的单元，确保应用在任何环境中都能一致运行。

**容器 vs 虚拟机**：

```
┌─────────────────────────────────────────────────────────────┐
│                        物理服务器                            │
├──────────────┬──────────────┬──────────────┬──────────────┤
│   虚拟机 1   │   虚拟机 2   │   虚拟机 3   │   虚拟机 4   │
│  ┌────────┐ │  ┌────────┐  │  ┌────────┐  │  ┌────────┐  │
│  │ Guest  │ │  │ Guest  │  │  │ Guest  │  │  │ Guest  │  │
│  │   OS   │ │  │   OS   │  │  │   OS   │  │  │   OS   │  │
│  ├────────┤ │  ├────────┤  │  ├────────┤  │  ├────────┤  │
│  │  App   │ │  │  App   │  │  │  App   │  │  │  App   │  │
│  │ Libs   │ │  │ Libs   │  │  │ Libs   │  │  │ Libs   │  │
│  └────────┘ │  └────────┘  │  └────────┘  │  └────────┘  │
│  Hypervisor  │  Hypervisor  │  Hypervisor  │  Hypervisor  │
└──────────────┴──────────────┴──────────────┴──────────────┘

┌─────────────────────────────────────────────────────────────┐
│                        物理服务器                            │
├─────────────────────────────────────────────────────────────┤
│   容器 1    │   容器 2    │   容器 3    │   容器 4         │
│  ┌────────┐ │  ┌────────┐ │  ┌────────┐ │  ┌────────┐   │
│  │  App   │ │  │  App   │ │  │  App   │ │  │  App   │   │
│  │ Libs   │ │  │ Libs   │ │  │ Libs   │ │  │ Libs   │   │
│  └────────┘ │  └────────┘ │  └────────┘ │  └────────┘   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Docker Engine / Containerd               │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                    操作系统                            │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

| 特性 | 虚拟机 | 容器 |
|------|--------|------|
| 启动时间 | 分钟级 | 秒级 |
| 资源占用 | GB 级 | MB 级 |
| 密度（单机能跑多少） | 几个 | 几十个 |
| 隔离性 | 完全隔离 | 共享内核 |
| 性能 | 有虚拟化损耗 | 接近原生 |

### 3.1.2 什么是 Kubernetes

**Kubernetes（K8s）** 是一个开源的容器编排平台，用于自动化容器的部署、扩缩容和管理。

**为什么需要 Kubernetes？**

当你只有几个容器时，手动管理是可行的。但当应用扩展到几十个、几百个容器时，需要解决：

- 某个容器挂了，如何自动重启？
- 流量高峰时，如何自动扩容？
- 如何滚动更新应用而不中断服务？
- 如何跨多台服务器调度容器？

Kubernetes 就是为了解决这些问题而生的。

### 3.1.3 ACK 与 ASK

**ACK（Container Service for Kubernetes）**：
- 阿里云托管的 Kubernetes 服务
- 你管理应用和配置，阿里云管理控制平面
- 适合：有 Kubernetes 使用经验，需要完全控制集群

**ASK（Serverless Kubernetes）**：
- 无服务器 Kubernetes
- 无需管理节点，容器按需创建
- 适合：突发流量、事件驱动型应用

| 维度 | ACK | ASK |
|------|-----|-----|
| 节点管理 | 用户管理（Node Pool） | 完全托管（无需节点） |
| 扩缩容 | 节点+Pod 扩缩容 | Pod 级别扩缩容 |
| 冷启动 | 节点预热 | 更快（按需创建） |
| 成本 | 节点费用 | Pod 运行费用 |
| 适用场景 | 长期稳定工作负载 | 突发、事件驱动 |

### 3.1.4 在 ACK 上部署 AI 应用

**1. 编写 Dockerfile**：

```dockerfile
# 基础镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 暴露端口
EXPOSE 8080

# 健康检查
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s \
    CMD curl -f http://localhost:8080/health || exit 1

# 启动命令
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "4", "app:app"]
```

**requirements.txt**：
```
flask==3.0.0
gunicorn==21.2.0
dashscope==1.14.0
redis==5.0.1
```

**2. 构建并推送镜像**：

```bash
# 登录阿里云容器镜像服务
docker login --username=your-username registry.cn-hangzhou.aliyuncs.com

# 构建镜像
docker build -t registry.cn-hangzhou.aliyuncs.com/your-namespace/ai-chat:v1 .

# 推送镜像
docker push registry.cn-hangzhou.aliyuncs.com/your-namespace/ai-chat:v1
```

**3. 编写 Kubernetes 部署文件**：

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ai-chat-deployment
  labels:
    app: ai-chat
spec:
  replicas: 2
  selector:
    matchLabels:
      app: ai-chat
  template:
    metadata:
      labels:
        app: ai-chat
    spec:
      containers:
      - name: ai-chat
        image: registry.cn-hangzhou.aliyuncs.com/your-namespace/ai-chat:v1
        ports:
        - containerPort: 8080
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        env:
        - name: DASHSCOPE_API_KEY
          valueFrom:
            secretKeyRef:
              name: ai-chat-secrets
              key: api-key
        - name: REDIS_HOST
          value: "redis-service"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 10
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 10

---
# service.yaml
apiVersion: v1
kind: Service
metadata:
  name: ai-chat-service
spec:
  selector:
    app: ai-chat
  ports:
  - port: 80
    targetPort: 8080
  type: ClusterIP

---
# hpa.yaml (Horizontal Pod Autoscaler)
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: ai-chat-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: ai-chat-deployment
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

**4. 部署到 ACK**：

```bash
# 创建命名空间
kubectl create namespace ai-chat

# 创建密钥（存储敏感信息）
kubectl create secret generic ai-chat-secrets \
    --from-literal=api-key=your-dashscope-key \
    --namespace=ai-chat

# 部署应用
kubectl apply -f deployment.yaml -n ai-chat
kubectl apply -f service.yaml -n ai-chat
kubectl apply -f hpa.yaml -n ai-chat

# 查看部署状态
kubectl get pods -n ai-chat
kubectl get svc -n ai-chat
kubectl get hpa -n ai-chat

# 查看日志
kubectl logs -l app=ai-chat -n ai-chat -f
```

---

## 3.2 数据库服务

### 3.2.1 关系型数据库 RDS

**RDS（Relational Database Service）** 是阿里云托管的关系型数据库服务，支持 MySQL、PostgreSQL、SQL Server、MariaDB 等引擎。

**为什么不用 ECS 自建数据库？**

| 维度 | ECS 自建 | RDS |
|------|----------|-----|
| 运维 | 需要 DBA 团队 | 云厂商托管 |
| 备份 | 手动配置 | 自动备份 |
| 高可用 | 手动主从 | 多副本自动切换 |
| 性能优化 | 需要专家 | 参数自动调优 |
| 安全 | 手动配置防火墙 | 内置安全防护 |

### 3.2.2 RDS 基本操作（Python）

```python
import pymysql
from dbutils.pooled_db import PooledDB
import os

class DatabaseManager:
    """数据库连接池管理"""
    
    def __init__(self):
        self.pool = PooledDB(
            creator=pymysql,
            maxconnections=20,
            mincached=5,
            host=os.getenv('RDS_HOST'),
            port=3306,
            user=os.getenv('RDS_USER'),
            password=os.getenv('RDS_PASSWORD'),
            database='ai_chat',
            charset='utf8mb4'
        )
    
    def get_connection(self):
        return self.pool.connection()
    
    def execute_query(self, sql, params=None):
        """执行查询"""
        conn = self.get_connection()
        try:
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                cursor.execute(sql, params or ())
                return cursor.fetchall()
        finally:
            conn.close()
    
    def execute_update(self, sql, params=None):
        """执行更新"""
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                affected = cursor.execute(sql, params or ())
                conn.commit()
                return affected
        finally:
            conn.close()

# 使用示例
db = DatabaseManager()

# 创建表
CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS chat_sessions (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    session_id VARCHAR(64) NOT NULL UNIQUE,
    user_id VARCHAR(64) NOT NULL,
    title VARCHAR(255),
    model VARCHAR(32) DEFAULT 'qwen-turbo',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_user_id (user_id),
    INDEX idx_session_id (session_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
"""

# 创建消息表
CREATE_MESSAGES_SQL = """
CREATE TABLE IF NOT EXISTS chat_messages (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    session_id VARCHAR(64) NOT NULL,
    role ENUM('user', 'assistant', 'system') NOT NULL,
    content TEXT NOT NULL,
    tokens INT DEFAULT 0,
    model VARCHAR(32) DEFAULT 'qwen-turbo',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_session_id (session_id),
    FOREIGN KEY (session_id) REFERENCES chat_sessions(session_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
"""

# 初始化表
db.execute_update(CREATE_TABLE_SQL)
db.execute_update(CREATE_MESSAGES_SQL)

# 插入会话
def create_session(user_id, title="新对话"):
    sql = "INSERT INTO chat_sessions (session_id, user_id, title) VALUES (%s, %s, %s)"
    import uuid
    session_id = str(uuid.uuid4())
    db.execute_update(sql, (session_id, user_id, title))
    return session_id

# 插入消息
def save_message(session_id, role, content, tokens=0, model="qwen-turbo"):
    sql = "INSERT INTO chat_messages (session_id, role, content, tokens, model) VALUES (%s, %s, %s, %s, %s)"
    db.execute_update(sql, (session_id, role, content, tokens, model))

# 查询历史
def get_history(session_id, limit=20):
    sql = """
        SELECT role, content, created_at 
        FROM chat_messages 
        WHERE session_id = %s 
        ORDER BY created_at DESC 
        LIMIT %s
    """
    return db.execute_query(sql, (session_id, limit))
```

### 3.2.3 云数据库 Redis

**Redis** 是高性能的内存数据库，常用于缓存、会话存储、消息队列等场景。

```python
import redis
import json
from typing import Optional, List, Dict

class RedisCache:
    """Redis 缓存管理"""
    
    def __init__(self):
        self.client = redis.Redis(
            host=os.getenv('REDIS_HOST'),
            port=6379,
            password=os.getenv('REDIS_PASSWORD'),
            db=0,
            decode_responses=True
        )
    
    # ===== 对话历史管理 =====
    def save_conversation(self, session_id: str, messages: List[Dict], 
                         ttl: int = 86400) -> bool:
        """保存对话历史（默认24小时过期）"""
        key = f"chat:history:{session_id}"
        self.client.setex(key, ttl, json.dumps(messages, ensure_ascii=False))
        return True
    
    def get_conversation(self, session_id: str) -> Optional[List[Dict]]:
        """获取对话历史"""
        key = f"chat:history:{session_id}"
        data = self.client.get(key)
        if data:
            return json.loads(data)
        return None
    
    def append_message(self, session_id: str, role: str, content: str) -> int:
        """追加单条消息"""
        history = self.get_conversation(session_id) or []
        history.append({"role": role, "content": content})
        self.save_conversation(session_id, history)
        return len(history)
    
    # ===== Token 计数 =====
    def count_tokens(self, session_id: str) -> int:
        """统计会话总 Token 数"""
        history = self.get_conversation(session_id) or []
        # 粗略估算：中文每个字算 1.5 token，英文每个词算 1.3 token
        total = 0
        for msg in history:
            content = msg.get('content', '')
            # 简化估算
            total += len(content) // 2
        return total
    
    # ===== 速率限制 =====
    def check_rate_limit(self, user_id: str, max_requests: int = 60, 
                        window: int = 60) -> tuple[bool, int]:
        """
        检查用户请求频率
        返回: (是否允许, 剩余请求数)
        """
        key = f"ratelimit:{user_id}"
        
        # 使用滑动窗口
        current = self.client.get(key)
        if current is None:
            pipe = self.client.pipeline()
            pipe.setex(key, window, 1)
            pipe.execute()
            return True, max_requests - 1
        
        count = int(current)
        if count >= max_requests:
            ttl = self.client.ttl(key)
            return False, 0
        
        pipe = self.client.pipeline()
        pipe.incr(key)
        pipe.expire(key, window)
        pipe.execute()
        
        return True, max_requests - count - 1

# 使用示例
cache = RedisCache()

# 保存对话
cache.save_conversation("session-123", [
    {"role": "user", "content": "你好"},
    {"role": "assistant", "content": "你好！有什么可以帮助你的吗？"}
])

# 检查限流
allowed, remaining = cache.check_rate_limit("user-456", max_requests=10)
if not allowed:
    print("请求过于频繁，请稍后再试")
else:
    print(f"请求通过，剩余 {remaining} 次")
```

---

## 3.3 日志与监控服务

### 3.3.1 日志服务 SLS

**SLS（Simple Log Service）** 是阿里云的海量日志采集、存储、查询服务，是 AI 应用可观测性的核心组件。

```python
import logging
from aliyun.log import LogClient, PutLogsRequest, LogGroup, LogItem
import json
import os

class AliYunLogHandler(logging.Handler):
    """自定义日志处理器，将日志发送到 SLS"""
    
    def __init__(self, endpoint, access_key_id, access_key_secret,
                 project, logstore):
        super().__init__()
        self.client = LogClient(endpoint, access_key_id, access_key_secret)
        self.project = project
        self.logstore = logstore
    
    def emit(self, record):
        try:
            # 构造日志内容
            logitem = LogItem()
            logitem.set_time(int(record.created))
            logitem.push_back('level', record.levelname)
            logitem.push_back('message', record.getMessage())
            logitem.push_back('logger', record.name)
            logitem.push_back('module', record.module)
            
            if record.exc_info:
                logitem.push_back('exception', self.formatException(record.exc_info))
            
            # 添加请求上下文（如果有）
            if hasattr(record, 'request_id'):
                logitem.push_back('request_id', str(record.request_id))
            if hasattr(record, 'user_id'):
                logitem.push_back('user_id', str(record.user_id))
            
            # 发送日志
            loggroup = LogGroup()
            loggroup.logs.append(logitem)
            
            request = PutLogsRequest(self.project, self.logstore, '', '', loggroup)
            self.client.put_logs(request)
            
        except Exception:
            self.handleError(record)

# 配置日志
def setup_logging():
    # 获取 SLS 配置
    endpoint = os.getenv('SLS_ENDPOINT', 'cn-hangzhou.log.aliyuncs.com')
    project = os.getenv('SLS_PROJECT', 'ai-chat-log')
    logstore = os.getenv('SLS_LOGSTORE', 'app-logs')
    
    # 创建 SLS handler
    sls_handler = AliYunLogHandler(
        endpoint=endpoint,
        access_key_id=os.getenv('ACCESS_KEY_ID'),
        access_key_secret=os.getenv('ACCESS_KEY_SECRET'),
        project=project,
        logstore=logstore
    )
    
    # 配置根日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            sls_handler
        ]
    )
    
    return logging.getLogger(__name__)

logger = setup_logging()

# 应用中使用
def chat_handler(request):
    logger.info("收到对话请求", extra={
        'request_id': request.id,
        'user_id': request.user_id,
        'model': request.model
    })
    
    try:
        result = process_chat(request)
        logger.info("对话请求成功", extra={
            'request_id': request.id,
            'tokens': result.tokens
        })
        return result
    except Exception as e:
        logger.error("对话请求失败", extra={
            'request_id': request.id,
            'error': str(e)
        }, exc_info=True)
        raise
```

### 3.3.2 应用实时监控 ARMS

**ARMS（Application Real-Time Monitoring Service）** 提供应用性能监控（APM）能力，帮助快速定位性能问题。

```python
from arms import ArmsClient
import json
import os

class AIMonitor:
    """AI 应用监控"""
    
    def __init__(self):
        self.client = ArmsClient(
            app_name='ai-chat-app',
            endpoint='cn-hangzhou.console.arms.alibaba.com',
            license_key=os.getenv('ARMS_LICENSE_KEY')
        )
    
    def track_request(self, request_id: str, duration: float, 
                     status: int, model: str):
        """追踪 API 请求"""
        self.client.track_request(
            name='chat_completion',
            duration=duration,
            status=status,
            tags={
                'model': model,
                'region': os.getenv('REGION', 'cn-hangzhou')
            }
        )
    
    def track_llm_call(self, request_id: str, model: str,
                      prompt_tokens: int, completion_tokens: int,
                      latency: float):
        """追踪 LLM 调用"""
        self.client.metrics().counter(
            name='llm_tokens_total',
            value=prompt_tokens + completion_tokens,
            tags={
                'model': model,
                'type': 'prompt' if prompt_tokens > completion_tokens else 'completion'
            }
        )
        
        self.client.metrics().histogram(
            name='llm_latency_seconds',
            value=latency,
            tags={'model': model}
        )
    
    def track_error(self, error_type: str, error_message: str,
                   request_id: str = None):
        """追踪错误"""
        self.client.errors().add(
            error_type=error_type,
            message=error_message,
            request_id=request_id
        )

# 中间件集成
class MonitorMiddleware:
    """Flask 监控中间件"""
    
    def __init__(self, app, monitor: AIMonitor):
        self.app = app
        self.monitor = monitor
    
    def __call__(self, environ, start_response):
        import time
        from werkzeug.wrappers import Request
        
        request = Request(environ)
        request_id = request.headers.get('X-Request-ID', 'unknown')
        
        start_time = time.time()
        
        # 包装响应
        def custom_start_response(status, headers, exc_info=None):
            duration = time.time() - start_time
            self.monitor.track_request(
                request_id=request_id,
                duration=duration * 1000,  # 转换为毫秒
                status=200 if status.startswith('200') else 500,
                model=request.args.get('model', 'qwen-turbo')
            )
            return start_response(status, headers, exc_info)
        
        return self.app(environ, custom_start_response)

# 使用示例
monitor = AIMonitor()
monitor.track_llm_call(
    request_id="req-123",
    model="qwen-plus",
    prompt_tokens=150,
    completion_tokens=200,
    latency=1.5
)
```

---

## 3.4 本章小结

本章介绍了三组重要的阿里云产品：

| 产品 | 核心价值 | 在 AI 应用中的角色 |
|------|----------|-------------------|
| **ACK/ASK** | 容器编排 | 运行 AI 微服务的 Kubernetes 平台 |
| **RDS/Redis** | 数据存储 | 持久化存储和缓存层 |
| **SLS/ARMS** | 可观测性 | 日志、监控、链路追踪 |

**典型 AI 应用架构**：

```
┌─────────────────────────────────────────────────────────────┐
│                        用户请求                              │
├─────────────────────────────────────────────────────────────┤
│                         API 网关                             │
│                      (鉴权、限流)                            │
├─────────────────────────────────────────────────────────────┤
│                         负载均衡                             │
├─────────────────┬─────────────────┬───────────────────────┤
│                 │                 │                       │
│    ACK 集群     │    函数计算      │      数据库集群         │
│  ┌───────────┐  │                 │  ┌─────────┐ ┌──────┐ │
│  │ AI Chat   │  │   定时任务      │  │   RDS   │ │Redis │ │
│  │ Service   │  │   批处理任务    │  │  (主库) │ │(缓存) │ │
│  └───────────┘  │                 │  └─────────┘ └──────┘ │
│  ┌───────────┐  │                 │                       │
│  │ AI Model  │  │                 │      日志/监控         │
│  │  Service  │  │                 │  ┌─────────────────┐ │
│  └───────────┘  │                 │  │  SLS     ARMS   │ │
│                 │                 │  │ (日志)   (监控)  │ │
│                 │                 │  └─────────────────┘ │
└─────────────────┴─────────────────┴───────────────────────┘
                              │
                    ┌─────────┴─────────┐
                    │      OSS         │
                    │  (模型文件/数据)   │
                    └─────────────────┘
```

---

## 思考与练习

1. **架构设计**：设计一个支持日活 10 万用户的 AI 对话应用，考虑容器部署、数据库选型、缓存策略
2. **成本估算**：计算以下架构的月成本：
   - ACK：3 个 4 核 8G 节点
   - RDS MySQL：2 核 4G 高可用版
   - Redis：1GB 集群版
   - SLS：每天 100GB 日志
3. **监控告警**：为 AI 对话 API 设计监控指标，包括：请求量、响应时间、错误率、Token 消耗，设置合理的告警阈值

---

## 本书第一部分小结

经过三章的学习，你已经掌握了：

1. **云计算基础**：理解 IaaS/PaaS/SaaS 的区别
2. **核心产品**：
   - OSS：存储训练数据、模型文件
   - 函数计算 FC：Serverless 执行 AI 推理
   - API 网关：统一入口、安全防护
   - ACK/ASK：容器化部署
   - RDS/Redis：数据存储
   - SLS/ARMS：可观测性

这些知识将为你后续学习大模型应用开发打下坚实的云端基础设施基础。

---

**下一步**：进入第二部分，学习大模型的技术原理和阿里云大模型产品。
