# 第9章：快速构建 AI 对话应用

> 本章介绍如何使用 Python 快速构建 AI 对话应用。从最简的 Gradio 原型，到生产级的 FastAPI 服务，再到对话历史管理，帮助你掌握 AI 应用开发的核心技能。

## 9.1 AI 对话应用概述

### 9.1.1 应用架构

一个完整的 AI 对话应用通常包含以下组件：

```
┌─────────────────────────────────────────────────────────────────┐
│                    AI 对话应用架构                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌────────────┐      ┌────────────┐      ┌────────────┐         │
│  │   前端     │      │   后端     │      │   AI服务   │         │
│  │  (Gradio/  │ ───► │  (FastAPI/ │ ───► │  (DashScope│         │
│  │   Streamlit│      │   Flask)   │      │   API)     │         │
│  │   React)   │ ◄─── │            │ ◄─── │            │         │
│  └────────────┘      └────────────┘      └────────────┘         │
│         │                   │                   │               │
│         │                   ↓                   │               │
│         │           ┌────────────┐              │               │
│         │           │   数据库   │              │               │
│         │           │(对话历史/  │              │               │
│         │           │ 用户信息)  │              │               │
│         │           └────────────┘              │               │
│         │                                         │               │
│         └─────────────────────────────────────────┘               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 9.1.2 开发模式选择

| 场景 | 推荐技术 | 说明 |
|------|----------|------|
| 快速原型/POC | Gradio | 几行代码即可完成界面 |
| 内部工具/演示 | Streamlit | 更丰富的 UI 组件 |
| 生产环境 | FastAPI | 高性能、异步、自动化文档 |
| Web 应用 | React/Vue | 前后端分离架构 |

## 9.2 Gradio：快速原型开发

### 9.2.1 Gradio 简介

**Gradio** 是一个用于构建机器学习 Web 应用的 Python 库，让你可以快速创建交互式界面。

**安装**：

```bash
pip install gradio
```

**核心优势**：
- 几行代码即可创建界面
- 自动生成分享链接
- 支持丰富的输入输出组件
- 内置聊天机器人组件

### 9.2.2 最简单的 AI 对话

```python
#!/usr/bin/env python3
"""
gradio-simple-chat.py
最简单的 AI 对话应用
"""

import gradio as gr
from dashscope import Generation

# 初始化 DashScope 客户端
dashscope.api_key = "your-api-key"

def chat_with_ai(message, history):
    """处理用户消息，返回 AI 回复"""
    # 构建消息历史
    messages = []
    for h in history:
        messages.append({"role": "user", "content": h[0]})
        messages.append({"role": "assistant", "content": h[1]})
    messages.append({"role": "user", "content": message})
    
    # 调用 API
    response = Generation.call(
        model="qwen-turbo",
        messages=messages,
        result_format="message"
    )
    
    if response.status_code == 200:
        return response.output.choices[0].message.content
    else:
        return f"出错了: {response.message}"

# 创建 Gradio 界面
demo = gr.ChatInterface(
    fn=chat_with_ai,
    title="AI 对话助手",
    description="基于通义千问的智能对话助手",
    examples=[
        "你好，请介绍一下你自己",
        "用Python写一个快速排序",
        "解释一下什么是云计算"
    ],
    theme="soft"
)

# 启动服务
if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860
    )
```

运行后访问 `http://localhost:7860` 即可看到界面。

### 9.2.3 带系统提示的对话

