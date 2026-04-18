# 第5章：阿里云大模型产品

> 本章详细介绍阿里云的大模型产品体系，包括 DashScope 灵积平台、通义千问 Qwen 系列、通义万相（图像生成）、通义听悟（语音处理）等产品，帮助你快速找到适合自己应用场景的AI能力。

## 5.1 阿里云大模型产品全景

### 5.1.1 产品体系架构

阿里云的大模型产品布局完整，覆盖从底层基础设施到上层应用的各个层面：

```
┌─────────────────────────────────────────────────────────────────┐
│                  阿里云大模型产品体系                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                      应用层产品                          │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐   │   │
│  │  │通义千问  │ │通义万相  │ │通义听悟  │ │通义灵码  │   │   │
│  │  │  Chat   │ │ 图像生成  │ │ 语音处理  │ │ 代码助手 │   │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘   │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              ↓                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    模型服务平台                          │   │
│  │  ┌──────────────────────────────────────────────────┐   │   │
│  │  │              DashScope 灵积                        │   │   │
│  │  │  • 模型API调用  • 模型服务  • 模型评测  • 模型管理   │   │   │
│  │  └──────────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              ↓                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    模型训练平台                          │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐   │   │
│  │  │  PAI-    │ │  PAI-    │ │  PAI-    │ │  模型库   │   │   │
│  │  │  DSW     │ │  EAS     │ │  Autodl  │ │  ModelScope│  │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘   │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 5.1.2 核心产品一览

| 产品 | 类型 | 说明 |
|------|------|------|
| **DashScope 灵积** | 模型服务平台 | 统一的大模型 API 接入平台 |
| **通义千问 Qwen** | 大语言模型 | 文本理解与生成 |
| **通义万相** | 多模态模型 | 图像生成、风格迁移 |
| **通义听悟** | 语音模型 | 语音转文字、会议纪要 |
| **通义灵码** | 代码模型 | 代码补全、代码审查 |
| **PAI** | 机器学习平台 | 模型训练与部署 |
| **ModelScope** | 模型社区 | 开源模型库 |

## 5.2 DashScope 灵积平台

### 5.2.1 平台概述

**DashScope**（灵积）是阿里云推出的大模型服务平台，提供统一的 API 接口，让你可以通过简单的 HTTP 调用访问多种大模型能力。

**核心优势**：

- **统一入口**：一个 API 接入多种模型
- **按量付费**：无需预付费，按实际调用量计费
- **弹性扩展**：自动应对流量高峰
- **稳定可靠**：企业级 SLA 保障

### 5.2.2 支持的模型类别

```
┌─────────────────────────────────────────────────────────────────┐
│                     DashScope 支持的模型类别                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  📝 文本生成                                                     │
│  ├── qwen-turbo   (高速)                                        │
│  ├── qwen-plus    (标准)                                        │
│  ├── qwen-max     (高性能)                                      │
│  └── qwen-max-longcontext (长上下文)                             │
│                                                                  │
│  🎨 图像生成                                                     │
│  ├── wanx2.1      (文生图)                                      │
│  └── wanx-v1      (图像风格化)                                   │
│                                                                  │
│  🔊 语音识别                                                     │
│  ├── paraformer-zh  (中文)                                      │
│  └── paraformer-en  (英文)                                      │
│                                                                  │
│  🗣️ 语音合成                                                     │
│  └── cosyvoice-v1  (自然语音)                                   │
│                                                                  │
│  🔍 向量嵌入                                                     │
│  └── text-embedding-v3  (高精度向量)                            │
│                                                                  │
│  📊 重排序                                                       │
│  └── rerank-v3      (语义排序)                                  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 5.2.3 API 申请与配置

**Step 1：开通服务**

1. 登录阿里云控制台
2. 搜索"DashScope"或访问 https://dashscope.console.aliyun.com
3. 点击"开通服务"
4. 完成授权

