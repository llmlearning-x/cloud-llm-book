# 第 2 章：阿里云核心产品（上）

> 本章聚焦三款与大模型应用开发最密切相关的产品：对象存储 OSS、函数计算 FC 和 API 网关。掌握这三款产品，就掌握了云端 AI 应用的数据存储、计算执行和流量入口。

## 本章内容

- 对象存储 OSS：云端文件存储
- 函数计算 FC：Serverless 计算服务
- API 网关：API 管理与流量控制

---

## 2.1 对象存储 OSS

### 2.1.1 什么是 OSS

**OSS（Object Storage Service）** 是阿里云提供的海量、安全、低成本、高可靠的云存储服务。它专门用于存储文件（称为"对象"），支持任意类型的数据。

**与传统的文件系统相比**：

| 特性 | 传统文件系统 | OSS |
|------|-------------|-----|
| 存储规模 | 单机TB级 | 理论上无限PB级 |
| 访问方式 | 挂载到单机 | HTTP/HTTPS API |
| 扩展性 | 需要扩容硬件 | 一键扩容 |
| 成本 | 硬件+运维成本高 | 按量付费 |
| 持久性 | 99.9% | 99.999999999% (11个9) |

### 2.1.2 核心概念

**Bucket（存储空间）**：
- OSS 的顶层容器
- 每个 Bucket 有唯一的域名：`<bucket>.oss-<region>.aliyuncs.com`
- 可以设置访问权限（公共读、私有等）

**Object（对象）**：
- OSS 中存储的基本单元
- 由 Key（文件名）+ Meta（元数据）+ Data（数据）组成
- Key 支持路径格式：`folder/subfolder/file.txt`

**Region（地域）**：
- 数据中心所在的地理区域
- 如：华东1（杭州）、华北2（北京）、华南1（深圳）
- 建议选择离用户最近的地域，减少延迟

### 2.1.3 OSS 基本操作

**Python SDK 示例**：

```python
import oss2
from dotenv import load_dotenv
import os

# 加载环境变量
load_dotenv()

# 获取凭证
access_key_id = os.getenv('OSS_ACCESS_KEY_ID')
access_key_secret = os.getenv('OSS_ACCESS_KEY_SECRET')
bucket_name = 'cloud-llm-demo'
endpoint = 'https://oss-cn-hangzhou.aliyuncs.com'

# 初始化 Bucket
auth = oss2.Auth(access_key_id, access_key_secret)
bucket = oss2.Bucket(auth, endpoint, bucket_name)

# 上传文件
def upload_file(local_path, oss_key):
    """上传文件到 OSS"""
    result = bucket.put_object(oss_key, open(local_path, 'rb').read())
    if result.status == 200:
        print(f"上传成功: {oss_key}")
        print(f"URL: https://{bucket_name}{endpoint.replace('https://', '/')}/{oss_key}")
    return result.status == 200

# 下载文件
def download_file(oss_key, local_path):
    """从 OSS 下载文件"""
    result = bucket.get_object(oss_key)
    if result.status == 200:
        with open(local_path, 'wb') as f:
            f.write(result.read())
        print(f"下载成功: {local_path}")
        return True
    return False

# 列举文件
def list_files(prefix=''):
    """列举 Bucket 中的文件"""
    for obj in oss2.ObjectIterator(bucket, prefix=prefix):
        print(f"  {obj.key} ({obj.size} bytes)")

# 删除文件
def delete_file(oss_key):
    """删除 OSS 文件"""
    result = bucket.delete_object(oss_key)
    print(f"删除状态: {result.status}")
    return result.status == 204

# 示例调用
if __name__ == '__main__':
    # 上传训练数据
    upload_file('data/train.json', 'training/train.json')
    
    # 列举所有训练数据
    print("\n训练数据列表:")
    list_files('training/')
    
    # 下载模型文件
    download_file('models/llm-v1.bin', './local-model.bin')
```

### 2.1.4 OSS 在大模型应用中的典型场景