```python
#!/usr/bin/env python3
"""
gradio-chatbot.py
带系统提示和更多功能的对话应用
"""

import gradio as gr
from dashscope import Generation
from dashscope.common import Message

# 系统提示词
SYSTEM_PROMPT = """你是一位专业的Python讲师，名为"小P老师"。
你有以下特点：
1. 讲解深入浅出，善于用例子说明抽象概念
2. 注重代码规范和最佳实践
3. 鼓励学生动手实践
4. 回答简洁明了，避免冗长

请用友好的方式与学生交流。"""

def chat(message, history, system_prompt):
    """带系统提示的对话"""
    messages = [
        Message(role="system", content=system_prompt)
    ]
    
    # 添加历史对话
    for h in history:
        messages.append(Message(role="user", content=h[0]))
        messages.append(Message(role="assistant", content=h[1]))
    
    # 添加当前消息
    messages.append(Message(role="user", content=message))
    
    # 调用 API
    response = Generation.call(
        model="qwen-plus",
        messages=messages,
        temperature=0.7,
        result_format="message"
    )
    
    if response.status_code == 200:
        return response.output.choices[0].message.content
    else:
        return f"出错了: {response.message}"

def reset_conversation():
    """重置对话"""
    return None, []

# 创建界面
with gr.Blocks(title="Python 助教") as demo:
    gr.Markdown("# 🎓 Python 助教")
    gr.Markdown("一个基于 AI 的 Python 学习助手，帮你解答 Python 相关问题。")
    
    with gr.Row():
        with gr.Column(scale=3):
            chatbot = gr.Chatbot(
                label="对话历史",
                height=400,
                show_copy_button=True
            )
            msg = gr.Textbox(
                label="输入你的问题",
                placeholder="例如：什么是装饰器？",
                lines=2
            )
            
            with gr.Row():
                submit_btn = gr.Button("发送", variant="primary")
                clear_btn = gr.Button("清空对话")
        
        with gr.Column(scale=1):
            gr.Markdown("### ⚙️ 设置")
            
            model_select = gr.Dropdown(
                choices=["qwen-turbo", "qwen-plus", "qwen-max"],
                value="qwen-plus",
                label="选择模型"
            )
            
            temp_slider = gr.Slider(
                minimum=0.0,
                maximum=1.0,
                value=0.7,
                step=0.1,
                label="创意度 (Temperature)"
            )
            
            system_input = gr.Textbox(
                value=SYSTEM_PROMPT,
                label="系统提示词",
                lines=5,
                visible=False
            )
            
            gr.Markdown("---")
            gr.Markdown("💡 **提示**：直接输入 Python 问题，AI 会帮你解答！")
    
    def respond(message, history, model, temperature):
        """处理回复"""
        # 更新 API 调用
        messages = [
            Message(role="system", content=SYSTEM_PROMPT)
        ]
        
        for h in history:
            messages.append(Message(role="user", content=h[0]))
            messages.append(Message(role="assistant", content=h[1]))
        
        messages.append(Message(role="user", content=message))
        
        response = Generation.call(
            model=model,
            messages=messages,
            temperature=temperature,
            result_format="message"
        )
        
        if response.status_code == 200:
            bot_message = response.output.choices[0].message.content
        else:
            bot_message = f"出错了: {response.message}"
        
        history.append((message, bot_message))
        return "", history
    
    # 绑定事件
    submit_btn.click(
        respond,
        inputs=[msg, chatbot, model_select, temp_slider],
        outputs=[msg, chatbot]
    )
    
    msg.submit(
        respond,
        inputs=[msg, chatbot, model_select, temp_slider],
        outputs=[msg, chatbot]
    )
    
    clear_btn.click(
        lambda: (None, []),
        outputs=[msg, chatbot]
    )

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
```

### 9.2.4 流式输出

```python
#!/usr/bin/env python3
"""
gradio-streaming.py
流式输出的 AI 对话
"""

import gradio as gr
from dashscope import Generation

def stream_chat(message, history):
    """流式对话"""
    messages = []
    for h in history:
        messages.append({"role": "user", "content": h[0]})
        messages.append({"role": "assistant", "content": h[1]})
    messages.append({"role": "user", "content": message})
    
    # 流式调用
    response = Generation.call(
        model="qwen-turbo",
        messages=messages,
        stream=True,
        incremental_output=True,
        result_format="message"
    )
    
    partial_text = ""
    for chunk in response:
        if chunk.status_code == 200:
            content = chunk.output.choices[0].delta.content
            partial_text += content
            yield partial_text
        else:
            yield f"出错了: {chunk.message}"

# 创建界面
demo = gr.ChatInterface(
    fn=stream_chat,
    type="messages",  # 使用 messages 格式
    title="🚀 流式对话助手",
    description="体验流畅的流式输出效果",
)

if __name__ == "__main__":
    demo.launch()
```

## 9.3 FastAPI：生产级服务

### 9.3.1 FastAPI 简介

**FastAPI** 是一个现代、快速的 Python Web 框架，基于标准 Python 类型提示，支持异步编程，自动生成 API 文档。

