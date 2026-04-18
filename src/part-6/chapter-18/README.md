# 第 18 章：云原生部署与运维

> 本章介绍将 AI 应用部署到云端的各种方式，包括 Docker 容器化、阿里云函数计算、容器服务 ACK，以及监控、日志与安全实践。

## 本章内容提要

| 主题 | 核心技能 |
|------|----------|
| Docker 部署 | 镜像构建、多阶段构建、GPU 部署 |
| 函数计算 | FC 部署 AI 应用、触发器配置 |
| Kubernetes | ACK 部署、Helm Chart、HPA |
| 运维实践 | 监控日志、安全加固、成本优化 |

---

## 18.1 Docker 容器化

### 18.1.1 AI 应用 Dockerfile

```dockerfile
# examples/Dockerfile.ai-app
# 多阶段构建
FROM python:3.11-slim AS builder

# 安装构建依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 创建虚拟环境
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# 安装 Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ============ 生产镜像 ============
FROM nvidia/cuda:12.1.0-cudnn8-runtime-ubuntu22.04 AS production

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# 安装运行时依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# 从 builder 复制虚拟环境
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# 复制应用代码
WORKDIR /app
COPY src/ ./src/
COPY config/ ./config/
COPY models/ ./models/

# 非 root 用户运行
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 启动命令
CMD ["uvicorn", "src.api:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 18.1.2 GPU 支持

```dockerfile
# examples/Dockerfile.gpu
FROM nvidia/cuda:12.1.0-cudnn8-runtime-ubuntu22.04

# 安装 NVIDIA Container Toolkit
RUN curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg && \
    curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
    sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
    tee /etc/apt/sources.list.d/nvidia-container-toolkit.list && \
    apt-get update && \
    apt-get install -y nvidia-container-toolkit && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# 配置 Docker runtime
RUN nvidia-ctk runtime configure --runtime=docker
```

```yaml
# docker-compose.gpu.yml
version: '3.8'

services:
  ai-service:
    build:
      context: .
      dockerfile: Dockerfile.gpu
    runtime: nvidia
    environment:
      NVIDIA_VISIBLE_DEVICES: all
      NVIDIA_REQUIRE_CUDA: "cuda>=12.0"
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    ports:
      - "8000:8000"
```

### 18.1.3 模型文件处理

```dockerfile
# 下载预训练模型
FROM python:3.11-slim

# 安装模型下载工具
RUN pip install huggingface_hub

# 下载模型（运行时）
CMD python -c "from huggingface_hub import snapshot_download; \
    snapshot_download(repo_id='Qwen/Qwen2-7B', \
    cache_dir='/models', \
    local_dir='/models/qwen')"
```

```bash
# 构建镜像
docker build -t my-ai-app:v1.0 .

# 运行
docker run --gpus all -p 8000:8000 \
    -v ./models:/models \
    -e MODEL_PATH=/models/qwen \
    my-ai-app:v1.0

# Docker Compose 启动
docker compose -f docker-compose.gpu.yml up -d
```

---

## 18.2 阿里云函数计算部署

### 18.2.1 FC 部署 AI 应用

函数计算（FC）是阿里云的 Serverless 计算服务，适合 AI 推理场景：

```yaml
# fc.yaml - FC 配置文件
edition: 1.0.0
provider:
  name: aliyun
  runtime: python3.11
  timeout: 300  # 5分钟超时

vars:
  region: cn-hangzhou
  functionName: campus-assistant

functions:
  inference:
    handler: inference.handler
    runtime: python3.11
    memorySize: 32768  # 32GB
    timeout: 300
    instanceType: gpu  # GPU 实例
    
    environmentVariables:
      MODEL_NAME: Qwen/Qwen2-7B
      MAX_LENGTH: 2048
      TEMPERATURE: "0.7"
    
    # 层依赖（预装依赖）
    layers:
      - acs:python3.11:v1  # Python 运行时
      - acs:custom-container:1.0  # 容器支持
    
    # NAS 存储（挂载模型文件）
    nasConfig:
      userId: 10003
      groupId: 10003
      mountPoints:
        - serverAddr: ${nas-mount-point}
          mountDir: /mnt/nas
