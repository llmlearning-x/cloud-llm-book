# 2.4 网络与安全架构

## 场景引入

某金融机构计划在阿里云上部署智能投顾系统，需要处理客户的敏感财务数据。合规部门提出以下要求：

1. 所有数据传输必须加密
2. 大模型 API 调用不能经过公网
3. API Key 等敏感凭证必须安全存储
4. 所有操作必须有审计日志
5. 符合金融行业的数据隔离要求

技术团队面临的核心问题是：如何设计安全的网络架构？如何保护敏感数据？如何满足合规要求？

本节将系统地解答这些问题。

---

## 2.4.1 VPC 私有网络规划

### 为什么需要 VPC

VPC（Virtual Private Cloud）是阿里云提供的隔离的虚拟网络环境。对于大模型应用，使用 VPC 的主要价值在于：

- **网络隔离**：不同业务系统的资源相互隔离，避免干扰
- **安全控制**：通过安全组和网络 ACL 精细控制访问权限
- **私网通信**：阿里云服务之间通过内网通信，延迟更低、更安全
- **混合云连接**：通过 VPN 或专线连接本地数据中心

### VPC 架构设计

典型的三层网络架构：

```
┌──────────────────────────────────────────────────────┐
│                    VPC: 10.0.0.0/16                  │
├──────────────────────────────────────────────────────┤
│  公有子网 (Public Subnet): 10.0.1.0/24               │
│  ┌──────────────┐  ┌──────────────┐                 │
│  │  NAT Gateway  │  │  Bastion Host │                │
│  └──────────────┘  └──────────────┘                 │
├──────────────────────────────────────────────────────┤
│  应用子网 (Application Subnet): 10.0.2.0/24          │
│  ┌──────────────┐  ┌──────────────┐                 │
│  │  Web Server   │  │  App Server   │                │
│  └──────────────┘  └──────────────┘                 │
├──────────────────────────────────────────────────────┤
│  数据子网 (Data Subnet): 10.0.3.0/24                 │
│  ┌──────────────┐  ┌──────────────┐                 │
│  │  RDS/PolarDB  │  │  Redis Cache  │                │
│  └──────────────┘  └──────────────┘                 │
└──────────────────────────────────────────────────────┘
```

**设计原则：**

1. **最小权限**：每个子网只开放必要的端口和协议
2. **分层隔离**：Web 层、应用层、数据层分别部署在不同子网
3. **单向访问**：数据层只能被应用层访问，不能被 Web 层直接访问
4. **堡垒机接入**：运维人员通过堡垒机访问内部资源

### 快速入门

**步骤一：创建 VPC 和交换机**

```python
from alibabacloud_vpc20160428.client import Client
from alibabacloud_vpc20160428.models import CreateVpcRequest, CreateVSwitchRequest

client = Client(
    access_key_id=os.getenv('ALIBABA_CLOUD_ACCESS_KEY_ID'),
    access_key_secret=os.getenv('ALIBABA_CLOUD_ACCESS_KEY_SECRET')
)

# 创建 VPC
vpc_request = CreateVpcRequest(
    region_id='cn-beijing',
    cidr_block='10.0.0.0/16',
    vpc_name='llm-app-vpc',
    description='大模型应用 VPC'
)
vpc_response = client.create_vpc(vpc_request)
vpc_id = vpc_response.body.vpc_id
print(f"VPC 创建成功: {vpc_id}")

# 创建交换机（子网）
zones = ['cn-beijing-a', 'cn-beijing-b', 'cn-beijing-c']
subnet_cidrs = ['10.0.1.0/24', '10.0.2.0/24', '10.0.3.0/24']
subnet_names = ['public-subnet', 'app-subnet', 'data-subnet']

vswitch_ids = []
for zone, cidr, name in zip(zones, subnet_cidrs, subnet_names):
    vswitch_request = CreateVSwitchRequest(
        region_id='cn-beijing',
        vpc_id=vpc_id,
        cidr_block=cidr,
        zone_id=zone,
        v_switch_name=name
    )
    vswitch_response = client.create_vswitch(vswitch_request)
    vswitch_ids.append(vswitch_response.body.v_switch_id)
    print(f"交换机创建成功: {name} - {vswitch_response.body.v_switch_id}")
```