**Step 2：获取 API Key**

1. 进入 DashScope 控制台
2. 点击左侧"API-KEY管理"
3. 创建新的 API-KEY
4. 妥善保存生成的密钥

> ⚠️ **安全提示**：API Key 等同于你的账号密码，请勿泄露或提交到公开代码仓库。

**Step 3：配置环境变量**

```bash
# macOS/Linux: 添加到 ~/.bashrc 或 ~/.zshrc
export DASHSCOPE_API_KEY="sk-xxxxxxxxxxxxxxxxxxxxxxxx"

# Windows: 在系统环境变量中添加
# DASHSCOPE_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx

# 验证配置
echo $DASHSCOPE_API_KEY
```

**Step 4：SDK 安装**

```bash
# 使用 pip 安装
pip install dashscope

# 或使用阿里云 SDK
pip install alibaba-cloud-sdk-go-v3
```

## 5.3 通义千问 Qwen 系列

### 5.3.1 Qwen 模型家族

**通义千问（Qwen）** 是阿里云自研的大语言模型系列，参数规模从十几亿到上千亿不等：

| 模型 | 参数量 | 上下文 | 适用场景 |
|------|--------|--------|----------|
| **qwen-turbo** | - | 8K | 快速响应、低延迟场景 |
| **qwen-plus** | - | 32K | 平衡性能与成本 |
| **qwen-max** | - | 8K | 高质量输出场景 |
| **qwen-max-longcontext** | - | 100K | 长文档分析 |
| **qwen-vl-plus** | - | - | 图文理解 |
| **qwen-audio** | - | - | 音频理解 |

### 5.3.2 模型特点

**Qwen 的核心优势**：

1. **强大的中文能力**：针对中文语境优化，中文任务表现优异
2. **开源开放**：Qwen 系列开源模型在 ModelScope 和 HuggingFace 可下载
3. **长上下文**：部分版本支持超长上下文窗口
4. **工具调用**：支持 Function Calling，便于 Agent 开发
5. **代码能力**：CodeQwen 在代码生成方面表现突出

### 5.3.3 API 调用示例

#### 基础对话调用

```python
import dashscope
from dashscope import Generation

# 设置 API Key
dashscope.api_key = "your-api-key"

def chat_with_qwen(prompt: str, model: str = "qwen-turbo") -> str:
    """与通义千问对话"""
    response = Generation.call(
        model=model,
        messages=[
            {"role": "system", "content": "你是一个有帮助的AI助手。"},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        top_p=0.8,
        result_format="message"
    )
    
    if response.status_code == 200:
        return response.output.choices[0].message.content
    else:
        return f"请求失败: {response.code} - {response.message}"

# 使用示例
result = chat_with_qwen("用一句话解释什么是云计算")
print(result)
```

#### 多轮对话

```python
def multi_turn_chat(messages: list) -> str:
    """多轮对话"""
    response = Generation.call(
        model="qwen-plus",
        messages=messages,
        temperature=0.7,
        result_format="message"
    )
    
    if response.status_code == 200:
        return response.output.choices[0].message
    else:
        raise Exception(f"API调用失败: {response.message}")

# 构建多轮对话
conversation = [
    {"role": "system", "content": "你是一个专业的Python教练。"},
    {"role": "user", "content": "什么是装饰器？"},
]

# 第一轮对话
assistant_msg = multi_turn_chat(conversation)
print(f"助手: {assistant_msg.content}")
conversation.append(assistant_msg)

# 添加用户追问
conversation.append({
    "role": "user", 
    "content": "能给我一个实际的使用例子吗？"
})

# 第二轮对话
assistant_msg = multi_turn_chat(conversation)
print(f"助手: {assistant_msg.content}")
```

#### 流式输出