```

```python
# src/fc/inference.py
# 函数计算入口文件

import json
import os
from http.server import BaseHTTPRequestHandler

# 全局变量（冷启动时初始化）
model = None
tokenizer = None

def load_model():
    """加载模型（冷启动时执行一次）"""
    global model, tokenizer
    
    from transformers import AutoModelForCausalLM, AutoTokenizer
    
    model_name = os.environ.get("MODEL_NAME", "Qwen/Qwen2-7B")
    model_path = os.environ.get("MODEL_PATH", "/mnt/nas/models")
    
    print(f"加载模型: {model_name}")
    
    tokenizer = AutoTokenizer.from_pretrained(
        model_path if os.path.exists(model_path) else model_name,
        trust_remote_code=True
    )
    
    model = AutoModelForCausalLM.from_pretrained(
        model_path if os.path.exists(model_path) else model_name,
        device_map="auto",
        trust_remote_code=True
    )
    
    print("模型加载完成")

def handler(event, context):
    """函数计算入口"""
    global model, tokenizer
    
    # 冷启动加载模型
    if model is None:
        load_model()
    
    # 解析请求
    try:
        evt = json.loads(event) if isinstance(event, str) else event
    except:
        evt = {"body": event}
    
    # 处理请求
    if "request" in evt and "uri" in evt["request"]:
        return handle_http(event, context)
    else:
        return handle_invoke(event, context)

def handle_http(event, context):
    """处理 HTTP 请求"""
    global model, tokenizer
    
    # 解析 HTTP 请求
    method = event["request"]["method"]
    path = event["request"]["uri"]
    
    if method == "GET" and path == "/health":
        return {
            "statusCode": 200,
            "body": json.dumps({"status": "ok"})
        }
    
    if method == "POST" and path == "/v1/chat":
        body = json.loads(event["body"])
        return chat_completion(body)
    
    return {"statusCode": 404, "body": "Not Found"}

def handle_invoke(event, context):
    """处理函数调用"""
    global model, tokenizer
    
    messages = event.get("messages", [])
    return chat_completion({"messages": messages})

def chat_completion(request):
    """聊天补全"""
    global model, tokenizer
    
    messages = request.get("messages", [])
    temperature = float(request.get("temperature", 0.7))
    max_tokens = int(request.get("max_tokens", 2048))
    
    # 生成回复
    text = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True
    )
    
    inputs = tokenizer([text], return_tensors="pt").to(model.device)
    
    outputs = model.generate(
        **inputs,
        max_new_tokens=max_tokens,
        temperature=temperature,
        do_sample=temperature > 0
    )
    
    response = tokenizer.decode(
        outputs[0][inputs.input_ids.shape[1]:],
        skip_special_tokens=True
    )
    
    return {
        "statusCode": 200,
        "body": json.dumps({
            "choices": [{
                "message": {"role": "assistant", "content": response}
            }]
        })
    }
```

### 18.2.2 Serverless Devs 部署

```yaml
# s.yaml - Serverless Devs 配置
edition: 1.0.0
name: campus-assistant
access: default

services:
  inference-service:
    component: fc
    props:
      region: cn-hangzhou
      service:
        name: ai-services
        description: AI 推理服务
        vpcConfig:
          vpcId: ${vars.vpcId}
          vswitchIds: [${vars.vswitchId}]
          securityGroupId: ${vars.securityGroupId}
        nasConfig:
          userId: 10003
          groupId: 10003
          mountPoints:
            - serverAddr: ${vars.nasAddr}
              mountDir: /mnt/nas
      function:
        name: ${vars.functionName}
        runtime: custom-container
        timeout: 300
        memorySize: 32768
        instanceConcurrency: 10
        customContainerConfig:
          image: registry.cn-hangzhou.aliyuncs.com/my-account/ai-service:v1
          port: 8000
        environmentVariables:
          MODEL_PATH: /mnt/nas/models/qwen
          MAX_LENGTH: "2048"
      triggers:
        - name: http-trigger
          type: http
          config:
            authType: anonymous
            methods: [GET, POST]
      permissions:
        - service: RAM
          plugin: RAMRole