**步骤二：配置安全组**

```python
from alibabacloud_ecs20140526.client import Client as EcsClient
from alibabacloud_ecs20140526.models import CreateSecurityGroupRequest, AuthorizeSecurityGroupRequest

ecs_client = EcsClient(
    access_key_id=os.getenv('ALIBABA_CLOUD_ACCESS_KEY_ID'),
    access_key_secret=os.getenv('ALIBABA_CLOUD_ACCESS_KEY_SECRET')
)

# 创建安全组
sg_request = CreateSecurityGroupRequest(
    region_id='cn-beijing',
    vpc_id=vpc_id,
    security_group_name='llm-app-sg',
    description='大模型应用安全组'
)
sg_response = ecs_client.create_security_group(sg_request)
sg_id = sg_response.body.security_group_id
print(f"安全组创建成功: {sg_id}")

# 添加入方向规则
rules = [
    # Web 层：允许 HTTP/HTTPS
    {'port': '80/80', 'source_cidr': '0.0.0.0/0', 'description': 'HTTP'},
    {'port': '443/443', 'source_cidr': '0.0.0.0/0', 'description': 'HTTPS'},
    
    # 应用层：允许来自 Web 层的访问
    {'port': '8000/8000', 'source_cidr': '10.0.1.0/24', 'description': 'App API'},
    
    # 数据层：允许来自应用层的访问
    {'port': '3306/3306', 'source_cidr': '10.0.2.0/24', 'description': 'MySQL'},
    {'port': '6379/6379', 'source_cidr': '10.0.2.0/24', 'description': 'Redis'},
]

for rule in rules:
    auth_request = AuthorizeSecurityGroupRequest(
        region_id='cn-beijing',
        security_group_id=sg_id,
        ip_protocol='tcp',
        port_range=rule['port'],
        source_cidr_ip=rule['source_cidr'],
        description=rule['description']
    )
    ecs_client.authorize_security_group(auth_request)
    print(f"安全组规则添加: {rule['description']}")
```

### 私网连接百炼平台

默认情况下，百炼平台的 API 通过公网访问。对于有严格安全要求的场景，可以通过 VPC Endpoint 实现私网访问：

```python
from alibabacloud_privatelink20200415.client import Client
from alibabacloud_privatelink20200415.models import CreateVpcEndpointRequest

privatelink_client = Client(
    access_key_id=os.getenv('ALIBABA_CLOUD_ACCESS_KEY_ID'),
    access_key_secret=os.getenv('ALIBABA_CLOUD_ACCESS_KEY_SECRET')
)

# 创建 VPC Endpoint
endpoint_request = CreateVpcEndpointRequest(
    region_id='cn-beijing',
    vpc_id=vpc_id,
    service_name='com.aliyun.modelstudio',  # 百炼平台服务名称
    endpoint_name='modelstudio-endpoint',
    security_group_ids=[sg_id],
    zone_mappings=[
        {'zone_id': 'cn-beijing-a', 'v_switch_id': vswitch_ids[0]},
        {'zone_id': 'cn-beijing-b', 'v_switch_id': vswitch_ids[1]},
    ]
)
endpoint_response = privatelink_client.create_vpc_endpoint(endpoint_request)
endpoint_id = endpoint_response.body.endpoint_id
print(f"VPC Endpoint 创建成功: {endpoint_id}")

# 获取 Endpoint 域名
endpoint_dns = f"{endpoint_id}.cn-beijing.privatelink.aliyuncs.com"
print(f"私网访问域名: {endpoint_dns}")
```

**使用私网域名调用 API：**

```python
import dashscope

# 配置私网 Endpoint
dashscope.base_websocket_api_url = f"wss://{endpoint_dns}/api/v1"
dashscope.base_http_api_url = f"https://{endpoint_dns}/api/v1"

# 正常调用 API（流量走私网）
response = dashscope.Generation.call(
    model='qwen3.6-plus',
    prompt='你好',
    api_key=os.getenv('DASHSCOPE_API_KEY')
)
print(response.output.text)
```