```python
from dashscope import Generation
from dashscope.callback import CallbackIterator

def stream_chat(prompt: str):
    """流式对话，实时显示输出"""
    responses = Generation.call(
        model="qwen-turbo",
        messages=[
            {"role": "user", "content": prompt}
        ],
        stream=True,
        incremental_output=True
    )
    
    full_response = ""
    for response in responses:
        if response.status_code == 200:
            content = response.output.choices[0].delta.content
            print(content, end="", flush=True)
            full_response += content
        else:
            print(f"\n错误: {response.message}")
            break
    print()  # 换行
    return full_response

# 使用示例
result = stream_chat("写一首关于春天的诗")
```

#### 函数调用（Function Calling）

```python
from dashscope import Generation
from openai import OpenAI
import json

# 定义可用函数
functions = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "获取指定城市的天气信息",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "城市名称，如：北京、上海"
                    },
                    "unit": {
                        "type": "string",
                        "enum": ["celsius", "fahrenheit"],
                        "description": "温度单位"
                    }
                },
                "required": ["city"]
            }
        }
    }
]

def get_weather(city: str, unit: str = "celsius") -> dict:
    """模拟天气查询API"""
    # 实际项目中这里调用真实天气API
    return {
        "city": city,
        "temperature": 22 if unit == "celsius" else 72,
        "condition": "晴转多云",
        "humidity": 65
    }

def chat_with_function(prompt: str):
    """支持函数调用的对话"""
    messages = [{"role": "user", "content": prompt}]
    
    # 第一次调用：模型决定是否需要调用函数
    response = Generation.call(
        model="qwen-max",
        messages=messages,
        tools=functions,
        temperature=0.7
    )
    
    if response.status_code == 200:
        choice = response.output.choices[0]
        
        # 如果模型决定调用函数
        if hasattr(choice, 'finish_reason') and choice.finish_reason == 'tool_calls':
            tool_calls = choice.message.tool_calls
            
            for tool_call in tool_calls:
                func_name = tool_call.function.name
                func_args = json.loads(tool_call.function.arguments)
                
                print(f"调用函数: {func_name}")
                print(f"参数: {func_args}")
                
                # 执行函数
                if func_name == "get_weather":
                    result = get_weather(**func_args)
                    print(f"函数返回: {result}")
                    
                    # 添加函数结果到对话
                    messages.append(choice.message)
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(result)
                    })
                    
                    # 第二次调用：基于函数结果生成回复
                    response = Generation.call(
                        model="qwen-max",
                        messages=messages,
                        tools=functions
                    )
                    print(f"最终回复: {response.output.choices[0].message.content}")
        else:
            print(f"回复: {choice.message.content}")

# 使用示例
chat_with_function("北京今天天气怎么样？")
```

## 5.4 通义万相：图像生成

### 5.4.1 产品概述

**通义万相**是阿里云的图像生成模型，支持文生图、图像风格化、图像修复等功能。

**主要能力**：

- **文本到图像**：根据文字描述生成图片
- **风格迁移**：将图片转换为不同艺术风格
- **相似图像生成**：生成与参考图风格相似的作品

### 5.4.2 API 调用示例

```python
from dashscope import ImageSynthesis

def text_to_image(prompt: str, model: str = "wanx2.1-pro") -> list:
    """
    文本生成图像
    prompt: 图像描述（中文效果更佳）
    返回生成的图像URL列表
    """
    response = ImageSynthesis.call(
        model=model,
        prompt=prompt,
        n=1,  # 生成数量
        size="1024*1024"  # 图像尺寸
    )
    
    if response.status_code == 200:
        return response.output.results
    else:
        raise Exception(f"生成失败: {response.message}")

def generate_and_save(prompt: str, output_path: str = "generated_image.png"):
    """生成图像并保存"""
    import urllib.request
    import ssl
    
    results = text_to_image(prompt)
    
    # 下载并保存图像
    for idx, result in enumerate(results):
        url = result.url
        print(f"图像 {idx+1} URL: {url}")
        
        # 下载图像
        ssl._create_default_https_context = ssl._create_unverified_context
        urllib.request.urlretrieve(url, f"{output_path}")
        print(f"已保存到: {output_path}")
    
    return results

# 使用示例
results = generate_and_save(
    "一只可爱的橘猫在阳光下打盹，写实风格，高清摄影"
)
```

