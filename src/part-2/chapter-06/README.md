# 第6章：DashScope API 快速入门

> 本章是 DashScope API 的实战指南，从环境准备到第一个 AI 程序，再到错误处理和调试技巧，带你快速上手阿里云的大模型 API 服务。

## 6.1 环境准备

### 6.1.1 Python 环境要求

DashScope SDK 需要以下环境：

- Python 3.8 或更高版本
- 推荐使用虚拟环境管理依赖

```bash
# 检查 Python 版本
python --version
# Python 3.10.12

# 创建虚拟环境（推荐）
python -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate   # Windows

# 升级 pip
pip install --upgrade pip
```

### 6.1.2 安装 DashScope SDK

```bash
# 安装最新版 DashScope SDK
pip install dashscope

# 如果需要流式输出支持
pip install dashscope[sseclient]

# 验证安装
python -c "import dashscope; print(dashscope.__version__)"
```

### 6.1.3 环境变量配置

```bash
# 方式一：环境变量（推荐）
export DASHSCOPE_API_KEY="sk-xxxxxxxxxxxxxxxxxxxxxxxx"

# 方式二：代码中设置
import dashscope
dashscope.api_key = "sk-xxxxxxxxxxxxxxxxxxxxxxxx"

# 方式三：配置文件
# ~/.dashscope/config.json
{
    "api_key": "sk-xxxxxxxxxxxxxxxxxxxxxxxx"
}
```

> 💡 **最佳实践**：将 API Key 存储在环境变量中，避免硬编码在代码里。

### 6.1.4 IDE 配置

如果你使用 VS Code 或 PyCharm，确保：

1. 选择了正确的 Python 解释器（虚拟环境）
2. 安装了 Python 扩展
3. 配置了代码补全和类型提示

```json
// VS Code: .vscode/settings.json
{
    "python.defaultInterpreterPath": "./venv/bin/python",
    "python.linting.enabled": true,
    "python.formatting.provider": "black"
}
```

## 6.2 第一个 AI 程序

### 6.2.1 最简示例

让我们从一个最简单的例子开始：

```python
#!/usr/bin/env python3
"""
dashscope-quickstart.py
DashScope API 快速入门示例
"""

from dashscope import Generation

def simple_chat():
    """最简单的对话示例"""
    response = Generation.call(
        model="qwen-turbo",
        prompt="你好，请用一句话介绍一下阿里云。"
    )
    
    if response.status_code == 200:
        print(response.output.text)
    else:
        print(f"请求失败: {response.code} - {response.message}")

if __name__ == "__main__":
    simple_chat()
```

运行：

```bash
python dashscope-quickstart.py
```

输出：

```
阿里云（Alibaba Cloud）是阿里巴巴集团旗下的云计算品牌，为全球用户提供计算、数据库、存储、网络等基础设施服务以及大数据、人工智能等解决方案。
```

### 6.2.2 使用消息格式

更规范的对话使用消息（Messages）格式：

```python
from dashscope import Generation
from dashscope.common import Message

def chat_with_messages():
    """使用标准消息格式的对话"""
    
    messages = [
        Message(
            role="system",
            content="你是一个专业的Python讲师，用简洁易懂的语言解释概念。"
        ),
        Message(
            role="user",
            content="什么是装饰器？"
        )
    ]
    
    response = Generation.call(
        model="qwen-turbo",
        messages=messages,
        temperature=0.7,
        top_p=0.8,
        result_format="message"  # 返回格式
    )
    
    if response.status_code == 200:
        assistant_message = response.output.choices[0].message
        print(f"角色: {assistant_message.role}")
        print(f"回复: {assistant_message.content}")
    else:
        print(f"错误: {response.message}")

if __name__ == "__main__":
    chat_with_messages()
```

### 6.2.3 完整项目结构

一个规范的 DashScope 项目通常有如下结构：

```
my-ai-app/
├── config.py          # 配置管理
├── api_client.py      # API 调用封装
├── prompts.py         # Prompt 模板
├── main.py            # 程序入口
├── requirements.txt   # 依赖列表
└── tests/             # 测试目录
    └── test_api.py
```

**config.py**：配置管理