---

## 2.4.2 API Gateway 与 WAF 防护

### API Gateway 的作用

API Gateway 是大模型应用的前置网关，提供以下能力：

- **统一入口**：所有 API 请求通过统一域名访问
- **认证鉴权**：验证用户身份和权限
- **限流熔断**：防止恶意攻击和过载
- **日志审计**：记录所有 API 调用
- **版本管理**：支持多版本 API 并存

### 快速入门

**步骤一：创建 API 分组**

```python
from alibabacloud_apigateway20160714.client import Client
from alibabacloud_apigateway20160714.models import CreateApiGroupRequest

apigw_client = Client(
    access_key_id=os.getenv('ALIBABA_CLOUD_ACCESS_KEY_ID'),
    access_key_secret=os.getenv('ALIBABA_CLOUD_ACCESS_KEY_SECRET')
)

# 创建 API 分组
group_request = CreateApiGroupRequest(
    group_name='llm-api-group',
    description='大模型 API 分组',
    traffic_limit=10000,  # QPS 限制
    billing_status='ENABLED'
)
group_response = apigw_client.create_api_group(group_request)
group_id = group_response.body.group_id
print(f"API 分组创建成功: {group_id}")
```

**步骤二：定义 API**

```python
from alibabacloud_apigateway20160714.models import CreateApiRequest

# 创建对话 API
api_request = CreateApiRequest(
    group_id=group_id,
    api_name='chat_completion',
    visibility='PRIVATE',  # 私有 API
    auth_type='APP',  # APP 认证
    request_config={
        'request_protocol': 'HTTPS',
        'request_method': 'POST',
        'request_path': '/v1/chat/completions',
        'body_format': 'FORM'
    },
    service_config={
        'service_protocol': 'HTTPS',
        'service_address': 'dashscope.aliyuncs.com',
        'service_path': '/api/v1/services/aigc/text-generation/generation',
        'service_method': 'POST'
    }
)
api_response = apigw_client.create_api(api_request)
api_id = api_response.body.api_id
print(f"API 创建成功: {api_id}")
```

**步骤三：配置限流策略**

```python
from alibabacloud_apigateway20160714.models import SetApiTrafficControlRequest

# 设置 API 限流
traffic_request = SetApiTrafficControlRequest(
    group_id=group_id,
    api_id=api_id,
    traffic_control_id='default',
    api_traffic_limit=100,  # 单 API QPS 限制
    user_traffic_limit=10,  # 单用户 QPS 限制
    app_traffic_limit=50  # 单应用 QPS 限制
)
apigw_client.set_api_traffic_control(traffic_request)
print("限流策略配置成功")
```

### WAF 防护

WAF（Web Application Firewall）用于防护常见的 Web 攻击，如 SQL 注入、XSS、CC 攻击等。

**配置 WAF 防护：**

```python
from alibabacloud_waf_openapi20190910.client import Client as WafClient
from alibabacloud_waf_openapi20190910.models import CreateDomainRequest

waf_client = WafClient(
    access_key_id=os.getenv('ALIBABA_CLOUD_ACCESS_KEY_ID'),
    access_key_secret=os.getenv('ALIBABA_CLOUD_ACCESS_KEY_SECRET')
)

# 添加域名到 WAF
domain_request = CreateDomainRequest(
    domain='api.llm-app.example.com',
    instance_id='waf-instance-xxx',
    protocols=['HTTPS'],
    https_ext_info={
        'cert_id': 'cert-xxx',  # SSL 证书 ID
        'force_redirect': True  # 强制 HTTPS
    }
)
waf_client.create_domain(domain_request)
print("域名已添加到 WAF")

# 配置防护规则
# 1. SQL 注入防护：启用
# 2. XSS 防护：启用
# 3. CC 防护：启用，阈值 100 次/分钟
# 4. Bot 管理：启用，拦截恶意爬虫
```