### 5.4.3 提示词技巧

文生图模型对提示词非常敏感，以下是一些技巧：

```python
# 好的提示词示例
good_prompts = [
    # 明确主体
    "一只穿着宇航服的柯基犬",
    
    # 添加风格描述
    "山水画风格的中国古典园林",
    
    # 添加细节修饰
    "4K高清, 电影级光效, 辛烷值渲染",
    
    # 添加负面提示词（避免不良结果）
    "纯色背景, 简单构图, 不要文字",
]

# 结构化提示词模板
def build_prompt(subject: str, style: str, quality: str = "4K高清") -> str:
    """构建高质量提示词"""
    return f"{subject}, {style}, {quality}, 细节丰富, 光影效果好"

prompt = build_prompt(
    subject="未来城市的空中花园",
    style="赛博朋克风格",
    quality="8K超清"
)
print(prompt)  # 未来城市的空中花园, 赛博朋克风格, 8K超清, 细节丰富, 光影效果好
```

## 5.5 通义听悟：语音处理

### 5.5.1 产品概述

**通义听悟**是阿里云的语音处理产品，核心能力包括：

- **语音转文字（ASR）**：高准确率的中英文语音识别
- **会议纪要**：自动生成会议摘要和关键要点
- **实时字幕**：会议、直播实时字幕
- **音频分析**：说话人分离、情感分析

### 5.5.2 API 调用示例

#### 语音识别

```python
from dashscope import Audio

def transcribe_audio(audio_path: str) -> str:
    """
    语音转文字
    支持格式: wav, mp3, m4a, ogg
    """
    response = Audio.async_call(
        model="paraformer-zh",
        file_path=audio_path,
        notification_queue_name="your-queue-name"  # 需要先创建消息队列
    )
    
    if response.status_code == 200:
        task_id = response.output.task_id
        print(f"任务ID: {task_id}")
        return task_id
    else:
        raise Exception(f"转写失败: {response.message}")

def get_transcription_result(task_id: str) -> dict:
    """查询转写结果"""
    response = Audio.async_result(task_id)
    
    if response.status_code == 200:
        result = response.output
        return {
            "status": result.task_status,
            "text": result.results.get("text", ""),
            "sentences": result.results.get("sentences", [])
        }
    else:
        raise Exception(f"查询失败: {response.message}")

# 使用示例
task_id = transcribe_audio("/path/to/recording.mp3")

# 轮询获取结果（实际项目中建议使用消息队列异步通知）
import time
for _ in range(30):  # 最多等待5分钟
    result = get_transcription_result(task_id)
    if result["status"] == "SUCCEEDED":
        print("转写结果:")
        print(result["text"])
        break
    elif result["status"] == "FAILED":
        print("转写失败")
        break
    else:
        print(f"处理中... {result['status']}")
        time.sleep(10)
```

#### 处理长音频

```python
def transcribe_long_audio(file_path: str, language_hints: str = "zh") -> str:
    """
    转写长音频（自动分段处理）
    """
    import os
    
    # 验证文件存在
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"文件不存在: {file_path}")
    
    # 获取文件大小
    file_size = os.path.getsize(file_path)
    print(f"文件大小: {file_size / 1024 / 1024:.2f} MB")
    
    # 长音频自动分段
    response = Audio.async_call(
        model="paraformer-zh",
        file_path=file_path,
        language_hints=language_hints,
        speaker_number=2,  # 假设有2个说话人
        hot_word_ids=["阿里云", "DashScope"],  # 热词，提升专有名词识别率
        time_out=300  # 5分钟超时
    )
    
    return response.output.task_id

# 使用示例
task_id = transcribe_long_audio("/path/to/meeting.mp3")
```