```python
"""
配置管理：集中管理 API 配置和参数
"""
import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class ModelConfig:
    """模型配置"""
    name: str
    temperature: float = 0.7
    top_p: float = 0.8
    max_tokens: int = 2000
    presence_penalty: float = 0.0
    frequency_penalty: float = 0.0

@dataclass
class AppConfig:
    """应用配置"""
    api_key: str
    default_model: str = "qwen-turbo"
    timeout: int = 60
    max_retries: int = 3
    
    @classmethod
    def from_env(cls):
        """从环境变量加载配置"""
        api_key = os.getenv("DASHSCOPE_API_KEY")
        if not api_key:
            raise ValueError("未设置 DASHSCOPE_API_KEY 环境变量")
        return cls(api_key=api_key)

# 预定义的模型配置
MODELS = {
    "fast": ModelConfig("qwen-turbo", temperature=0.7),
    "balanced": ModelConfig("qwen-plus", temperature=0.7),
    "quality": ModelConfig("qwen-max", temperature=0.5),
}

# 全局配置实例
config = AppConfig.from_env()
```

**api_client.py**：API 调用封装

```python
"""
DashScope API 客户端封装
"""
import dashscope
from dashscope import Generation
from dashscope.common import Message
from typing import List, Dict, Optional, Union
import time

class DashScopeClient:
    """DashScope API 客户端封装类"""
    
    def __init__(self, api_key: str, default_model: str = "qwen-turbo"):
        dashscope.api_key = api_key
        self.default_model = default_model
    
    def chat(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> Dict:
        """
        对话生成
        
        Args:
            prompt: 用户输入
            system_prompt: 系统提示
            model: 模型名称，默认使用配置
            temperature: 随机性控制
            max_tokens: 最大生成token数
            **kwargs: 其他参数
        
        Returns:
            Dict: 包含 status、message、usage 等信息
        """
        # 构建消息列表
        messages = []
        if system_prompt:
            messages.append(Message(role="system", content=system_prompt))
        messages.append(Message(role="user", content=prompt))
        
        # 调用 API
        response = Generation.call(
            model=model or self.default_model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            result_format="message",
            **kwargs
        )
        
        return self._parse_response(response)
    
    def chat_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        **kwargs
    ):
        """
        流式对话生成
        
        Yields:
            str: 生成的文本片段
        """
        messages = []
        if system_prompt:
            messages.append(Message(role="system", content=system_prompt))
        messages.append(Message(role="user", content=prompt))
        
        response = Generation.call(
            model=model or self.default_model,
            messages=messages,
            stream=True,
            incremental_output=True,
            result_format="message",
            **kwargs
        )
        
        for resp in response:
            if resp.status_code == 200:
                content = resp.output.choices[0].delta.content
                if content:
                    yield content
            else:
                raise Exception(f"流式输出错误: {resp.message}")
    
    def chat_with_retry(
        self,
        prompt: str,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        **kwargs
    ) -> Dict:
        """
        带重试的对话
        
        Args:
            prompt: 用户输入
            max_retries: 最大重试次数
            retry_delay: 重试间隔（秒）
            **kwargs: 传递给 chat 的其他参数
        """
        for attempt in range(max_retries):
            try:
                result = self.chat(prompt, **kwargs)
                if result["status"] == "success":
                    return result
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                print(f"请求失败，{retry_delay}秒后重试... ({attempt + 1}/{max_retries})")
                time.sleep(retry_delay)
        
        raise Exception("达到最大重试次数")
    
    def _parse_response(self, response) -> Dict:
        """解析 API 响应"""
        if response.status_code == 200:
            choice = response.output.choices[0].message
            usage = getattr(response.output, 'usage', None)
            
            return {
                "status": "success",
                "message": choice.content,
                "model": response.request.model,
                "usage": {
                    "input_tokens": getattr(usage, 'input_tokens', 0),
                    "output_tokens": getattr(usage, 'output_tokens', 0),
                    "total_tokens": getattr(usage, 'total_tokens', 0),
                } if usage else None,
                "request_id": response.request_id
            }
        else:
            return {
                "status": "error",
                "error_code": response.code,
                "error_message": response.message,
                "request_id": response.request_id
            }


# 便捷函数
def get_client() -> DashScopeClient:
    """获取客户端实例（从环境变量）"""
    from config import config
    return DashScopeClient(
        api_key=config.api_key,
        default_model=config.default_model
    )
```