**WAF 防护效果：**

| 攻击类型 | 防护能力 | 误报率 |
|---------|---------|-------|
| SQL 注入 | 高 | <0.1% |
| XSS | 高 | <0.1% |
| CC 攻击 | 中 | 1-2% |
| Bot 攻击 | 中 | 2-5% |

**最佳实践：**

- 开启日志记录，定期分析攻击趋势
- 配置告警规则，及时发现异常流量
- 定期更新防护规则，适应新型攻击
- 对于误报，添加白名单而非关闭防护

---

## 2.4.3 密钥管理与访问控制

### RAM 访问控制

RAM（Resource Access Management）是阿里云的身份管理服务，用于控制用户对云资源的访问权限。

**最小权限原则：**

为不同的角色分配最小必要权限：

```json
{
  "Version": "1",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "dashscope:GenerateText",
        "dashscope:GenerateEmbedding"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Deny",
      "Action": [
        "dashscope:CreateModel",
        "dashscope:DeleteModel",
        "dashscope:UpdateApiKey"
      ],
      "Resource": "*"
    }
  ]
}
```

**创建 RAM 用户并授权：**

```python
from alibabacloud_ram20150501.client import Client as RamClient
from alibabacloud_ram20150501.models import CreateUserRequest, AttachPolicyToUserRequest

ram_client = RamClient(
    access_key_id=os.getenv('ALIBABA_CLOUD_ACCESS_KEY_ID'),
    access_key_secret=os.getenv('ALIBABA_CLOUD_ACCESS_KEY_SECRET')
)

# 创建 RAM 用户
user_request = CreateUserRequest(
    user_name='llm-app-service',
    display_name='大模型应用服务账号',
    comments='用于大模型 API 调用的服务账号'
)
ram_client.create_user(user_request)
print("RAM 用户创建成功")

# 附加策略
policy_request = AttachPolicyToUserRequest(
    user_name='llm-app-service',
    policy_name='AliyunDashScopeReadOnlyAccess',  # 只读权限
    policy_type='System'
)
ram_client.attach_policy_to_user(policy_request)
print("策略附加成功")

# 创建 AccessKey
from alibabacloud_ram20150501.models import CreateAccessKeyRequest
ak_request = CreateAccessKeyRequest(user_name='llm-app-service')
ak_response = ram_client.create_access_key(ak_request)
print(f"AccessKey ID: {ak_response.body.access_key.access_key_id}")
print(f"AccessKey Secret: {ak_response.body.access_key.access_key_secret}")
```

### 密钥管理服务 KMS

KMS（Key Management Service）用于安全存储和管理敏感凭证，如 API Key、数据库密码等。

**为什么需要 KMS：**

- **安全存储**：密钥加密存储，即使数据库泄露也无法直接读取
- **访问审计**：记录所有密钥访问操作
- **自动轮换**：支持定期自动轮换密钥
- **细粒度权限**：控制谁可以访问哪些密钥

**快速入门：**

```python
from alibabacloud_kms20160120.client import Client as KmsClient
from alibabacloud_kms20160120.models import CreateKeyRequest, PutSecretValueRequest, GetSecretValueRequest

kms_client = KmsClient(
    access_key_id=os.getenv('ALIBABA_CLOUD_ACCESS_KEY_ID'),
    access_key_secret=os.getenv('ALIBABA_CLOUD_ACCESS_KEY_SECRET')
)

# 创建密钥
key_request = CreateKeyRequest(
    description='DashScope API Key',
    key_spec='AES_256',
    protection_level='SOFTWARE'
)
key_response = kms_client.create_key(key_request)
key_id = key_response.body.key_metadata.key_id
print(f"密钥创建成功: {key_id}")

# 存储密钥值
secret_request = PutSecretValueRequest(
    secret_name='dashscope-api-key',
    secret_data=os.getenv('DASHSCOPE_API_KEY'),
    version_id='v1'
)
kms_client.put_secret_value(secret_request)
print("密钥值存储成功")

# 读取密钥值
def get_api_key():
    """从 KMS 获取 API Key"""
    secret_response = kms_client.get_secret_value(
        GetSecretValueRequest(secret_name='dashscope-api-key')
    )
    return secret_response.body.secret_data

# 使用密钥
api_key = get_api_key()
response = dashscope.Generation.call(
    model='qwen3.6-plus',
    prompt='你好',
    api_key=api_key
)
```