## 5.6 其他模型服务

### 5.6.1 向量嵌入模型

```python
from dashscope import TextEmbedding

def get_embedding(text: str, model: str = "text-embedding-v3") -> list:
    """获取文本的向量表示"""
    response = TextEmbedding.call(
        model=model,
        input=text
    )
    
    if response.status_code == 200:
        return response.output.embeddings[0].embedding
    else:
        raise Exception(f"嵌入失败: {response.message}")

def compute_similarity(text1: str, text2: str) -> float:
    """计算两个文本的相似度"""
    import numpy as np
    
    emb1 = np.array(get_embedding(text1))
    emb2 = np.array(get_embedding(text2))
    
    # 余弦相似度
    similarity = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))
    return similarity

# 使用示例
sim = compute_similarity(
    "人工智能将改变未来的工作方式",
    "AI技术会深刻影响未来的职业发展"
)
print(f"相似度: {sim:.4f}")  # 约0.85-0.95
```

### 5.6.2 重排序模型

```python
from dashscope import Rerank

def semantic_search(query: str, documents: list) -> list:
    """
    语义重排序
    query: 查询文本
    documents: 文档列表
    返回按相关性排序的文档
    """
    response = Rerank.call(
        model="gte-rerank",
        query=query,
        documents=documents,
        top_n=len(documents)
    )
    
    if response.status_code == 200:
        results = response.output.results
        return [
            {"index": r.index, "document": documents[r.index], "score": r.relevance_score}
            for r in results
        ]
    else:
        raise Exception(f"重排失败: {response.message}")

# 使用示例
docs = [
    "云计算是一种通过网络提供计算资源的服务模式",
    "人工智能是研究如何让计算机模拟人类智能的学科",
    "机器学习是人工智能的一个分支，让计算机从数据中学习"
]

results = semantic_search("什么是机器学习？", docs)
for r in results:
    print(f"[{r['score']:.4f}] {r['document']}")
```

## 5.7 阿里云百炼平台

### 5.7.1 平台概述

**阿里云百炼**（原DashScope企业版）是面向企业客户的大模型服务平台，提供更丰富的企业级功能：

- **模型训练**：私有化模型定制
- **模型部署**：一键部署专属模型服务
- **知识库**：企业知识管理
- **Agent**：智能体编排
- **企业级安全**：数据隔离、权限管理

### 5.7.2 与 DashScope 的区别

| 功能 | DashScope | 百炼 |
|------|-----------|------|
| 目标用户 | 开发者/个人 | 企业 |
| 定价 | 按量付费 | 包年包月 |
| 数据安全 | 标准安全 | 企业级安全 |
| 私有化部署 | ❌ | ✅ |
| SLA保障 | 99.5% | 99.9% |
| 专属支持 | ❌ | ✅ |

## 本章小结

本章介绍了阿里云的大模型产品体系：

1. **DashScope 灵积**：统一的大模型 API 服务平台
2. **通义千问 Qwen**：覆盖多种规格的文本生成模型
3. **通义万相**：文本到图像的生成能力
4. **通义听悟**：语音识别与处理能力
5. **向量嵌入与重排序**：支撑 RAG 应用的核心能力

下一章我们将深入学习 DashScope API 的使用，掌握快速构建 AI 应用的能力。

---

## 思考与练习

1. **产品选型**：为一个校园助手应用选择合适的阿里云产品组合，说明理由。

2. **成本优化**：对比 qwen-turbo、qwen-plus、qwen-max 的定价特点，讨论在什么场景下应该选择哪个模型。

3. **实践操作**：在阿里云控制台开通 DashScope 服务，编写一个简单的对话程序。

4. **扩展探索**：调研 DashScope 还支持哪些模型（如通义万相的详细功能）。

5. **架构设计**：设计一个基于 DashScope API 的客服系统架构图。