**main.py**：程序入口

```python
#!/usr/bin/env python3
"""
AI 助手主程序
"""
from api_client import get_client
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

console = Console()

def main():
    """主程序"""
    console.print(Panel.fit(
        "[bold cyan]AI 助手[/bold cyan] - 基于 DashScope API\n"
        "输入问题，AI 将为你解答\n"
        "输入 [bold]quit[/bold] 或 [bold]exit[/bold] 退出"
    ))
    
    client = get_client()
    
    while True:
        try:
            user_input = console.input("\n[bold green]你:[/bold green] ")
            
            if user_input.lower() in ["quit", "exit", "q"]:
                console.print("[yellow]再见！[/yellow]")
                break
            
            if not user_input.strip():
                continue
            
            console.print("[bold blue]AI:[/bold blue] ", end="")
            
            # 流式输出
            response_text = ""
            for chunk in client.chat_stream(user_input):
                print(chunk, end="", flush=True)
                response_text += chunk
            
            # 打印使用信息
            print("\n")
            
        except KeyboardInterrupt:
            console.print("\n[yellow]已退出[/yellow]")
            break
        except Exception as e:
            console.print(f"\n[bold red]错误:[/bold red] {e}")

if __name__ == "__main__":
    main()
```

**requirements.txt**：

```
dashscope>=1.14.0
rich>=13.0.0
python-dotenv>=1.0.0
```

## 6.3 常见参数详解

### 6.3.1 生成参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `model` | string | 必填 | 模型名称 |
| `prompt` | string | 必填 | 输入提示（单轮） |
| `messages` | list | - | 对话消息列表 |
| `temperature` | float | 0.7 | 随机性（0-1） |
| `top_p` | float | 0.8 | 核采样 |
| `top_k` | int | - | Top-K 采样 |
| `max_tokens` | int | - | 最大生成token数 |
| `stream` | bool | False | 是否流式输出 |
| `result_format` | string | "message" | 输出格式 |

### 6.3.2 temperature 与 top_p

```python
def demonstrate_temperature():
    """
    演示 temperature 对输出的影响
    """
    client = get_client()
    prompt = "给我5个科幻小说标题"
    
    print("=== Temperature = 0.0（最确定）===")
    response = client.chat(prompt, model="qwen-turbo", temperature=0.0)
    print(response["message"])
    
    print("\n=== Temperature = 0.7（平衡）===")
    response = client.chat(prompt, model="qwen-turbo", temperature=0.7)
    print(response["message"])
    
    print("\n=== Temperature = 1.5（高随机性）===")
    response = client.chat(prompt, model="qwen-turbo", temperature=1.5)
    print(response["message"])

def demonstrate_top_p():
    """
    演示 top_p 对输出的影响
    top_p 越小，选择范围越窄，越确定
    """
    client = get_client()
    prompt = "用一句话描述人工智能"
    
    print("=== Top-P = 0.1（保守）===")
    response = client.chat(prompt, top_p=0.1)
    print(response["message"])
    
    print("\n=== Top-P = 0.9（多样）===")
    response = client.chat(prompt, top_p=0.9)
    print(response["message"])
```

### 6.3.3 控制生成长度

```python
def control_output_length():
    """
    演示如何控制生成长度
    """
    client = get_client()
    prompt = "介绍一下云计算"
    
    print("=== 短回答 (max_tokens=50) ===")
    response = client.chat(prompt, max_tokens=50)
    print(response["message"])
    print(f"实际使用 tokens: {response['usage']['output_tokens']}")
    
    print("\n=== 中等回答 (max_tokens=200) ===")
    response = client.chat(prompt, max_tokens=200)
    print(response["message"])
    print(f"实际使用 tokens: {response['usage']['output_tokens']}")
```

## 6.4 错误处理与调试

### 6.4.1 常见错误码