```
┌─────────────────────────────────────────────────────────────┐
│                    大模型应用中的 OSS                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    │
│  │  训练数据    │    │  模型文件   │    │  用户上传   │    │
│  │  存储       │    │  存储       │    │  内容存储   │    │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘    │
│         │                  │                  │            │
│         └──────────────────┼──────────────────┘            │
│                            ▼                               │
│                    ┌───────────────┐                       │
│                    │   OSS Bucket  │                       │
│                    └───────────────┘                       │
│                            │                               │
│         ┌──────────────────┼──────────────────┐           │
│         ▼                  ▼                  ▼           │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    │
│  │  PAI 训练   │    │  函数计算   │    │  CDN 加速   │    │
│  │  读取数据   │    │  读取文件   │    │  分发内容   │    │
│  └─────────────┘    └─────────────┘    └─────────────┘    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 2.2 函数计算 FC

### 2.2.1 什么是函数计算

**函数计算 FC（Function Compute）** 是阿里云提供的 Serverless 计算服务。它允许你编写和部署代码，无需管理服务器。函数计算会自动为你处理服务器的扩容、负载均衡、高可用等基础设施问题。

**Serverless = 无服务器 ≠ 没有服务器**：
- 你不需要关心服务器的存在
- 背后的服务器由云厂商管理和维护
- 按实际执行时间计费，不执行不收费

### 2.2.2 核心概念

**Function（函数）**：
- 函数计算的基本单元
- 一个函数包含：代码、配置（内存、超时时间）、触发器
- 支持多种运行时：Python、Node.js、Java、PHP、Go 等

**Trigger（触发器）**：
- 触发函数执行的事件源
- 支持：HTTP 调用、定时任务、OSS 事件、API 网关、MQ 消息等
- 一个函数可以绑定多个触发器

**Execution Role（执行角色）**：
- 函数运行时使用的权限身份
- 通过 RAM 角色控制函数可以访问的云资源

### 2.2.3 第一个 Serverless 函数

**1. 安装函数计算工具**：

```bash
# 安装 fun 工具（函数计算的命令行工具）
npm install @alicloud/fun -g

# 验证安装
fun --version
```

**2. 创建函数项目**：

```bash
# 创建项目目录
mkdir fc-ai-demo && cd fc-ai-demo
mkdir -p code

# 创建函数代码
cat > code/index.py << 'EOF'
# -*- coding: utf-8 -*-
import json

def handler(event, context):
    """
    事件处理函数
    event: 触发事件（JSON 字符串）
    context: 运行环境信息
    """
    # 解析事件
    payload = json.loads(event)
    name = payload.get('name', 'World')
    
    # 返回响应
    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': f'Hello, {name}!',
            'source': 'Serverless Function'
        }),
        'headers': {
            'Content-Type': 'application/json'
        }
    }
EOF

# 创建配置文件
cat > template.yml << 'EOF'
ROSTemplateFormatVersion: '2015-09-01'
Transform: 'Aliyun::Serverless-2018-04-03'

Service:
  ai-demo-service:
    Description: 'AI 应用 Serverless 服务'
    Policies:
      - AliyunOSSFullAccess  # 函数需要访问 OSS

Function:
  hello-function:
    Handler: index.handler
    Runtime: python3.10
    CodeUri: ./code
    MemorySize: 512
    Timeout: 60
    EnvironmentVariables:
      REGION: cn-hangzhou

Trigger:
  http-trigger:
    Type: HTTP
    Properties:
      AuthType: ANONYMOUS
      Methods:
        - GET
        - POST
EOF
```

**3. 部署函数**：

```bash
# 部署（需要先配置 AccessKey）
fun deploy

# 部署输出示例：
# function hello-function deploy success
# trigger http-trigger deploy success
# url: https://ai-demo-service-hz12345.cn-hangzhou.fc.aliyuncs.com/2016-08-15/proxy/hello-function/hello/
```

**4. 调用函数**：

```bash
# 测试 HTTP 调用
curl https://ai-demo-service-hz12345.cn-hangzhou.fc.aliyuncs.com/2016-08-15/proxy/hello-function/hello/ \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"name": "Cloud AI"}'

# 响应：
# {"message": "Hello, Cloud AI!", "source": "Serverless Function"}
```

### 2.2.4 函数计算的高级特性

**1. 异步调用与回调**：

```python
def async_handler(event, context):
    """异步处理长时间任务"""
    import time
    client = fc2.Client(
        endpoint=context.account_id + '.cn-hangzhou.fc.aliyuncs.com',
        access_key_id=context.credentials.access_key_id,
        access_key_secret=context.credentials.access_key_secret,
        security_token=context.credentials.security_token
    )
    
    # 模拟耗时任务
    time.sleep(5)
    
    # 返回任务ID
    return {
        'statusCode': 202,
        'body': json.dumps({
            'taskId': 'async-' + str(int(time.time())),
            'status': 'processing'
        })
    }