```

```bash
# 安装 serverless devs
npm install -g @serverless-devs/s

# 配置凭证
s config add --alias default --AccessKeyID xxx --AccessKeySecret xxx

# 部署
s deploy

# 触发测试
s invoke -e '{"messages": [{"role": "user", "content": "你好"}]}'

# 查看日志
s logs -t
```

---

## 18.3 容器服务 ACK 部署

### 18.3.1 Kubernetes 部署配置

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: campus-assistant
  namespace: ai-services
spec:
  replicas: 2
  selector:
    matchLabels:
      app: campus-assistant
  template:
    metadata:
      labels:
        app: campus-assistant
    spec:
      # GPU 调度
      nodeSelector:
        nvidia.com/gpu: "true"
      containers:
        - name: ai-service
          image: registry.cn-hangzhou.aliyuncs.com/my-account/ai-service:v1
          imagePullPolicy: Always
          ports:
            - containerPort: 8000
          resources:
            limits:
              nvidia.com/gpu: 1
              memory: "32Gi"
              cpu: "8"
            requests:
              memory: "16Gi"
              cpu: "4"
          env:
            - name: MODEL_PATH
              value: /models/qwen
            - name: MAX_LENGTH
              value: "2048"
          volumeMounts:
            - name: model-volume
              mountPath: /models
          readinessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 60
            periodSeconds: 10
          livenessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 120
            periodSeconds: 30
      volumes:
        - name: model-volume
          persistentVolumeClaim:
            claimName: model-pvc
---
apiVersion: v1
kind: Service
metadata:
  name: campus-assistant-svc
  namespace: ai-services
spec:
  type: ClusterIP
  ports:
    - port: 80
      targetPort: 8000
  selector:
    app: campus-assistant
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: campus-assistant-hpa
  namespace: ai-services
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: campus-assistant
  minReplicas: 2
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
    - type: Pods
      pods:
        metric:
          name: inference_requests_per_second
        target:
          type: AverageValue
          averageValue: "10"
```

### 18.3.2 Helm Chart

```yaml
# helm/campus-assistant/Chart.yaml
apiVersion: v2
name: campus-assistant
description: 校园助手 AI 服务
type: application
version: 1.0.0
appVersion: "1.0"

# helm/campus-assistant/values.yaml
replicaCount: 2

image:
  repository: registry.cn-hangzhou.aliyuncs.com/my-account/ai-service
  tag: v1.0
  pullPolicy: Always

service:
  type: ClusterIP
  port: 80
  targetPort: 8000

resources:
  limits:
    nvidia.com/gpu: 1
    memory: 32Gi
    cpu: 8
  requests:
    memory: 16Gi
    cpu: 4

autoscaling:
  enabled: true
  minReplicas: 2
  maxReplicas: 10
  targetCPUUtilizationPercentage: 70

config:
  modelPath: /models/qwen
  maxLength: 2048
  temperature: 0.7

persistence:
  enabled: true
  storageClass: alicloud-nas
  size: 100Gi

ingress:
  enabled: true
  className: nginx
  annotations:
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
  hosts:
    - host: ai.example.com
      paths:
        - path: /
          pathType: Prefix

# helm/campus-assistant/templates/_helpers.tpl
{{/*
Expand the name of the chart.
*/}}
{{- define "campus-assistant.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "campus-assistant.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}
```

```bash
# 安装 Helm Chart
helm install campus-assistant ./helm/campus-assistant \
    --namespace ai-services \
    --create-namespace \
    --values ./helm/campus-assistant/values.yaml

# 升级
helm upgrade campus-assistant ./helm/campus-assistant \
    --namespace ai-services \
    --values ./helm/campus-assistant/values-prod.yaml

# 回滚
helm rollback campus-assistant -n ai-services

# 查看状态
helm status campus-assistant
kubectl get pods -n ai-services -l app=campus-assistant
```

