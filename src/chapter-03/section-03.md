# 3.3 限流熔断与版本管理

## 3.3.1 客户端限流策略

百炼平台对不同用户等级有明确的 QPS 限制。为了防止因突发流量导致服务不可用，建议在客户端实现令牌桶算法：

```python
import time
from threading import Lock

class RateLimiter:
    def __init__(self, rate, capacity):
        self.rate = rate
        self.capacity = capacity
        self.tokens = capacity
        self.last_update = time.time()
        self.lock = Lock()
    
    def acquire(self):
        with self.lock:
            now = time.time()
            elapsed = now - self.last_update
            self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
            self.last_update = now
            
            if self.tokens >= 1:
                self.tokens -= 1
                return True
            return False
```

## 3.3.2 熔断与重试机制

当 API 出现连续失败时，应触发熔断以保护系统资源：

*   **熔断器状态**：关闭（正常）、打开（快速失败）、半开（尝试恢复）。
*   **指数退避重试**：针对网络抖动或临时性错误，采用 `base_delay * (2 ^ attempt)` 的策略进行重试。

## 3.3.3 API 版本管理

大模型能力迭代迅速，API 演进不可避免。建议采用语义化版本号（Semantic Versioning）：

*   **并行运行期**：新旧版本同时可用至少 3 个月。
*   **废弃通知**：在 HTTP Response Header 中添加 `Deprecation` 字段。
*   **迁移指南**：提供详细的参数映射表和自动化迁移脚本。

> **本章小结**：规范的 API 设计、安全的认证机制以及完善的弹性防护，是构建企业级大模型应用的基石。技术决策者应从第一天起就建立这些工程化规范。