**安装**：

```bash
pip install fastapi uvicorn python-dotenv sse-starlette
```

### 9.3.2 基础 API 服务

```python
#!/usr/bin/env python3
"""
fastapi-basic.py
FastAPI 基础服务
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional
import os

from dashscope import Generation
from dashscope.common import Message

# 加载环境变量
from dotenv import load_dotenv
load_dotenv()

# 初始化 FastAPI
app = FastAPI(
    title="AI Chat API",
    description="基于 DashScope 的 AI 对话服务",
    version="1.0.0"
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 请求模型
class Message(BaseModel):
    """消息模型"""
    role: str = Field(..., description="角色: system/user/assistant")
    content: str = Field(..., description="消息内容")

class ChatRequest(BaseModel):
    """对话请求"""
    messages: List[Message] = Field(..., description="消息列表")
    model: str = Field(default="qwen-turbo", description="模型名称")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=2000, ge=1, le=4000)

class ChatResponse(BaseModel):
    """对话响应"""
    message: str
    model: str
    usage: dict

# API 端点
@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    对话接口
    """
    try:
        # 转换为 DashScope 格式
        dashscope_messages = [
            Message(role=m.role, content=m.content)
            for m in request.messages
        ]
        
        # 调用 API
        response = Generation.call(
            model=request.model,
            messages=dashscope_messages,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            result_format="message"
        )
        
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail=response.message)
        
        choice = response.output.choices[0].message
        
        return ChatResponse(
            message=choice.content,
            model=response.request.model,
            usage={
                "input_tokens": response.output.usage.input_tokens if hasattr(response.output, 'usage') else 0,
                "output_tokens": response.output.usage.output_tokens if hasattr(response.output, 'usage') else 0,
            }
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/models")
async def list_models():
    """列出可用模型"""
    return {
        "models": [
            {"id": "qwen-turbo", "name": "Qwen Turbo", "description": "快速响应"},
            {"id": "qwen-plus", "name": "Qwen Plus", "description": "平衡性能"},
            {"id": "qwen-max", "name": "Qwen Max", "description": "最高质量"},
        ]
    }

@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}

# 运行服务
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### 9.3.3 流式 API

```python
#!/usr/bin/env python3
"""
fastapi-streaming.py
FastAPI 流式服务
"""

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import List
import json
import asyncio

from dashscope import Generation
from dashscope.common import Message

app = FastAPI()

class ChatRequest(BaseModel):
    messages: List[Message]
    model: str = "qwen-turbo"
    temperature: float = 0.7

async def generate_stream(request: ChatRequest):
    """生成流式响应"""
    try:
        # 流式调用
        responses = Generation.call(
            model=request.model,
            messages=[Message(role=m.role, content=m.content) for m in request.messages],
            temperature=request.temperature,
            stream=True,
            incremental_output=True,
            result_format="message"
        )
        
        for chunk in responses:
            if chunk.status_code == 200:
                content = chunk.output.choices[0].delta.content
                
                # SSE 格式
                data = {
                    "content": content,
                    "done": False
                }
                yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
            else:
                error_data = {
                    "error": chunk.message,
                    "done": True
                }
                yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"
        
        # 发送完成信号
        yield f"data: {json.dumps({'done': True})}\n\n"
    
    except Exception as e:
        error_data = {"error": str(e), "done": True}
        yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"

@app.post("/api/chat/stream")
async def chat_stream(request: ChatRequest):
    """流式对话接口"""
    return StreamingResponse(
        generate_stream(request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )
```

### 9.3.4 带数据库的完整服务

```python
#!/usr/bin/env python3
"""
fastapi-complete.py
带数据库的完整对话服务
"""

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import uuid

import sqlite3
from contextlib import contextmanager

from dashscope import Generation
from dashscope.common import Message

app = FastAPI(title="AI Chat Service")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============== 数据库操作 ==============

DB_PATH = "chat_history.db"

@contextmanager
def get_db():
    """数据库上下文管理器"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()

def init_db():
    """初始化数据库"""
    with get_db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                title TEXT
            );
            
            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                conversation_id TEXT,
                role TEXT,
                content TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (conversation_id) REFERENCES conversations(id)
            );
        """)

