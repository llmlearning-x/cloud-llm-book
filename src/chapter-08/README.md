# 第 8 章 大模型应用部署与运维

> **本章导读**
> 
> 从开发环境到生产环境的部署与运维是大模型应用落地的最后一公里。本章将讲解容器化部署、CI/CD流程、灰度发布策略、监控告警体系、故障排查方法等生产环境必备技能。
> 
> **核心议题：**
> - Docker 容器化部署
> - Kubernetes 集群编排
> - CI/CD自动化流程
> - 灰度发布与回滚
> - 监控告警体系
> - 故障排查与应急响应

---

## 8.1 容器化部署

### 8.1.1 Dockerfile 编写

```dockerfile
# 基础镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制代码
COPY . .

# 设置环境变量
ENV DASHSCOPE_API_KEY=${DASHSCOPE_API_KEY}
ENV LOG_LEVEL=INFO

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 启动命令
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 8.1.2 Docker Compose 编排

```yaml
version: '3.8'

services:
  # 大模型应用服务
  llm-app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DASHSCOPE_API_KEY=${DASHSCOPE_API_KEY}
      - REDIS_HOST=redis
      - MYSQL_HOST=mysql
    depends_on:
      - redis
      - mysql
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '2'
          memory: 4G
    restart: always
  
  # Redis 缓存
  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis-data:/data
    ports:
      - "6379:6379"
  
  # MySQL 数据库
  mysql:
    image: mysql:8.0
    environment:
      - MYSQL_ROOT_PASSWORD=${MYSQL_ROOT_PASSWORD}
      - MYSQL_DATABASE=llm_app
    volumes:
      - mysql-data:/var/lib/mysql
    ports:
      - "3306:3306"
  
  # Nginx 反向代理
  nginx:
    image: nginx:alpine
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    ports:
      - "80:80"
      - "443:443"
    depends_on:
      - llm-app

volumes:
  redis-data:
  mysql-data:
```

### 8.1.3 Kubernetes 部署

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: llm-app-deployment
spec:
  replicas: 3
  selector:
    matchLabels:
      app: llm-app
  template:
    metadata:
      labels:
        app: llm-app
    spec:
      containers:
      - name: llm-app
        image: registry.cn-beijing.aliyuncs.com/your-namespace/llm-app:v1.0.0
        ports:
        - containerPort: 8000
        env:
        - name: DASHSCOPE_API_KEY
          valueFrom:
            secretKeyRef:
              name: llm-secrets
              key: dashscope-api-key
        - name: REDIS_HOST
          value: "redis-service"
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5

---
# service.yaml
apiVersion: v1
kind: Service
metadata:
  name: llm-app-service
spec:
  selector:
    app: llm-app
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer

---
# hpa.yaml (自动扩缩容)
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: llm-app-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: llm-app-deployment
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

---

## 8.2 CI/CD自动化流程

### 8.2.1 GitHub Actions 配置

```yaml
# .github/workflows/deploy.yml
name: Deploy LLM Application

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  # 测试
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-cov
    
    - name: Run tests
      run: pytest --cov=app tests/
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3

  # 构建镜像
  build:
    needs: test
    runs-on: ubuntu-latest
    if: github.event_name == 'push'
    steps:
    - uses: actions/checkout@v3
    
    - name: Login to ACR
      uses: docker/login-action@v2
      with:
        registry: registry.cn-beijing.aliyuncs.com
        username: ${{ secrets.ACR_USERNAME }}
        password: ${{ secrets.ACR_PASSWORD }}
    
    - name: Build and push
      uses: docker/build-push-action@v4
      with:
        context: .
        push: true
        tags: |
          registry.cn-beijing.aliyuncs.com/your-namespace/llm-app:${{ github.sha }}
          registry.cn-beijing.aliyuncs.com/your-namespace/llm-app:latest

  # 部署到测试环境
  deploy-staging:
    needs: build
    runs-on: ubuntu-latest
    environment: staging
    steps:
    - uses: azure/k8s-set-context@v3
      with:
        kubeconfig: ${{ secrets.K8S_CONFIG_STAGING }}
    
    - name: Deploy to staging
      run: |
        kubectl set image deployment/llm-app-deployment \
          llm-app=registry.cn-beijing.aliyuncs.com/your-namespace/llm-app:${{ github.sha }}
        kubectl rollout status deployment/llm-app-deployment

  # 部署到生产环境（需审批）
  deploy-production:
    needs: deploy-staging
    runs-on: ubuntu-latest
    environment: production
    steps:
    - uses: azure/k8s-set-context@v3
      with:
        kubeconfig: ${{ secrets.K8S_CONFIG_PRODUCTION }}
    
    - name: Deploy to production
      run: |
        kubectl set image deployment/llm-app-deployment \
          llm-app=registry.cn-beijing.aliyuncs.com/your-namespace/llm-app:${{ github.sha }}
        kubectl rollout status deployment/llm-app-deployment