```

**2. 访问云资源（OSS）**：

```python
import oss2

def handler(event, context):
    """函数中访问 OSS"""
    creds = context.credentials
    
    # 使用函数执行角色的临时凭证访问 OSS
    auth = oss2.StsAuth(
        creds.access_key_id,
        creds.access_key_secret,
        creds.security_token
    )
    
    bucket = oss2.Bucket(auth, 'oss-cn-hangzhou.aliyuncs.com', 'my-bucket')
    
    # 读取文件
    result = bucket.get_object('data/input.txt')
    content = result.read().decode('utf-8')
    
    return {
        'statusCode': 200,
        'body': json.dumps({'content_length': len(content)})
    }
```

**3. 并发执行与流量控制**：

```yaml
# template.yml 中配置并发
Function:
  llm-function:
    Handler: index.handler
    Runtime: python3.10
    MemorySize: 1024
    
    # 并发设置
    InstanceConcurrency: 10  # 单实例最大并发数
    
    # 预留实例（冷启动优化）
    CustomRuntimeConfig:
      Command: ['python', '-m', 'mylib.app']
      InstanceType: e1
```

### 2.2.5 函数计算 vs ECS

| 维度 | 函数计算 FC | 云服务器 ECS |
|------|-------------|-------------|
| **计费方式** | 按调用次数+执行时长 | 包月/包年 |
| **扩缩容** | 自动（毫秒级） | 手动（分钟级） |
| **适用场景** | 事件驱动、间歇性负载 | 持续负载、常驻进程 |
| **冷启动** | 首次调用有延迟 | 无冷启动 |
| **运行环境** | 受限（无 SSH 访问） | 完全控制 |
| **价格** | 适合低频调用 | 适合高频使用 |

**经验法则**：
- 流量波动大、不可预测 → 函数计算
- 持续稳定流量 → ECS
- 两者结合 → 用 ECS 跑核心服务，函数计算处理突发流量

---

## 2.3 API 网关

### 2.3.1 什么是 API 网关

**API 网关（API Gateway）** 是管理和保护 API 的服务。它作为所有 API 请求的统一入口，提供请求路由、协议转换、流量控制、安全认证等功能。

### 2.3.2 API 网关的核心功能

```
┌─────────────────────────────────────────────────────────────┐
│                       API 网关                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐  │
│  │ 请求路由 │   │ 流量控制 │   │ 安全认证│   │ 日志监控│  │
│  │         │   │         │   │         │   │         │  │
│  │ 根据路径 │   │ 限流限速 │   │ API Key │   │ 调用统计│  │
│  │ 分发请求 │   │ 熔断降级 │   │ JWT认证 │   │ 错误追踪│  │
│  └────┬────┘   └────┬────┘   └────┬────┘   └────┬────┘  │
│       │             │             │             │         │
│       └─────────────┴─────────────┴─────────────┘         │
│                             │                              │
└─────────────────────────────┼──────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
        ┌─────────┐    ┌─────────┐    ┌─────────┐
        │ 函数计算 │    │  ECS    │    │  PAI    │
        │   FC    │    │ 服务器  │    │ 推理服务 │
        └─────────┘    └─────────┘    └─────────┘
```

### 2.3.3 创建 API 分组

**1. 通过控制台创建**：

1. 登录阿里云 API 网关控制台
2. 创建 API 分组（每个分组有独立域名）
3. 定义 API：请求方法、路径、后端服务类型
4. 绑定域名（可选，使用自定义域名）

**2. Python SDK 创建 API**：

```python
from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.request import CommonRequest
import os

# 初始化客户端
client = AcsClient(
    os.getenv('ACCESS_KEY_ID'),
    os.getenv('ACCESS_KEY_SECRET'),
    'cn-hangzhou'
)