**最佳实践：**

1. **不要硬编码密钥**：永远不要在代码中硬编码 API Key 或密码
2. **使用环境变量或 KMS**：通过环境变量或 KMS 动态获取密钥
3. **定期轮换密钥**：建议每 90 天轮换一次 API Key
4. **最小权限**：为每个服务分配独立的 RAM 用户和最小权限
5. **启用 MFA**：对管理员账号启用多因素认证

---

## 2.4.4 数据安全与加密

### 传输加密

所有数据传输必须使用 TLS 1.2 或更高版本：

```python
import ssl
import requests

# 强制使用 TLS 1.2+
session = requests.Session()
session.verify = True  # 验证 SSL 证书

# 禁用不安全的协议
context = ssl.create_default_context()
context.check_hostname = True
context.verify_mode = ssl.CERT_REQUIRED
context.minimum_version = ssl.TLSVersion.TLSv1_2

response = session.get(
    'https://dashscope.aliyuncs.com/api/v1',
    verify=True
)
```

### 存储加密

**OSS 服务端加密：**

```python
import oss2

# 创建启用服务端加密的 Bucket
bucket_config = oss2.models.ServerSideEncryptionRule()
bucket_config.sse_algorithm = oss2.SERVER_SIDE_ENCRYPTION_AES256  # AES-256 加密
bucket.put_bucket_encryption(bucket_config)
print("OSS 服务端加密已启用")
```

**RDS 透明数据加密（TDE）：**

```sql
-- 启用 TDE
ALTER INSTANCE ENABLE TDE;

-- 为特定表空间启用加密
CREATE TABLESPACE encrypted_ts
ADD DATAFILE 'encrypted_ts.ibd'
ENCRYPTION = 'Y';
```

### 数据脱敏

对于敏感数据（如用户手机号、身份证号），在存储和日志中进行脱敏：

```python
import re

def mask_phone(phone: str) -> str:
    """手机号脱敏：138****1234"""
    if len(phone) == 11:
        return phone[:3] + '****' + phone[7:]
    return phone

def mask_id_card(id_card: str) -> str:
    """身份证脱敏：110101********1234"""
    if len(id_card) == 18:
        return id_card[:6] + '********' + id_card[14:]
    return id_card

def mask_email(email: str) -> str:
    """邮箱脱敏：us***@example.com"""
    if '@' in email:
        local, domain = email.split('@', 1)
        if len(local) > 2:
            masked_local = local[:2] + '***'
        else:
            masked_local = '***'
        return f"{masked_local}@{domain}"
    return email

# 使用示例
print(mask_phone('13812345678'))  # 138****5678
print(mask_id_card('110101199001011234'))  # 110101********1234
print(mask_email('user@example.com'))  # us***@example.com
```

---

## 2.4.5 审计与监控

### 操作审计 ActionTrail

ActionTrail 记录所有阿里云 API 调用，用于安全审计和问题追溯。

**查询审计日志：**

```python
from alibabacloud_actiontrail20200706.client import Client as ActionTrailClient
from alibabacloud_actiontrail20200706.models import LookupEventsRequest

actiontrail_client = ActionTrailClient(
    access_key_id=os.getenv('ALIBABA_CLOUD_ACCESS_KEY_ID'),
    access_key_secret=os.getenv('ALIBABA_CLOUD_ACCESS_KEY_SECRET')
)

# 查询过去 24 小时的 DashScope API 调用
import datetime
end_time = datetime.datetime.utcnow()
start_time = end_time - datetime.timedelta(hours=24)

lookup_request = LookupEventsRequest(
    start_time=start_time.isoformat() + 'Z',
    end_time=end_time.isoformat() + 'Z',
    event_name=['GenerateText', 'GenerateEmbedding'],
    max_results=100
)
response = actiontrail_client.lookup_events(lookup_request)

for event in response.body.events:
    print(f"[{event.event_time}] {event.user_identity.principal_id} - {event.event_name}")
```