| 错误码 | 含义 | 解决方案 |
|--------|------|----------|
| `InvalidApiKey` | API Key 无效 | 检查 Key 是否正确 |
| `QuotaExceeded` | 配额用尽 | 购买更多配额或等待重置 |
| `RateLimitExceeded` | 请求过于频繁 | 添加重试逻辑或降低QPS |
| `ParameterRequired` | 缺少必需参数 | 检查 API 文档 |
| `ModelNotSupported` | 模型不支持 | 使用支持的模型 |
| `InvalidParameter` | 参数值无效 | 检查参数范围 |
| `ServerError` | 服务器错误 | 重试或联系支持 |

### 6.4.2 错误处理模板

```python
from dashscope import Generation
from dashscope.common.error import (
    AuthenticationError,
    InvalidParameter,
    RequestFailedException
)
from typing import Optional

class DashScopeError(Exception):
    """DashScope 异常基类"""
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(f"[{code}] {message}")

def robust_chat(prompt: str) -> Optional[str]:
    """
    带完整错误处理的对话函数
    """
    try:
        response = Generation.call(
            model="qwen-turbo",
            messages=[{"role": "user", "content": prompt}],
            result_format="message"
        )
        
        if response.status_code == 200:
            return response.output.choices[0].message.content
        else:
            # 根据错误码处理
            error_map = {
                "InvalidApiKey": "API Key 无效，请检查配置",
                "QuotaExceeded": "配额已用尽，请购买更多配额",
                "RateLimitExceeded": "请求过于频繁，请稍后重试",
                "ModelNotSupported": "该模型不可用",
            }
            message = error_map.get(
                response.code, 
                f"请求失败: {response.code} - {response.message}"
            )
            print(f"❌ {message}")
            return None
            
    except AuthenticationError as e:
        print(f"❌ 认证失败: {e}")
        return None
    except InvalidParameter as e:
        print(f"❌ 参数错误: {e}")
        return None
    except RequestFailedException as e:
        print(f"❌ 请求失败 ({e.status_code}): {e.message}")
        if e.status_code == 429:
            print("   建议：添加重试延迟或降低调用频率")
        return None
    except Exception as e:
        print(f"❌ 未知错误: {e}")
        return None

def chat_with_retry(
    prompt: str,
    max_retries: int = 3,
    initial_delay: float = 1.0
) -> Optional[str]:
    """
    带指数退避重试的对话
    """
    import time
    
    for attempt in range(max_retries):
        result = robust_chat(prompt)
        
        if result is not None:
            return result
        
        if attempt < max_retries - 1:
            delay = initial_delay * (2 ** attempt)  # 指数退避
            print(f"⏳ {delay}秒后重试... ({attempt + 1}/{max_retries})")
            time.sleep(delay)
    
    print("❌ 达到最大重试次数")
    return None
```

### 6.4.3 调试技巧

**启用详细日志**：

```python
import logging

# 启用请求日志
logging.basicConfig(level=logging.DEBUG)
dashscope.logger.setLevel(logging.DEBUG)

# 自定义日志格式
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
```

**打印完整响应**：

```python
def debug_response():
    """打印 API 完整响应，用于调试"""
    response = Generation.call(
        model="qwen-turbo",
        prompt="你好",
        result_format="message"
    )
    
    print("=== 响应对象 ===")
    print(f"状态码: {response.status_code}")
    print(f"请求ID: {response.request_id}")
    print(f"模型: {response.request.model}")
    print(f"Code: {response.code}")
    print(f"Message: {response.message}")
    print(f"Output: {response.output}")
```

**网络调试**：

```python
import requests

# 使用 requests 直接调用，便于调试
def raw_api_call(prompt: str):
    """直接使用 requests 调用 API"""
    import os
    
    url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
    headers = {
        "Authorization": f"Bearer {os.getenv('DASHSCOPE_API_KEY')}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "qwen-turbo",
        "input": {
            "prompt": prompt
        },
        "parameters": {
            "temperature": 0.7
        }
    }
    
    response = requests.post(url, json=payload, headers=headers)
    print(f"HTTP Status: {response.status_code}")
    print(f"Response: {response.json()}")
```

## 6.5 实际应用示例

### 6.5.1 文本摘要