# ============== 数据模型 ==============

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    conversation_id: Optional[str] = None
    messages: List[Message]
    model: str = "qwen-turbo"
    temperature: float = 0.7

class ChatResponse(BaseModel):
    conversation_id: str
    message: str
    message_id: str

# ============== API 端点 ==============

@app.on_event("startup")
async def startup():
    init_db()

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """对话接口"""
    try:
        # 创建或获取会话
        if request.conversation_id:
            conversation_id = request.conversation_id
        else:
            conversation_id = str(uuid.uuid4())
            with get_db() as conn:
                conn.execute(
                    "INSERT INTO conversations (id, title) VALUES (?, ?)",
                    (conversation_id, request.messages[-1].content[:50])
                )
        
        # 保存用户消息
        user_msg_id = str(uuid.uuid4())
        with get_db() as conn:
            conn.execute(
                "INSERT INTO messages (id, conversation_id, role, content) VALUES (?, ?, ?, ?)",
                (user_msg_id, conversation_id, "user", request.messages[-1].content)
            )
        
        # 调用 AI
        dashscope_messages = [
            Message(role=m.role, content=m.content)
            for m in request.messages
        ]
        
        response = Generation.call(
            model=request.model,
            messages=dashscope_messages,
            temperature=request.temperature,
            result_format="message"
        )
        
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail=response.message)
        
        assistant_content = response.output.choices[0].message.content
        
        # 保存助手消息
        assistant_msg_id = str(uuid.uuid4())
        with get_db() as conn:
            conn.execute(
                "INSERT INTO messages (id, conversation_id, role, content) VALUES (?, ?, ?, ?)",
                (assistant_msg_id, conversation_id, "assistant", assistant_content)
            )
            conn.execute(
                "UPDATE conversations SET updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (conversation_id,)
            )
        
        return ChatResponse(
            conversation_id=conversation_id,
            message=assistant_content,
            message_id=assistant_msg_id
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/conversations")
async def list_conversations(limit: int = 20):
    """获取会话列表"""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM conversations ORDER BY updated_at DESC LIMIT ?",
            (limit,)
        ).fetchall()
        
        return [
            {
                "id": row["id"],
                "title": row["title"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"]
            }
            for row in rows
        ]

@app.get("/api/conversations/{conversation_id}/messages")
async def get_messages(conversation_id: str):
    """获取会话消息"""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM messages WHERE conversation_id = ? ORDER BY created_at",
            (conversation_id,)
        ).fetchall()
        
        return [
            {
                "id": row["id"],
                "role": row["role"],
                "content": row["content"],
                "created_at": row["created_at"]
            }
            for row in rows
        ]