```

### 8.2.2 蓝绿部署

```yaml
# 蓝绿部署脚本
#!/bin/bash

CURRENT_VERSION=$1
NEW_VERSION=$2
NAMESPACE="llm-prod"

echo "开始蓝绿部署：$CURRENT_VERSION -> $NEW_VERSION"

# 1. 部署新版本（绿色）
kubectl apply -f deployment-green.yaml -n $NAMESPACE
kubectl set image deployment/llm-app-green llm-app=registry.cn-beijing.aliyuncs.com/your-namespace/llm-app:$NEW_VERSION -n $NAMESPACE

# 2. 等待绿色就绪
kubectl rollout status deployment/llm-app-green -n $NAMESPACE

# 3. 运行冒烟测试
./run-smoke-tests.sh green

# 4. 切换流量
kubectl patch service llm-app-service -n $NAMESPACE -p '{"spec":{"selector":{"pod-template-hash":"green"}}}'

# 5. 观察 10 分钟
sleep 600

# 6. 如果没有问题，删除蓝色（旧版本）
kubectl delete deployment llm-app-blue -n $NAMESPACE

echo "蓝绿部署完成！"
```

---

## 8.3 监控告警体系

### 8.3.1 日志收集

```yaml
# Fluentd 配置
<match llm.**>
  @type elasticsearch
  host elasticsearch.logging.svc
  port 9200
  logstash_format true
  logstash_prefix llm-logs
  flush_interval 5s
</match>
```

**日志结构化：**

```python
import logging
import json

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            'timestamp': self.formatTime(record),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # 添加额外字段
        if hasattr(record, 'user_id'):
            log_entry['user_id'] = record.user_id
        if hasattr(record, 'request_id'):
            log_entry['request_id'] = record.request_id
        if hasattr(record, 'token_usage'):
            log_entry['token_usage'] = record.token_usage
        
        return json.dumps(log_entry, ensure_ascii=False)

# 配置日志
handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logger.addHandler(handler)
```

### 8.3.2 告警规则

```yaml
# Prometheus AlertManager 配置
groups:
- name: llm-alerts
  rules:
  # 高错误率告警
  - alert: HighErrorRate
    expr: rate(llm_requests_error_total[5m]) / rate(llm_requests_total[5m]) > 0.05
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "大模型应用错误率超过 5%"
      description: "当前错误率：{{ $value | humanizePercentage }}"
  
  # 高延迟告警
  - alert: HighLatency
    expr: histogram_quantile(0.95, rate(llm_request_latency_seconds_bucket[5m])) > 1
    for: 10m
    labels:
      severity: warning
    annotations:
      summary: "P95 延迟超过 1 秒"
      description: "当前 P95 延迟：{{ $value | humanizeDuration }}"
  
  # Token 配额即将耗尽
  - alert: TokenQuotaLow
    expr: llm_token_quota_remaining < 100000
    for: 1h
    labels:
      severity: warning
    annotations:
      summary: "Token 配额剩余不足 10 万"
      description: "剩余 Token: {{ $value }}"
  
  # Pod 重启频繁
  - alert: PodRestartingFrequently
    expr: rate(kube_pod_container_status_restarts_total[1h]) > 0.5
    for: 15m
    labels:
      severity: warning
    annotations:
      summary: "Pod 频繁重启"
      description: "过去 1 小时重启次数：{{ $value }}"