```python
from api_client import get_client

def summarize_text(text: str, max_length: int = 100) -> str:
    """
    文本摘要
    """
    client = get_client()
    
    prompt = f"""请帮我将以下文章压缩成一段不超过{max_length}字的中文摘要：

{text}

摘要："""
    
    result = client.chat(prompt)
    return result["message"]

# 使用示例
article = """
2024年人工智能领域取得了重大突破。OpenAI发布了新一代GPT模型，在多项基准测试中创下新纪录。
与此同时，开源社区也迎来了Llama 3和Qwen 2等重量级模型。阿里云通义千问系列持续迭代，
最新版本在中文理解和代码生成方面表现突出。多模态成为趋势，GPT-4V、Gemini Pro等视觉语言模型
相继问世，推动了AI应用的新一轮创新。
"""

summary = summarize_text(article)
print(f"原文长度: {len(article)} 字")
print(f"摘要: {summary}")
```

### 6.5.2 翻译助手

```python
from api_client import get_client
from typing import Literal

def translate(
    text: str,
    target_lang: Literal["中文", "英文", "日文", "韩文", "法文", "德文"],
    source_lang: str = "自动检测"
) -> str:
    """
    多语言翻译
    """
    client = get_client()
    
    if source_lang == "自动检测":
        prompt = f"""请将以下内容翻译成{target_lang}：

{text}

只输出翻译结果，不要解释。"""
    else:
        prompt = f"""请将以下{source_lang}内容翻译成{target_lang}：

{text}

只输出翻译结果，不要解释。"""
    
    result = client.chat(prompt)
    return result["message"]

# 使用示例
english_text = "Artificial Intelligence is transforming the world."
chinese = translate(english_text, "中文")
print(f"英文: {english_text}")
print(f"中文: {chinese}")
```

### 6.5.3 代码审查

```python
from api_client import get_client

def review_code(code: str, language: str = "Python") -> str:
    """
    代码审查与建议
    """
    client = get_client()
    
    prompt = f"""请审查以下{language}代码，找出潜在问题并给出改进建议：

```{language.lower()}
{code}
```

请从以下角度审查：
1. 正确性：逻辑错误、边界条件
2. 安全性：潜在的安全漏洞
3. 性能：效率问题
4. 可维护性：代码风格、可读性
5. 最佳实践：是否符合语言规范

以结构化的方式输出审查结果。"""
    
    result = client.chat(prompt)
    return result["message"]

# 使用示例
code = """
def calculate_average(numbers):
    total = sum(numbers)
    return total / len(numbers)
"""

review = review_code(code)
print(review)
```

### 6.5.4 校园助手

```python
from api_client import get_client

class CampusAssistant:
    """校园问答助手"""
    
    SYSTEM_PROMPT = """你是一个热心的校园助手，名为"小智"。
你的职责是帮助学生解决校园生活中的各种问题。

你可以帮助的领域包括：
- 教务信息：选课、转专业、考试安排等
- 生活服务：食堂、宿舍、校园卡等
- 校园设施：图书馆、体育馆、自习室等
- 学生活动：社团、讲座、比赛等
- 技术问题：校园网、VPN、邮箱等

请用友好、耐心、专业的态度回答问题。
如果不确定答案，请诚实地说明并建议学生咨询相关部门。"""
    
    def __init__(self):
        self.client = get_client()
        self.conversation_history = []
    
    def ask(self, question: str) -> str:
        """提问"""
        messages = [{"role": "system", "content": self.SYSTEM_PROMPT}]
        messages.extend(self.conversation_history)
        messages.append({"role": "user", "content": question})
        
        response = self.client.chat(
            prompt="",  # 空prompt，因为我们用messages
            system_prompt=self.SYSTEM_PROMPT,
        )
        
        # 这里简化处理，实际应该用messages参数
        result = self.client.chat(
            f"{self.SYSTEM_PROMPT}\n\n用户问题：{question}"
        )
        
        answer = result["message"]
        
        # 保存对话历史
        self.conversation_history.append({"role": "user", "content": question})
        self.conversation_history.append({"role": "assistant", "content": answer})
        
        return answer
    
    def reset(self):
        """重置对话历史"""
        self.conversation_history = []

# 使用示例
assistant = CampusAssistant()

print("=== 校园助手 ===")
questions = [
    "图书馆开放时间是几点？",
    "如何申请转专业？",
    "校园无线网络怎么连接？"
]

for q in questions:
    print(f"\n学生: {q}")
    answer = assistant.ask(q)
    print(f"助手: {answer}")
```