def create_api_group():
    """创建 API 分组"""
    request = CommonRequest()
    request.set_method('POST')
    request.set_domain('apigateway.aliyuncs.com')
    request.set_version('2016-05-03')
    request.set_action_name('CreateApiGroup')
    
    request.add_query_param('GroupName', 'ai-chat-api')
    request.add_query_param('Description', 'AI 对话应用 API')
    
    response = client.do_action_with_exception(request)
    result = json.loads(response.decode('utf-8'))
    
    print(f"API 分组 ID: {result['ApiGroupId']}")
    print(f"二级域名: {result['SubDomain']}")
    return result

def create_chat_api(group_id):
    """创建对话 API"""
    request = CommonRequest()
    request.set_method('POST')
    request.set_domain('apigateway.aliyuncs.com')
    request.set_version('2016-05-03')
    request.set_action_name('CreateApi')
    
    request.add_query_param('GroupId', group_id)
    request.add_query_param('ApiName', 'chat_completion')
    request.add_query_param('Visibility', 'PRIVATE')
    request.add_query_param('RequestConfig', json.dumps({
        'RequestHttpMethod': 'POST',
        'RequestPath': '/v1/chat/completion',
        'BodyFormat': 'FORM'
    }))
    request.add_query_param('ServiceConfig', json.dumps({
        'ServiceType': 'FunctionCompute',
        'ServiceName': 'ai-demo-service',
        'FunctionName': 'chat-function',
        'ServiceTimeout': 60
    }))
    request.add_query_param('RequestParameters', json.dumps([
        {
            'ApiParameterName': 'prompt',
            'Location': 'BODY',
            'Required': 'REQUIRED',
            'Type': 'STRING'
        }
    ]))
    
    response = client.do_action_with_exception(request)
    return json.loads(response.decode('utf-8'))
```

### 2.3.4 API 安全认证

**1. API Key 认证（简单场景）**：

```python
# 请求时携带 API Key
headers = {
    'Authorization': 'APPCODE your_app_code_here',
    'Content-Type': 'application/json'
}

response = requests.post(
    'https://your-api.cn-hangzhou.aliyuncs.com/v1/chat/completion',
    headers=headers,
    json={'prompt': 'Hello!'}
)
```

**2. JWT 认证（推荐）**：

```python
import jwt
import time

def generate_jwt_token(user_id, api_key):
    """生成 JWT Token"""
    payload = {
        'iss': 'your-app',
        'sub': str(user_id),
        'iat': int(time.time()),
        'exp': int(time.time()) + 3600  # 1小时后过期
    }
    
    token = jwt.encode(payload, api_key, algorithm='HS256')
    return token

def verify_jwt_token(token, api_key):
    """验证 JWT Token"""
    try:
        payload = jwt.decode(token, api_key, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None  # Token 已过期
    except jwt.InvalidTokenError:
        return None  # Token 无效
```

### 2.3.5 流量控制配置

```yaml
# API 网关流量控制策略
AppQuota:
  - AppKey: your-app-key
    QuotaLimit: 1000          # 每分钟最多 1000 次
    QuotaRefreshPeriod: 1     # 刷新周期（分钟）
    
# 用户级限流
UserQuota:
  - UserId: user-123
    QuotaLimit: 100          # 每分钟最多 100 次
```

---

## 2.4 本章小结

本章介绍了三款与大模型应用开发最密切相关的阿里云产品：

| 产品 | 核心价值 | 典型场景 |
|------|----------|----------|
| **OSS** | 海量文件存储 | 训练数据、模型文件、用户内容 |
| **函数计算 FC** | Serverless 计算 | AI 推理、事件处理、定时任务 |
| **API 网关** | API 管理与保护 | 统一入口、流量控制、安全认证 |

**三者的典型组合**：

```
用户请求 → API 网关（鉴权、限流） → 函数计算（业务逻辑）
                                              ↓
                                        OSS（读取数据）
                                              ↓
                                        返回结果
```

下一章我们将继续学习容器服务、数据库和监控日志服务，完善云端 AI 应用的运维能力。

---

## 思考与练习

1. **产品选型**：你的团队要开发一个 AI 写作助手，用户会上传文档进行摘要，请分析需要使用哪些云产品，画出架构图
2. **成本优化**：假设你的应用日均调用 10 万次，每次函数执行 100ms，内存 512MB，计算函数计算的成本，并与 ECS（4核8G，月付 500 元）对比
3. **安全实践**：设计一个 API 网关的安全策略，包括：JWT 认证、API Key 管理、IP 白名单、调用频率限制