---

## 18.4 监控与日志

### 18.4.1 监控体系

```python
# src/monitoring/prometheus.py
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from fastapi import FastAPI, Response
import time
from contextlib import asynccontextmanager

# 定义指标
REQUEST_COUNT = Counter(
    'ai_request_total',
    'Total AI requests',
    ['endpoint', 'status']
)

REQUEST_LATENCY = Histogram(
    'ai_request_latency_seconds',
    'Request latency',
    ['endpoint']
)

MODEL_LOADING_TIME = Gauge(
    'model_loading_time_seconds',
    'Model loading time'
)

GPU_MEMORY_USAGE = Gauge(
    'gpu_memory_usage_bytes',
    'GPU memory usage',
    ['device']
)

ACTIVE_REQUESTS = Gauge(
    'active_requests',
    'Number of active requests'
)

# 指标收集中间件
@asynccontextmanager
async def metrics_middleware(request: Request, call_next):
    endpoint = request.url.path
    start_time = time.time()
    
    ACTIVE_REQUESTS.inc()
    
    try:
        response = await call_next(request)
        status = response.status_code
    except Exception as e:
        status = 500
        raise
    finally:
        ACTIVE_REQUESTS.dec()
        duration = time.time() - start_time
        
        REQUEST_COUNT.labels(endpoint=endpoint, status=status).inc()
        REQUEST_LATENCY.labels(endpoint=endpoint).observe(duration)
    
    return response

# 指标端点
app = FastAPI()

@app.get("/metrics")
async def metrics():
    """Prometheus 抓取端点"""
    # 更新 GPU 指标
    try:
        import torch
        if torch.cuda.is_available():
            for i in range(torch.cuda.device_count()):
                memory_allocated = torch.cuda.memory_allocated(i)
                GPU_MEMORY_USAGE.labels(device=f"gpu:{i}").set(memory_allocated)
    except:
        pass
    
    return Response(
        content=generate_latest(),
        media_type="text/plain"
    )
```

```yaml
# prometheus.yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'ai-service'
    kubernetes_sd_configs:
      - role: pod
    relabel_configs:
      - source_labels: [__meta_kubernetes_pod_label_app]
        action: keep
        regex: campus-assistant
      - source_labels: [__meta_kubernetes_pod_container_port_number]
        action: keep
        regex: "8000"
      - action: labelmap
        regex: __meta_kubernetes_pod_label_(.+)
      - source_labels: [__meta_kubernetes_namespace]
        action: replace
        target_label: namespace
```

### 18.4.2 日志管理

```python
# src/logging/structured_logging.py
import logging
import json
import sys
from datetime import datetime
from typing import Any, Dict
from functools import wraps

class StructuredFormatter(logging.Formatter):
    """结构化日志格式"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # 添加额外字段
        if hasattr(record, "extra"):
            log_data.update(record.extra)
        
        # 添加异常信息
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_data)

def setup_logging(log_level: str = "INFO"):
    """设置日志"""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(StructuredFormatter())
    
    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    root_logger.setLevel(getattr(logging, log_level))
    
    # 第三方库日志级别
    logging.getLogger("transformers").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

# 请求日志中间件
async def log_requests(request: Request, call_next):
    """记录请求日志"""
    request_id = request.headers.get("X-Request-ID", generate_id())
    
    logger = logging.getLogger("api")
    logger.info(
        f"Request started",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "client": request.client.host
        }
    )
    
    start_time = time.time()
    try:
        response = await call_next(request)
        duration = time.time() - start_time
        
        logger.info(
            f"Request completed",
            extra={
                "request_id": request_id,
                "status": response.status_code,
                "duration_ms": int(duration * 1000)
            }
        )
        return response
    except Exception as e:
        duration = time.time() - start_time
        logger.error(
            f"Request failed",
            extra={
                "request_id": request_id,
                "error": str(e),
                "duration_ms": int(duration * 1000)
            }
        )
        raise
```