## 6.6 成本优化建议

### 6.6.1 选择合适的模型

```python
def model_selection_guide():
    """
    模型选择指南
    """
    scenarios = [
        {
            "场景": "简单问答、客服机器人",
            "推荐模型": "qwen-turbo",
            "理由": "速度快、成本低、效果好"
        },
        {
            "场景": "内容创作、复杂推理",
            "推荐模型": "qwen-plus",
            "理由": "质量更高、上下文更长"
        },
        {
            "场景": "高精度要求的任务",
            "推荐模型": "qwen-max",
            "理由": "最高质量"
        }
    ]
    
    print("模型选择指南：")
    for s in scenarios:
        print(f"  {s['场景']} → {s['推荐模型']} ({s['理由']})")
```

### 6.6.2 减少 token 消耗

```python
def optimize_prompts():
    """Prompt 优化技巧"""
    
    # ❌ 冗余的提示词
    bad_prompt = """
    请你作为一个专业的人工智能助手，仔细地、认真地、详细地阅读下面的问题，
    然后用你的专业知识给出准确、全面、有条理的回答。
    
    问题：什么是Python？
    
    请回答：
    """
    
    # ✅ 简洁的提示词
    good_prompt = "什么是Python？请用一句话解释。"
    
    # 结论：去掉冗余表述，节省 token
    print(f"冗余提示词 token 数: ~{len(bad_prompt)}")
    print(f"简洁提示词 token 数: ~{len(good_prompt)}")
    print("节省约 70% 的输入 token")
```

### 6.6.3 缓存与批处理

```python
import hashlib
from functools import lru_cache

class CachedClient:
    """带缓存的 API 客户端"""
    
    def __init__(self):
        from api_client import get_client
        self.client = get_client()
        self.cache = {}
        self.cache_hits = 0
    
    def chat_with_cache(self, prompt: str, ttl: int = 3600) -> str:
        """
        带缓存的对话，相同问题直接返回缓存结果
        ttl: 缓存有效期（秒）
        """
        # 生成缓存 key
        cache_key = hashlib.md5(prompt.encode()).hexdigest()
        
        import time
        current_time = time.time()
        
        if cache_key in self.cache:
            cached_time, cached_result = self.cache[cache_key]
            if current_time - cached_time < ttl:
                self.cache_hits += 1
                print(f"🔍 缓存命中 ({self.cache_hits})")
                return cached_result
        
        # 调用 API
        result = self.client.chat(prompt)
        self.cache[cache_key] = (current_time, result)
        
        return result
    
    def batch_chat(self, prompts: list) -> list:
        """批量处理（实际由业务层实现）"""
        results = []
        for prompt in prompts:
            results.append(self.chat_with_cache(prompt))
        return results
```

## 本章小结

本章是 DashScope API 的实战指南：

1. **环境准备**：Python 环境、SDK 安装、API Key 配置
2. **快速上手**：最简单的对话程序到完整的项目结构
3. **参数详解**：temperature、top_p、max_tokens 等核心参数
4. **错误处理**：常见错误码、错误处理模板、重试策略
5. **实战示例**：文本摘要、翻译、代码审查、校园助手
6. **成本优化**：模型选择、Prompt 优化、缓存策略

掌握这些内容，你已经具备了使用 DashScope API 构建 AI 应用的基础能力。下一章我们将学习 Prompt 工程，掌握与 AI 高效沟通的核心技能。

---

## 思考与练习

1. **环境搭建**：完成 DashScope 开发环境搭建，运行第一个 AI 程序。

2. **参数实验**：使用不同的 temperature、top_p 参数，观察输出变化，总结规律。

3. **错误处理**：模拟 API 调用失败场景，验证你的错误处理代码是否正常工作。

4. **项目实践**：基于本章的代码框架，开发一个命令行翻译工具，支持中英互译。

5. **性能优化**：为你的应用添加缓存功能，对比优化前后的 API 调用次数和响应时间。

6. **扩展探索**：阅读 DashScope 官方文档，了解更多高级功能（如向量嵌入、图像生成等）。