```

### 8.3.3 告警通知

```yaml
# AlertManager 通知配置
receivers:
- name: 'dingtalk'
  webhook_configs:
  - url: 'http://webhook-dingtalk.monitoring.svc:8060/dingtalk/webhook1/send'
    send_resolved: true

- name: 'email'
  email_configs:
  - to: 'team@example.com'
    from: 'alerts@example.com'
    smarthost: 'smtp.example.com:587'
    auth_username: 'alerts@example.com'
    auth_password: 'xxx'

- name: 'sms'
  webhook_configs:
  - url: 'http://sms-gateway.monitoring.svc/send'
    send_resolved: false  # 只发送告警，不发送恢复通知

route:
  receiver: 'dingtalk'
  routes:
  - match:
      severity: critical
    receiver: 'sms'
    continue: true
  - match:
      severity: warning
    receiver: 'email'
```

---

## 8.4 故障排查

### 8.4.1 常见问题诊断树

```
用户报告"请求失败"
    │
    ├─ 检查错误日志
    │   ├─ "RateLimitExceeded" → 限流了，检查配额
    │   ├─ "Timeout" → 检查网络和后端负载
    │   └─ "InternalError" → 检查服务端状态
    │
    ├─ 检查指标
    │   ├─ 错误率突增 → 查看最近变更
    │   ├─ 延迟升高 → 检查资源使用率
    │   └─ QPS 下降 → 检查上游流量
    │
    └─ 复现问题
        ├─ 所有用户都失败 → 系统性故障
        └─ 部分用户失败 → 个别场景问题
```

### 8.4.2 排查命令速查

```bash
# 查看 Pod 状态
kubectl get pods -n llm-prod
kubectl describe pod <pod-name> -n llm-prod

# 查看日志
kubectl logs -f deployment/llm-app-deployment -n llm-prod
kubectl logs -f <pod-name> -c llm-app -n llm-prod --tail=1000

# 进入容器调试
kubectl exec -it <pod-name> -n llm-prod -- /bin/bash

# 查看资源使用
kubectl top pods -n llm-prod
kubectl top nodes

# 查看事件
kubectl get events -n llm-prod --sort-by='.lastTimestamp'

# 临时扩容
kubectl scale deployment llm-app-deployment --replicas=10 -n llm-prod

# 回滚到上一版本
kubectl rollout undo deployment/llm-app-deployment -n llm-prod
```

### 8.4.3 应急预案模板

```markdown
# 应急预案：大模型服务中断

## 故障等级
P0 - 核心功能完全不可用

## 响应流程

### 1. 发现与确认（5 分钟内）
- [ ] 收到告警
- [ ] 确认故障范围
- [ ] 拉起应急会议

### 2. 初步处置（15 分钟内）
- [ ] 切换到备用服务
- [ ] 通知客服团队准备话术
- [ ] 发送用户公告

### 3. 问题定位（30 分钟内）
- [ ] 收集相关日志
- [ ] 分析最近变更
- [ ] 联系阿里云技术支持

### 4. 恢复服务
- [ ] 执行修复方案
- [ ] 验证服务恢复
- [ ] 逐步恢复流量

### 5. 事后复盘
- [ ] 编写故障报告
- [ ] 制定改进措施
- [ ] 更新应急预案
```

---

## 本章小结

本章系统讲解了大模型应用的部署与运维：

1. **容器化部署**：Docker 打包、Compose 编排、Kubernetes 集群管理
2. **CI/CD 流程**：GitHub Actions 自动化构建、测试、部署
3. **发布策略**：蓝绿部署、金丝雀发布、自动回滚
4. **监控告警**：日志收集、指标监控、多级告警通知
5. **故障排查**：诊断树、命令速查、应急预案

稳定的运维体系是大模型应用持续服务用户的保障。技术决策者应重视运维能力建设，将 SRE 理念融入日常工作中。

---

## 延伸阅读

1. [Kubernetes 官方文档](https://kubernetes.io/docs/)
2. 《Site Reliability Engineering》- Google
3. [Prometheus 监控最佳实践](https://prometheus.io/docs/practices/)
4. 阿里云 ACK 服务文档：https://help.aliyun.com/product/44857.html

---

**下一章预告**：第 9 章将介绍行业解决方案与实践案例，包括智能客服、企业知识库、代码助手、营销文案生成等典型应用场景的落地经验。