### 18.4.3 阿里云日志服务集成

```python
# src/logging/sls_handler.py
import logging
from typing import Any, Dict
from aliyun.log import LogClient, PutLogsRequest, LogGroup, LogItem
from datetime import datetime

class SLSHandler(logging.Handler):
    """阿里云日志服务处理器"""
    
    def __init__(
        self,
        endpoint: str,
        access_key_id: str,
        access_key_secret: str,
        project: str,
        logstore: str
    ):
        super().__init__()
        self.client = LogClient(endpoint, access_key_id, access_key_secret)
        self.project = project
        self.logstore = logstore
    
    def emit(self, record: logging.LogRecord):
        """发送日志到 SLS"""
        try:
            # 构建日志内容
            contents = [
                ("time", datetime.utcnow().isoformat()),
                ("level", record.levelname),
                ("logger", record.name),
                ("message", record.getMessage()),
            ]
            
            log_item = LogItem()
            for key, value in contents:
                log_item.push_back(key, str(value))
            
            # 发送到 SLS
            log_group = LogGroup()
            log_group.logs.append(log_item)
            
            request = PutLogsRequest(
                self.project,
                self.logstore,
                "",
                "",
                log_group
            )
            
            self.client.put_logs(request)
        except Exception as e:
            self.handleError(record)
```

---

## 18.5 安全与合规

### 18.5.1 API 安全

```python
# src/security/api_security.py
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.security import APIKeyHeader
from typing import Optional
import hashlib
import time

app = FastAPI()

# API Key 认证
API_KEY_HEADER = APIKeyHeader(name="X-API-Key")

async def verify_api_key(api_key: str = Depends(API_KEY_HEADER)) -> str:
    """验证 API Key"""
    valid_keys = {
        "key_live_xxx": {"name": "production", "rate": 100},
        "key_test_xxx": {"name": "test", "rate": 10}
    }
    
    if api_key not in valid_keys:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    
    return valid_keys[api_key]["name"]

# 请求限流
RATE_LIMIT_STORAGE = {}

def rate_limit(key: str, limit: int, window: int = 60):
    """简单限流装饰器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            now = time.time()
            if key not in RATE_LIMIT_STORAGE:
                RATE_LIMIT_STORAGE[key] = []
            
            # 清理过期记录
            RATE_LIMIT_STORAGE[key] = [
                t for t in RATE_LIMIT_STORAGE[key]
                if now - t < window
            ]
            
            if len(RATE_LIMIT_STORAGE[key]) >= limit:
                raise HTTPException(
                    status_code=429,
                    detail=f"Rate limit exceeded. Max {limit} requests per {window}s"
                )
            
            RATE_LIMIT_STORAGE[key].append(now)
            return await func(*args, **kwargs)
        return wrapper
    return decorator

# 内容安全过滤
class ContentFilter:
    """内容安全过滤"""
    
    SENSITIVE_PATTERNS = [
        r"\b\d{15,18}\b",  # 身份证号
        r"\b\d{16,19}\b",  # 银行卡号
        r"password[:=]\s*\S+",  # 密码泄露
    ]
    
    @classmethod
    def check(cls, text: str) -> tuple[bool, list]:
        """检查敏感内容"""
        import re
        
        matches = []
        for pattern in cls.SENSITIVE_PATTERNS:
            found = re.findall(pattern, text, re.IGNORECASE)
            matches.extend(found)
        
        return len(matches) == 0, matches
    
    @classmethod
    def mask_sensitive(cls, text: str) -> str:
        """脱敏处理"""
        import re
        
        # 身份证号
        text = re.sub(
            r"\b(\d{3})\d{11}(\d{4})\b",
            r"\1***********\2",
            text
        )
        
        # 手机号
        text = re.sub(
            r"\b(1[3-9]\d)\d{4}(\d{4})\b",
            r"\1****\2",
            text
        )
        
        return text

# 使用示例
@app.post("/chat")
@rate_limit(key="default", limit=100, window=60)
async def chat(
    request: Request,
    api_key: str = Depends(verify_api_key)
):
    body = await request.json()
    message = body.get("message", "")
    
    # 内容检查
    is_safe, matches = ContentFilter.check(message)
    if not is_safe:
        return {"error": "内容包含敏感信息，请修改后重试"}
    
    # 处理请求
    ...
```