### 日志服务 SLS

SLS（Simple Log Service）用于收集和分析应用日志。

**配置日志采集：**

```python
from alibabacloud_sls20201230.client import Client as SlsClient
from alibabacloud_sls20201230.models import PostLogStoreLogsRequest

sls_client = SlsClient(
    access_key_id=os.getenv('ALIBABA_CLOUD_ACCESS_KEY_ID'),
    access_key_secret=os.getenv('ALIBABA_CLOUD_ACCESS_KEY_SECRET')
)

# 发送日志
log_item = {
    'time': int(time.time()),
    'contents': [
        ('level', 'INFO'),
        ('message', 'API 调用成功'),
        ('model', 'qwen3.6-plus'),
        ('input_tokens', '100'),
        ('output_tokens', '50'),
        ('latency_ms', '250'),
        ('user_id', 'user_12345')
    ]
}

log_group = {
    'logs': [log_item]
}

sls_client.post_log_store_logs(
    project='llm-app-logs',
    logstore='api-calls',
    log_group=log_group
)
```

**日志查询与分析：**

```sql
-- 查询过去 1 小时的 API 调用统计
SELECT 
    model,
    COUNT(*) as call_count,
    AVG(latency_ms) as avg_latency,
    SUM(input_tokens + output_tokens) as total_tokens
FROM api_calls
WHERE __time__ >= now() - 3600
GROUP BY model
ORDER BY call_count DESC

-- 查询错误率高的用户
SELECT 
    user_id,
    COUNT(*) as total_calls,
    SUM(CASE WHEN status_code >= 400 THEN 1 ELSE 0 END) as error_count,
    ROUND(SUM(CASE WHEN status_code >= 400 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as error_rate
FROM api_calls
WHERE __time__ >= now() - 86400
GROUP BY user_id
HAVING error_rate > 5
ORDER BY error_rate DESC
```

---

## 本节小结

本节系统介绍了大模型应用的网络与安全架构：

1. **VPC 私有网络**：通过分层架构和安全组实现网络隔离和访问控制，通过 VPC Endpoint 实现百炼平台私网访问

2. **API Gateway 与 WAF**：提供统一入口、认证鉴权、限流熔断和 Web 攻击防护

3. **密钥管理**：通过 RAM 实现最小权限控制，通过 KMS 安全存储敏感凭证

4. **数据加密**：传输层使用 TLS 1.2+，存储层使用 OSS 服务端加密和 RDS TDE

5. **审计与监控**：通过 ActionTrail 记录操作审计，通过 SLS 收集和分析应用日志

技术决策者在设计安全架构时，应遵循"纵深防御"的原则，在网络层、应用层、数据层都建立防护措施，而不是依赖单一的安全机制。同时，安全措施不应影响用户体验，需要在安全性和可用性之间取得平衡。

---

## 延伸阅读

1. **官方文档**
   - [VPC 产品文档](https://help.aliyun.com/zh/vpc/)
   - [API Gateway 产品文档](https://help.aliyun.com/zh/api-gateway/)
   - [RAM 产品文档](https://help.aliyun.com/zh/ram/)
   - [KMS 产品文档](https://help.aliyun.com/zh/kms/)
   - [ActionTrail 产品文档](https://help.aliyun.com/zh/actiontrail/)
   - [SLS 产品文档](https://help.aliyun.com/zh/sls/)

2. **安全最佳实践**
   - [阿里云安全白皮书](https://www.aliyun.com/security/whitepaper)
   - [金融行业云上安全合规指南](https://help.aliyun.com/zh/security/compliance)

3. **架构案例**
   - 某银行智能客服系统安全架构设计
   - 某医疗机构数据隐私保护方案
   - 某电商平台 API 安全防护实践
