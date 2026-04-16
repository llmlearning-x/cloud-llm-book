# 3.2 认证鉴权与多语言 SDK

## 3.2.1 API Key 管理与安全

阿里云百炼平台采用 API Key 作为主要的认证方式。技术决策者必须建立严格的密钥管理规范：

**安全最佳实践：**
*   **环境变量存储**：严禁在代码中硬编码 API Key，应通过 `os.getenv("DASHSCOPE_API_KEY")` 获取。
*   **RAM 用户隔离**：为每个应用或环境（开发/测试/生产）创建独立的 RAM 用户并授予最小权限。
*   **定期轮换**：建议每季度更换一次 API Key，并启用使用监控告警。

## 3.2.2 Python SDK 实战

Python 是大模型应用开发的首选语言。DashScope SDK 提供了简洁的调用接口：

```python
import os
from http import HTTPStatus
import dashscope
from dashscope import Generation

dashscope.api_key = os.getenv("DASHSCOPE_API_KEY")

response = Generation.call(
    model='qwen3.6-plus',
    messages=[{'role': 'user', 'content': '你好'}],
    temperature=0.7,
    max_tokens=1024
)

if response.status_code == HTTPStatus.OK:
    print(f"回复：{response.output.choices[0].message.content}")
else:
    print(f"请求失败：{response.code} - {response.message}")
```

## 3.2.3 Java 与 Node.js SDK

对于企业级后端系统，Java 和 Node.js 也是常用的集成语言：

**Java (Maven):**
```xml
<dependency>
    <groupId>com.alibaba</groupId>
    <artifactId>dashscope-sdk-java</artifactId>
    <version>2.15.0</version>
</dependency>
```

**Node.js:**
```javascript
const DashScope = require('@alicloud/dashscope');
const client = new DashScope({ accessKeyId: process.env.DASHSCOPE_API_KEY });

async function chat() {
  const response = await client.invoke('qwen3.6-plus', {
    messages: [{ role: 'user', content: '你好' }]
  });
  console.log(response.output.choices[0].message.content);
}
```

> **技术决策点**：在多语言团队中，建议封装统一的内部网关服务（Gateway），由网关统一处理认证、限流和日志记录，各业务线只需通过内网调用网关即可，从而降低 SDK 维护成本。