### 18.5.2 容器安全

```dockerfile
# 安全加固的 Dockerfile
FROM python:3.11-slim

# 安全扫描检查
# 使用 Trivy: trivy image python:3.11-slim

# 1. 创建非 root 用户
RUN groupadd --gid 1000 appgroup && \
    useradd --uid 1000 --gid appgroup --shell /bin/false appuser

# 2. 复制文件（先设置权限）
COPY --chown=appuser:appgroup . /app

# 3. 切换用户
USER appuser

# 4. 只读文件系统
# 在 kubernetes 中配置: securityContext: readOnlyRootFilesystem: true

# 5. 禁止特权模式
# 在 kubernetes 中配置: securityContext: privileged: false

# 6. 丢弃所有 capabilities
# 在 kubernetes 中配置: securityContext: capabilities: { drop: ["ALL"] }
```

```yaml
# k8s/security-context.yaml
apiVersion: v1
kind: Pod
metadata:
  name: secure-pod
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 1000
    fsGroup: 1000
    seccompProfile:
      type: RuntimeDefault
  containers:
    - name: app
      image: my-app:v1
      securityContext:
        allowPrivilegeEscalation: false
        readOnlyRootFilesystem: true
        capabilities:
          drop:
            - ALL
      resources:
        limits:
          memory: 2Gi
          cpu: 1
        requests:
          memory: 1Gi
          cpu: 0.5
```

---

## 18.6 成本优化

### 18.6.1 成本监控

```python
# src/monitoring/cost_tracker.py
from datetime import datetime, timedelta
import json
from typing import Dict, List

class CostTracker:
    """成本追踪器"""
    
    def __init__(self):
        self.usage_records = []
    
    def record_request(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
        duration_ms: int
    ):
        """记录一次请求"""
        # 价格表（示例）
        PRICE_PER_1K_TOKENS = {
            "qwen-turbo": {"input": 0.002, "output": 0.006},
            "qwen-plus": {"input": 0.008, "output": 0.024},
        }
        
        if model not in PRICE_PER_1K_TOKENS:
            return
        
        prices = PRICE_PER_1K_TOKENS[model]
        input_cost = (input_tokens / 1000) * prices["input"]
        output_cost = (output_tokens / 1000) * prices["output"]
        total_cost = input_cost + output_cost
        
        self.usage_records.append({
            "timestamp": datetime.now().isoformat(),
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "duration_ms": duration_ms,
            "cost": total_cost
        })
    
    def get_daily_cost(self, date: datetime = None) -> float:
        """获取每日成本"""
        if date is None:
            date = datetime.now()
        
        start = date.replace(hour=0, minute=0, second=0)
        end = start + timedelta(days=1)
        
        return sum(
            r["cost"] for r in self.usage_records
            if start.isoformat() <= r["timestamp"] < end.isoformat()
        )
    
    def get_cost_breakdown(self) -> Dict:
        """获取成本分析"""
        model_costs = {}
        
        for r in self.usage_records:
            model = r["model"]
            if model not in model_costs:
                model_costs[model] = {"cost": 0, "requests": 0, "tokens": 0}
            
            model_costs[model]["cost"] += r["cost"]
            model_costs[model]["requests"] += 1
            model_costs[model]["tokens"] += r["input_tokens"] + r["output_tokens"]
        
        return model_costs
    
    def estimate_monthly_cost(self) -> float:
        """预估月度成本"""
        if not self.usage_records:
            return 0.0
        
        # 计算日均成本
        first_date = datetime.fromisoformat(self.usage_records[0]["timestamp"])
        last_date = datetime.fromisoformat(self.usage_records[-1]["timestamp"])
        days = max(1, (last_date - first_date).days)
        
        daily_cost = sum(r["cost"] for r in self.usage_records) / days
        
        # 预估 30 天
        return daily_cost * 30
```