@app.delete("/api/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str):
    """删除会话"""
    with get_db() as conn:
        conn.execute("DELETE FROM messages WHERE conversation_id = ?", (conversation_id,))
        conn.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))
    
    return {"status": "deleted"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

## 9.4 对话历史管理

### 9.4.1 对话上下文策略

```python
from typing import List, Dict
from dataclasses import dataclass

@dataclass
class ConversationContext:
    """对话上下文"""
    messages: List[Dict[str, str]]
    max_tokens: int = 8000
    system_prompt: str = ""
    
    def add_user_message(self, content: str):
        """添加用户消息"""
        self.messages.append({"role": "user", "content": content})
    
    def add_assistant_message(self, content: str):
        """添加助手消息"""
        self.messages.append({"role": "assistant", "content": content})
    
    def get_messages(self) -> List[Dict]:
        """获取消息列表（带截断）"""
        result = []
        
        if self.system_prompt:
            result.append({"role": "system", "content": self.system_prompt})
        
        result.extend(self.messages)
        
        # 如果超过 token 限制，截断早期消息
        if self._estimate_tokens(result) > self.max_tokens:
            result = self._truncate_messages(result)
        
        return result
    
    def _estimate_tokens(self, messages: List[Dict]) -> int:
        """粗略估算 token 数量"""
        total = 0
        for msg in messages:
            # 中文字符约 2 token/字，英文约 4 token/词
            content = msg["content"]
            total += len(content) // 2  # 简化估算
        return total
    
    def _truncate_messages(self, messages: List[Dict]) -> List[Dict]:
        """截断消息以符合 token 限制"""
        # 保留系统提示
        result = [messages[0]] if messages[0]["role"] == "system" else []
        
        # 从后向前保留消息
        remaining_tokens = self.max_tokens - self._estimate_tokens(result)
        
        for msg in reversed(messages[1:]):
            msg_tokens = self._estimate_tokens([msg])
            if remaining_tokens >= msg_tokens:
                result.insert(1, msg)
                remaining_tokens -= msg_tokens
            else:
                break
        
        return result
    
    def clear(self):
        """清空对话历史"""
        self.messages = []
```

### 9.4.2 对话摘要策略

```python
class SummarizingContext(ConversationContext):
    """带摘要的对话上下文"""
    
    def __init__(self, *args, summary_trigger_tokens: int = 6000, **kwargs):
        super().__init__(*args, **kwargs)
        self.summary_trigger_tokens = summary_trigger_tokens
        self.summary = ""
    
    def get_messages(self) -> List[Dict]:
        """获取消息列表（带摘要）"""
        result = []
        
        if self.system_prompt:
            result.append({"role": "system", "content": self.system_prompt})
        
        # 如果有摘要，加入到开头
        if self.summary:
            result.append({
                "role": "system",
                "content": f"之前的对话摘要：{self.summary}"
            })
        
        result.extend(self.messages)
        
        # 检查是否需要摘要
        if self._estimate_tokens(result) > self.summary_trigger_tokens:
            self._generate_summary()
            # 重新构建消息列表
            result = []
            if self.system_prompt:
                result.append({"role": "system", "content": self.system_prompt})
            if self.summary:
                result.append({
                    "role": "system",
                    "content": f"之前的对话摘要：{self.summary}"
                })
            # 只保留最近几条消息
            result.extend(self.messages[-4:])
        
        return result
    
    def _generate_summary(self):
        """生成对话摘要"""
        # 实际项目中调用 AI 生成摘要
        summary_prompt = f"""
请为以下对话生成一个简洁的摘要，保留关键信息：

{self._format_conversation()}

摘要要求：
- 50字以内
- 包含关键话题和结论
- 使用中文
"""
        # 简化实现，实际应该调用 AI
        recent = self.messages[-6:] if len(self.messages) > 6 else self.messages
        topics = [m["content"][:30] for m in recent if m["role"] == "user"]
        self.summary = f"讨论了{len(topics)}个问题"
```

### 9.4.3 多会话管理

```python
from typing import Dict, Optional
from datetime import datetime
import threading

class ConversationManager:
    """会话管理器"""
    
    def __init__(self):
        self.conversations: Dict[str, ConversationContext] = {}
        self.lock = threading.Lock()
    
    def create_conversation(
        self,
        conversation_id: Optional[str] = None,
        system_prompt: str = ""
    ) -> str:
        """创建新会话"""
        with self.lock:
            if conversation_id is None:
                conversation_id = str(uuid.uuid4())
            
            self.conversations[conversation_id] = ConversationContext(
                messages=[],
                system_prompt=system_prompt
            )
            
            return conversation_id
    
    def get_conversation(self, conversation_id: str) -> Optional[ConversationContext]:
        """获取会话"""
        return self.conversations.get(conversation_id)
    
    def delete_conversation(self, conversation_id: str) -> bool:
        """删除会话"""
        with self.lock:
            if conversation_id in self.conversations:
                del self.conversations[conversation_id]
                return True
            return False
    
    def list_conversations(self) -> List[Dict]:
        """列出所有会话"""
        return [
            {
                "id": cid,
                "message_count": len(ctx.messages),
                "token_count": ctx._estimate_tokens(ctx.get_messages())
            }
            for cid, ctx in self.conversations.items()
        ]

# 全局实例
conversation_manager = ConversationManager()
```

## 9.5 项目实战：构建聊天机器人

### 9.5.1 项目结构

```
chatbot-project/
├── app/
│   ├── __init__.py
│   ├── main.py           # FastAPI 入口
│   ├── models.py         # 数据模型
│   ├── schemas.py        # Pydantic 模型
│   ├── api/
│   │   ├── __init__.py
│   │   └── chat.py       # 聊天 API
│   ├── services/
│   │   ├── __init__.py
│   │   ├── ai_service.py # AI 服务封装
│   │   └── context.py    # 上下文管理
│   └── db/
│       ├── __init__.py
│       └── sqlite.py     # 数据库操作
├── static/               # 静态文件
├── templates/            # HTML 模板
├── tests/               # 测试
├── .env                 # 环境变量
├── requirements.txt
└── README.md
```

### 9.5.2 AI 服务封装

```python
# app/services/ai_service.py
"""
AI 服务封装
"""

from typing import List, Dict, Optional, AsyncIterator
import dashscope
from dashscope import Generation
from dashscope.common import Message

class AIService:
    """AI 服务封装类"""
    
    def __init__(self, api_key: str, default_model: str = "qwen-turbo"):
        dashscope.api_key = api_key
        self.default_model = default_model
    
    def chat(
        self,
        messages: List[Dict],
        model: str = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> Dict:
        """
        对话生成（非流式）
        
        Returns:
            {"message": str, "usage": dict}
        """
        model = model or self.default_model
        
        dashscope_messages = [
            Message(role=m["role"], content=m["content"])
            for m in messages
        ]
        
        response = Generation.call(
            model=model,
            messages=dashscope_messages,
            temperature=temperature,
            max_tokens=max_tokens,
            result_format="message"
        )
        
        if response.status_code != 200:
            raise Exception(f"AI 服务错误: {response.message}")
        
        return {
            "message": response.output.choices[0].message.content,
            "usage": {
                "input_tokens": response.output.usage.input_tokens,
                "output_tokens": response.output.usage.output_tokens,
            } if hasattr(response.output, 'usage') else {}
        }
    
    async def chat_stream(
        self,
        messages: List[Dict],
        model: str = None,
        temperature: float = 0.7
    ) -> AsyncIterator[str]:
        """
        对话生成（流式）
        
        Yields:
            str: 生成的文本片段
        """
        model = model or self.default_model
        
        dashscope_messages = [
            Message(role=m["role"], content=m["content"])
            for m in messages
        ]
        
        responses = Generation.call(
            model=model,
            messages=dashscope_messages,
            temperature=temperature,
            stream=True,
            incremental_output=True,
            result_format="message"
        )
        
        for chunk in responses:
            if chunk.status_code == 200:
                content = chunk.output.choices[0].delta.content
                if content:
                    yield content
            else:
                raise Exception(f"AI 服务错误: {chunk.message}")

# 单例
ai_service = AIService(api_key=os.getenv("DASHSCOPE_API_KEY"))
```

### 9.5.3 前端页面

```html
<!-- templates/chat.html -->
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI 聊天机器人</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f5f5;
            height: 100vh;
            display: flex;
            flex-direction: column;
        }
        
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 1rem 2rem;
            text-align: center;
        }
        
        .chat-container {
            flex: 1;
            max-width: 800px;
            margin: 0 auto;
            width: 100%;
            padding: 1rem;
            overflow-y: auto;
        }
        
        .message {
            margin-bottom: 1rem;
            padding: 1rem;
            border-radius: 1rem;
            max-width: 80%;
        }
        
        .message.user {
            background: #667eea;
            color: white;
            margin-left: auto;
            border-bottom-right-radius: 0.25rem;
        }
        
        .message.assistant {
            background: white;
            color: #333;
            border-bottom-left-radius: 0.25rem;
            box-shadow: 0 1px 2px rgba(0,0,0,0.1);
        }
        
        .input-area {
            background: white;
            padding: 1rem 2rem;
            border-top: 1px solid #eee;
            display: flex;
            gap: 1rem;
        }
        
        .input-area input {
            flex: 1;
            padding: 0.75rem 1rem;
            border: 1px solid #ddd;
            border-radius: 2rem;
            font-size: 1rem;
            outline: none;
        }
        
        .input-area input:focus {
            border-color: #667eea;
        }
        
        .input-area button {
            padding: 0.75rem 1.5rem;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 2rem;
            cursor: pointer;
            font-size: 1rem;
        }
        
        .input-area button:hover {
            background: #764ba2;
        }
        
        .input-area button:disabled {
            background: #ccc;
            cursor: not-allowed;
        }
        
        .typing {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            color: #666;
            padding: 1rem;
        }
        
        .typing span {
            width: 8px;
            height: 8px;
            background: #667eea;
            border-radius: 50%;
            animation: bounce 1.4s infinite ease-in-out;
        }
        
        .typing span:nth-child(1) { animation-delay: -0.32s; }
        .typing span:nth-child(2) { animation-delay: -0.16s; }
        
        @keyframes bounce {
            0%, 80%, 100% { transform: scale(0); }
            40% { transform: scale(1); }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🤖 AI 聊天机器人</h1>
    </div>
    
    <div class="chat-container" id="chatContainer">
        <div class="message assistant">
            你好！我是 AI 助手，有什么可以帮你的吗？
        </div>
    </div>
    
    <div class="input-area">
        <input type="text" id="userInput" placeholder="输入消息..." autocomplete="off">
        <button id="sendBtn" onclick="sendMessage()">发送</button>
    </div>
    
    <script>
        const chatContainer = document.getElementById('chatContainer');
        const userInput = document.getElementById('userInput');
        const sendBtn = document.getElementById('sendBtn');
        
        let conversationId = null;
        
        userInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
        
        async function sendMessage() {
            const message = userInput.value.trim();
            if (!message) return;
            
            // 显示用户消息
            addMessage(message, 'user');
            userInput.value = '';
            
            // 显示加载状态
            const typingDiv = addTypingIndicator();
            
            try {
                const response = await fetch('/api/chat/stream', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        conversation_id: conversationId,
                        messages: [{ role: 'user', content: message }]
                    })
                });
                
                chatContainer.removeChild(typingDiv);
                
                if (!response.ok) {
                    throw new Error('请求失败');
                }
                
                // 创建助手消息框
                const assistantDiv = document.createElement('div');
                assistantDiv.className = 'message assistant';
                chatContainer.appendChild(assistantDiv);
                
                // 读取流式响应
                const reader = response.body.getReader();
                const decoder = new TextDecoder();
                let fullMessage = '';
                
                while (true) {
                    const { done, value } = await reader.read();
                    if (done) break;
                    
                    const chunk = decoder.decode(value);
                    const lines = chunk.split('\n');
                    
                    for (const line of lines) {
                        if (line.startsWith('data: ')) {
                            const data = JSON.parse(line.slice(6));
                            if (data.content) {
                                fullMessage += data.content;
                                assistantDiv.textContent = fullMessage;
                                scrollToBottom();
                            }
                        }
                    }
                }
                
                // 更新会话ID
                const data = await response.json();
                if (data.conversation_id) {
                    conversationId = data.conversation_id;
                }
                
            } catch (error) {
                chatContainer.removeChild(typingDiv);
                addMessage('抱歉，出错了: ' + error.message, 'assistant');
            }
        }
        
        function addMessage(content, type) {
            const div = document.createElement('div');
            div.className = `message ${type}`;
            div.textContent = content;
            chatContainer.appendChild(div);
            scrollToBottom();
        }
        
        function addTypingIndicator() {
            const div = document.createElement('div');
            div.className = 'typing';
            div.innerHTML = '<span></span><span></span><span></span> 思考中...';
            chatContainer.appendChild(div);
            scrollToBottom();
            return div;
        }
        
        function scrollToBottom() {
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }
    </script>
</body>
</html>
```

## 本章小结

本章介绍了快速构建 AI 对话应用的方法：

1. **Gradio**：几行代码创建交互式界面，适合快速原型
2. **FastAPI**：高性能 API 服务，支持异步和自动文档
3. **对话历史管理**：上下文管理、摘要策略、多会话管理
4. **项目实战**：完整的聊天机器人架构

下一章我们将学习企业知识库问答系统，掌握 RAG 架构的核心技术。

---

## 思考与练习

1. **实践练习**：使用 Gradio 创建一个简单的 AI 对话应用。

2. **进阶挑战**：使用 FastAPI 实现一个带数据库的完整对话服务。

3. **性能优化**：思考如何在大规模用户场景下优化对话服务。

4. **功能扩展**：为对话应用添加以下功能：
   - 敏感词过滤
   - 消息撤回
   - 会话搜索

5. **架构设计**：设计一个高并发的聊天服务架构。