### 18.6.2 优化策略

```python
# src/optimization/cost_optimizer.py
from typing import Optional

class CostOptimizer:
    """成本优化器"""
    
    @staticmethod
    def select_model(
        task: str,
        quality_requirement: str = "medium"
    ) -> str:
        """根据任务选择最优模型"""
        
        # 模型能力映射
        model_capabilities = {
            "qwen-turbo": {
                "strengths": ["快速响应", "简单问答", "文案生成"],
                "weaknesses": ["复杂推理", "长文本"]
            },
            "qwen-plus": {
                "strengths": ["复杂推理", "代码生成", "长文本理解"],
                "weaknesses": ["成本较高"]
            }
        }
        
        # 简单任务用小模型
        simple_tasks = ["闲聊", "简单问答", "格式转换"]
        if any(t in task for t in simple_tasks):
            return "qwen-turbo"
        
        # 复杂任务用大模型
        complex_tasks = ["代码生成", "分析推理", "专业领域"]
        if any(t in task for t in complex_tasks):
            return "qwen-plus"
        
        # 默认选择
        return "qwen-turbo"
    
    @staticmethod
    def optimize_prompt_tokens(
        system_prompt: str,
        user_prompt: str,
        max_tokens_budget: int = 4000
    ) -> tuple[str, str]:
        """优化 prompt 减少 token 消耗"""
        
        # 计算预估 token（粗略：中文约 2 char/token，英文约 4 char/token）
        def estimate_tokens(text: str) -> int:
            chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
            other_chars = len(text) - chinese_chars
            return chinese_chars // 2 + other_chars // 4
        
        system_tokens = estimate_tokens(system_prompt)
        user_tokens = estimate_tokens(user_prompt)
        total_tokens = system_tokens + user_tokens
        
        if total_tokens <= max_tokens_budget:
            return system_prompt, user_prompt
        
        # 精简 system prompt
        if system_tokens > 500:
            # 保留核心指令
           精简后的_prompt = system_prompt[:1000]
            return 精简后的_prompt, user_prompt
        
        # 精简 user prompt
        max_user = max_tokens_budget - system_tokens
        return system_prompt, user_prompt[:max_user * 4]
    
    @staticmethod
    def batch_requests(
        requests: list,
        batch_size: int = 10
    ) -> list:
        """批量处理请求以节省成本"""
        # 某些 API 支持批量请求，单价更低
        batches = [
            requests[i:i + batch_size]
            for i in range(0, len(requests), batch_size)
        ]
        return batches
```

---

## 18.7 本章小结

本章介绍了云原生部署与运维的完整实践：

| 主题 | 核心要点 |
|------|----------|
| **Docker 部署** | 多阶段构建、GPU 支持、模型文件处理 |
| **函数计算** | FC 部署 AI 应用、Serverless Devs |
| **Kubernetes** | ACK 部署、Helm Chart、HPA |
| **监控日志** | Prometheus 指标、结构化日志、SLS |
| **安全合规** | API 认证、内容过滤、容器安全 |
| **成本优化** | 成本追踪、模型选择、Prompt 优化 |

### 部署方案选型

| 场景 | 推荐方案 |
|------|----------|
| 个人项目 | Docker + 本地部署 |
| 小规模应用 | 函数计算 FC |
| 中等规模 | ACK + GPU 实例 |
| 大规模生产 | ACK + 弹性伸缩 + 负载均衡 |

---

## 延伸阅读

- [Docker 官方文档](https://docs.docker.com/)
- [阿里云函数计算文档](https://help.aliyun.com/zh/fc/)
- [阿里云 ACK 文档](https://help.aliyun.com/zh/ack/)
- [Prometheus 监控指南](https://prometheus.io/docs/introduction/overview/)
- [Kubernetes 安全最佳实践](https://kubernetes.io/docs/concepts/security/)
