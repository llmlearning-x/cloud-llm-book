# 第 5 章 Agent 应用架构与实战

> **本章导读**
> 
> AI Agent（智能体）是大模型应用的高级形态，具备自主规划、工具调用、记忆保持和目标导向等能力。本章将深入解析 Agent 的核心架构、规划算法、工具集成机制、记忆系统设计，并提供基于阿里云百炼平台的 Agent 开发框架和实战案例。
> 
> **核心议题：**
> - Agent 的定义与核心能力
> - ReAct、Plan-and-Solve 等规划算法
> - 工具调用（Function Calling）机制
> - 短期记忆与长期记忆设计
> - 多 Agent 协作模式
> - 百炼平台 Agent 开发实战

---

## 5.1 Agent 核心概念

### 5.1.1 什么是 AI Agent？

AI Agent 是具备环境感知、决策推理与行动执行能力的自治系统。与传统被动响应的 AI 不同，Agent 能够：

| 特性 | 传统 AI | AI Agent |
|-----|--------|----------|
| 响应模式 | 被动问答 | 主动规划 |
| 任务范围 | 单一任务 | 多步骤复杂任务 |
| 工具使用 | 无 | 可调用外部 API/工具 |
| 记忆能力 | 无状态 | 短期 + 长期记忆 |
| 目标导向 | 无 | 有明确目标并持续追踪 |

**典型应用场景：**
- 智能客服：自动处理退款、改签等复杂流程
- 代码助手：理解需求→编写代码→运行测试→修复 bug
- 数据分析：获取数据→清洗→分析→生成报告
- 个人助理：安排行程、预订餐厅、发送邮件

### 5.1.2 Agent 四层架构

```
┌─────────────────────────────────────────────┐
│              规划层 (Planning)               │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │ 任务分解  │  │ 反思优化  │  │ 目标管理  │  │
│  └──────────┘  └──────────┘  └──────────┘  │
├─────────────────────────────────────────────┤
│              工具层 (Tool Use)               │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │ API 调用  │  │ 代码执行  │  │ 数据库查询 │  │
│  └──────────┘  └──────────┘  └──────────┘  │
├─────────────────────────────────────────────┤
│              记忆层 (Memory)                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │ 工作记忆  │  │  episodic │  │ semantic │  │
│  └──────────┘  └──────────┘  └──────────┘  │
├─────────────────────────────────────────────┤
│              感知层 (Perception)             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │ 文本输入  │  │ 图像识别  │  │ 语音理解  │  │
│  └──────────┘  └──────────┘  └──────────┘  │
└─────────────────────────────────────────────┘
```

---

## 5.2 规划能力（Planning）

### 5.2.1 任务分解（Task Decomposition）

将复杂任务拆解为可执行的子任务：

**示例：数据分析任务**
```
原始任务："分析上季度销售数据并生成报告"

分解后：
1. 从数据库获取 Q3 销售记录
2. 清洗数据（处理缺失值、异常值）
3. 计算关键指标（总额、环比、同比）
4. 生成可视化图表
5. 撰写分析报告
6. 发送邮件给管理层
```

**代码实现：**

```python
from dashscope import Generation

def decompose_task(task_description):
    """
    使用大模型进行任务分解
    """
    prompt = f"""请将以下复杂任务分解为可执行的子任务序列。
每个子任务应该是具体的、可独立完成的动作。

任务：{task_description}

请按以下格式输出：
1. [子任务 1]
2. [子任务 2]
...
"""
    
    response = Generation.call(
        model='qwen3.6-plus',
        messages=[{'role': 'user', 'content': prompt}],
        temperature=0.3  # 较低温度保证稳定性
    )
    
    plan_text = response.output.choices[0].message.content
    
    # 解析子任务列表
    subtasks = []
    for line in plan_text.split('\n'):
        if line.strip() and line[0].isdigit():
            task = line.split('.', 1)[1].strip().strip('[]')
            subtasks.append(task)
    
    return subtasks

# 使用示例
subtasks = decompose_task("分析上季度销售数据并生成报告")
for i, task in enumerate(subtasks, 1):
    print(f"{i}. {task}")
```

### 5.2.2 ReAct 算法（Reasoning + Acting）

ReAct 是当前最主流的 Agent 算法，核心思想是交替进行推理和行动：

```
Thought: 我需要先获取用户订单信息
Action: query_order_api(user_id="U12345")
Observation: {"order_id": "O789", "status": "shipped", ...}
Thought: 订单已发货，需要查询物流信息
Action: query_logistics_api(order_id="O789")
Observation: {"location": "上海", "estimated_delivery": "2026-04-18"}
Thought: 现在可以回答用户了
Final Answer: 您的订单已从上海发出，预计 4 月 18 日送达。
```

**ReAct 实现框架：**

```python
class ReActAgent:
    def __init__(self, model='qwen3.6-plus', tools=None):
        self.model = model
        self.tools = tools or {}
        self.max_iterations = 10
    
    def run(self, question):
        """
        执行 ReAct 循环
        """
        history = []
        
        for iteration in range(self.max_iterations):
            # 1. 生成 Thought 和 Action
            prompt = self._build_prompt(question, history)
            response = Generation.call(
                model=self.model,
                messages=[{'role': 'user', 'content': prompt}]
            )
            output = response.output.choices[0].message.content
            
            # 2. 解析输出
            thought, action, action_input = self._parse_output(output)
            
            if not action:
                # 没有 Action，说明已有最终答案
                return thought
            
            # 3. 执行 Action
            observation = self._execute_action(action, action_input)
            
            # 4. 记录到历史
            history.append({
                'thought': thought,
                'action': action,
                'action_input': action_input,
                'observation': observation
            })
        
        raise Exception("达到最大迭代次数，未能完成任务")
    
    def _build_prompt(self, question, history):
        """构建 ReAct Prompt"""
        tools_desc = "\n".join([
            f"{name}: {desc}" for name, (desc, _) in self.tools.items()
        ])
        
        prompt = f"""请逐步思考并解决问题。你可以使用以下工具：

{tools_desc}

问题：{question}

"""
        # 添加历史对话
        for i, step in enumerate(history):
            prompt += f"""Step {i+1}:
Thought: {step['thought']}
Action: {step['action']}
Action Input: {step['action_input']}
Observation: {step['observation']}

"""
        
        prompt += f"Step {len(history)+1}:\nThought:"
        return prompt
    
    def _parse_output(self, output):
        """解析 Thought/Action"""
        import re
        
        thought_match = re.search(r'Thought:\s*(.+?)(?=Action:|$)', output, re.DOTALL)
        action_match = re.search(r'Action:\s*(\w+)', output)
        input_match = re.search(r'Action Input:\s*(.+?)(?=Observation:|$)', output, re.DOTALL)
        
        thought = thought_match.group(1).strip() if thought_match else ""
        action = action_match.group(1) if action_match else None
        action_input = input_match.group(1).strip() if input_match else ""
        
        return thought, action, action_input
    
    def _execute_action(self, action_name, action_input):
        """执行工具调用"""
        if action_name not in self.tools:
            return f"错误：未知工具 {action_name}"
        
        _, func = self.tools[action_name]
        try:
            # 解析 JSON 参数
            import json
            params = json.loads(action_input)
            result = func(**params)
            return str(result)
        except Exception as e:
            return f"执行错误：{str(e)}"

# 定义工具
def query_order_api(user_id):
    return {"order_id": "O789", "status": "shipped", "amount": 299.00}

def query_logistics_api(order_id):
    return {"location": "上海", "estimated_delivery": "2026-04-18"}

tools = {
    "query_order_api": ("查询用户订单信息", query_order_api),
    "query_logistics_api": ("查询订单物流状态", query_logistics_api)
}

# 创建并运行 Agent
agent = ReActAgent(tools=tools)
result = agent.run("我的订单到哪了？用户 ID: U12345")
print(result)
```

### 5.2.3 Plan-and-Solve 算法

相比 ReAct，Plan-and-Solve 更强调先制定完整计划再执行：

```python
def plan_and_solve(problem, model='qwen3.6-plus'):
    # Phase 1: 制定计划
    plan_prompt = f"""
    问题：{problem}
    
    请制定一个详细的解决计划，列出每一步需要做什么。
    计划应该具体、可执行。
    """
    
    plan_response = Generation.call(
        model=model,
        messages=[{'role': 'user', 'content': plan_prompt}]
    )
    plan = plan_response.output.choices[0].message.content
    
    # Phase 2: 执行计划
    solve_prompt = f"""
    问题：{problem}
    
    计划：
    {plan}
    
    请按照计划逐步执行，并给出最终答案。
    """
    
    solve_response = Generation.call(
        model=model,
        messages=[{'role': 'user', 'content': solve_prompt}]
    )
    
    return solve_response.output.choices[0].message.content
```

---

## 5.3 工具调用（Function Calling）

### 5.3.1 Function Calling 机制

Qwen3.6-Plus 原生支持 Function Calling，可以精准调用外部工具：

```python
from dashscope import Generation
import json

# 定义工具 Schema
tools_schema = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "查询指定城市的天气",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "城市名称，如'北京'、'上海'"
                    },
                    "date": {
                        "type": "string",
                        "description": "日期，格式 YYYY-MM-DD，默认为今天"
                    }
                },
                "required": ["city"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "执行数学计算",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "数学表达式，如'2+2'、'sqrt(16)'"
                    }
                },
                "required": ["expression"]
            }
        }
    }
]

# 实际工具函数
def get_weather(city, date=None):
    # 模拟天气 API
    return f"{city}今天晴朗，气温 25°C"

def calculate(expression):
    # 安全计算（生产环境应使用更安全的方案）
    allowed_chars = set("0123456789+-*/.() ")
    if all(c in allowed_chars for c in expression):
        return str(eval(expression))
    return "无效表达式"

tools_map = {
    "get_weather": get_weather,
    "calculate": calculate
}

# 调用大模型
response = Generation.call(
    model='qwen3.6-plus',
    messages=[
        {'role': 'user', 'content': '北京今天天气怎么样？另外帮我算一下 123*456 等于多少'}
    ],
    tools=tools_schema,
    tool_choice='auto'  # 让模型决定是否调用工具
)

# 处理响应
message = response.output.choices[0].message

if message.tool_calls:
    # 需要调用工具
    for tool_call in message.tool_calls:
        func_name = tool_call.function.name
        func_args = json.loads(tool_call.function.arguments)
        
        # 执行工具函数
        result = tools_map[func_name](**func_args)
        print(f"调用 {func_name}, 结果：{result}")
        
        # 将结果返回给模型
        response2 = Generation.call(
            model='qwen3.6-plus',
            messages=[
                {'role': 'user', 'content': message.content},
                {'role': 'assistant', 'content': message.content, 'tool_calls': message.tool_calls},
                {'role': 'tool', 'content': result, 'tool_call_id': tool_call.id}
            ]
        )
        print(f"最终回答：{response2.output.choices[0].message.content}")
else:
    # 不需要调用工具
    print(message.content)
```

### 5.3.2 自定义工具封装

将企业现有系统封装为 Agent 工具：

```python
class ToolRegistry:
    """工具注册中心"""
    
    def __init__(self):
        self.tools = {}
    
    def register(self, name, description, func, param_schema):
        """注册一个工具"""
        self.tools[name] = {
            "schema": {
                "type": "function",
                "function": {
                    "name": name,
                    "description": description,
                    "parameters": param_schema
                }
            },
            "func": func
        }
    
    def get_all_schemas(self):
        """获取所有工具的 Schema"""
        return [t["schema"] for t in self.tools.values()]
    
    def execute(self, name, **kwargs):
        """执行工具"""
        if name not in self.tools:
            raise ValueError(f"未知工具：{name}")
        return self.tools[name]["func"](**kwargs)

# 示例：封装企业 CRM 系统
registry = ToolRegistry()

def create_customer(name, phone, email=None):
    """创建客户记录"""
    # 实际场景调用 CRM API
    customer_id = f"CUST_{hash(name) % 10000}"
    return {"customer_id": customer_id, "status": "created"}

def query_customer(customer_id):
    """查询客户信息"""
    return {"customer_id": customer_id, "name": "张三", "level": "VIP"}

# 注册工具
registry.register(
    name="create_customer",
    description="在 CRM 系统中创建新客户",
    func=create_customer,
    param_schema={
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "客户姓名"},
            "phone": {"type": "string", "description": "手机号码"},
            "email": {"type": "string", "description": "邮箱地址（可选）"}
        },
        "required": ["name", "phone"]
    }
)

registry.register(
    name="query_customer",
    description="查询客户详细信息",
    func=query_customer,
    param_schema={
        "type": "object",
        "properties": {
            "customer_id": {"type": "string", "description": "客户 ID"}
        },
        "required": ["customer_id"]
    }
)

# Agent 可以使用这些工具
agent_tools = registry.get_all_schemas()
```

---

## 5.4 记忆系统设计

### 5.4.1 短期记忆（工作记忆）

保存当前对话的上下文：

```python
class ShortTermMemory:
    def __init__(self, max_tokens=4000):
        self.messages = []
        self.max_tokens = max_tokens
        self.current_tokens = 0
    
    def add(self, role, content):
        """添加消息"""
        from tiktoken import encoding_for_model
        enc = encoding_for_model("qwen3.6-plus")
        tokens = len(enc.encode(content))
        
        # 如果超出限制，移除最早的消息
        while self.current_tokens + tokens > self.max_tokens and len(self.messages) > 1:
            old_msg = self.messages.pop(0)
            old_tokens = len(enc.encode(old_msg['content']))
            self.current_tokens -= old_tokens
        
        self.messages.append({'role': role, 'content': content})
        self.current_tokens += tokens
    
    def get_messages(self):
        """获取完整对话历史"""
        return self.messages.copy()
    
    def clear(self):
        """清空记忆"""
        self.messages = []
        self.current_tokens = 0

# 使用示例
memory = ShortTermMemory(max_tokens=4000)
memory.add('user', '你好')
memory.add('assistant', '你好！有什么可以帮助你的？')
memory.add('user', '我想了解一下你们的产品')

conversation = memory.get_messages()
```

### 5.4.2 长期记忆（向量存储）

将重要信息存入向量数据库，支持跨会话检索：

```python
class LongTermMemory:
    def __init__(self, dashvector_client, collection_name='user_memory'):
        self.client = dashvector_client
        self.collection_name = collection_name
        
        # 确保集合存在
        if collection_name not in [c.name for c in client.list()]:
            client.create(name=collection_name, dimension=2048, metric='cosine')
        
        self.collection = client.get(collection_name)
    
    def store(self, user_id, content, metadata=None):
        """存储记忆"""
        from dashscope import TextEmbedding
        
        # 向量化
        embedding_response = TextEmbedding.call(
            model='text-embedding-v3',
            input=content
        )
        vector = embedding_response.output['embeddings'][0]['embedding']
        
        # 存储
        from dashvector import Doc
        doc = Doc(
            id=f"mem_{user_id}_{int(time.time())}",
            vector=vector,
            fields={
                'user_id': user_id,
                'content': content,
                'timestamp': time.time(),
                **(metadata or {})
            }
        )
        self.collection.upsert([doc])
    
    def retrieve(self, user_id, query, top_k=3):
        """检索相关记忆"""
        from dashscope import TextEmbedding
        
        # 问题向量化
        embedding_response = TextEmbedding.call(
            model='text-embedding-v3',
            input=query
        )
        query_vector = embedding_response.output['embeddings'][0]['embedding']
        
        # 检索（带用户过滤）
        result = self.collection.query(
            vector=query_vector,
            topk=top_k * 2,  # 先多取一些
            filter=f"user_id='{user_id}'"
        )
        
        # 按时间衰减重排序
        memories = []
        for doc in result.docs:
            recency_score = 1 / (1 + (time.time() - doc.fields['timestamp']) / 86400)
            memories.append({
                'content': doc.fields['content'],
                'score': recency_score
            })
        
        # 排序取 Top-K
        memories.sort(key=lambda x: x['score'], reverse=True)
        return [m['content'] for m in memories[:top_k]]

# 使用示例
long_memory = LongTermMemory(client=dv_client)

# 存储用户偏好
long_memory.store(
    user_id="U12345",
    content="用户喜欢喝美式咖啡，不加糖",
    metadata={'category': 'preference'}
)

# 检索记忆
query = "用户喜欢什么饮品？"
memories = long_memory.retrieve("U12345", query)
print(memories)  # ["用户喜欢喝美式咖啡，不加糖"]
```

### 5.4.3 记忆总结机制

定期将对话历史压缩为摘要：

```python
def summarize_conversation(messages, model='qwen3.6-plus'):
    """
    将长对话历史总结为简洁摘要
    """
    conversation_text = "\n".join([
        f"{m['role']}: {m['content']}" for m in messages[-20:]  # 取最近 20 条
    ])
    
    prompt = f"""请总结以下对话的关键信息：

{conversation_text}

请提取：
1. 用户的核心需求
2. 已解决的问题
3. 待跟进的事项
4. 用户的重要偏好或特征

用简洁的语言总结，控制在 200 字以内。"""

    response = Generation.call(
        model=model,
        messages=[{'role': 'user', 'content': prompt}]
    )
    
    return response.output.choices[0].message.content

# 定期调用（例如每 10 轮对话）
if len(memory.messages) % 10 == 0:
    summary = summarize_conversation(memory.messages)
    long_memory.store(user_id, summary, metadata={'type': 'summary'})
```

---

## 5.5 多 Agent 协作

### 5.5.1 角色分工模式

复杂任务可由多个专业 Agent 协作完成：

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  规划 Agent  │────▶│  执行 Agent  │────▶│  审核 Agent  │
│  (Planner)  │     │  (Worker)   │     │  (Reviewer) │
└─────────────┘     └─────────────┘     └─────────────┘
       │                   │                   │
       ▼                   ▼                   ▼
  任务分解            调用工具            质量检查
  资源分配            执行操作            修正建议
```

**代码示例：**

```python
class MultiAgentSystem:
    def __init__(self):
        self.planner = ReActAgent(model='qwen3.6-plus')
        self.worker = ReActAgent(model='qwen3.6-plus')
        self.reviewer = ReActAgent(model='qwen3.6-plus')
    
    def solve(self, task):
        # 1. 规划 Agent 制定计划
        plan = self.planner.run(f"请为以下任务制定详细计划：{task}")
        
        # 2. 执行 Agent 按计划行动
        result = self.worker.run(f"任务：{task}\n计划：{plan}\n请执行计划。")
        
        # 3. 审核 Agent 检查结果
        review = self.reviewer.run(f"""
        任务：{task}
        执行结果：{result}
        
        请检查结果是否满足任务要求。如有问题，提出修改建议。""")
        
        # 4. 如需修正，反馈给执行 Agent
        if "需要修改" in review:
            revised_result = self.worker.run(f"根据以下反馈修改结果：{review}")
            return revised_result
        
        return result

# 使用示例
system = MultiAgentSystem()
result = system.solve("分析公司 Q3 销售数据，找出表现最好的产品和区域，生成 PPT 报告")
```

### 5.5.2 百炼平台 Agent 编排

阿里云百炼提供可视化的 Agent 编排工具：

```yaml
# agent_workflow.yaml
version: "1.0"
name: customer_service_agent

nodes:
  - id: intent_recognition
    type: llm
    model: qwen3.6-plus
    prompt: "判断用户意图：退款/咨询/投诉/其他"
    output_key: intent
  
  - id: refund_check
    type: condition
    condition: "${intent_recognition.intent} == '退款'"
    true_branch: handle_refund
    false_branch: consult_check
  
  - id: handle_refund
    type: tool
    tool: query_order_api
    params:
      order_id: "${user_input.order_id}"
  
  - id: consult_check
    type: condition
    condition: "${intent_recognition.intent} == '咨询'"
    true_branch: knowledge_search
    false_branch: human_handoff
  
  - id: knowledge_search
    type: rag
    knowledge_base: product_faq
    top_k: 3
  
  - id: human_handoff
    type: notification
    channel: dingtalk
    recipient: customer_service_team

triggers:
  - event: user_message
    entry_node: intent_recognition
```

---

## 本章小结

本章系统讲解了 Agent 应用的架构与实战：

1. **核心架构**：规划层、工具层、记忆层、感知层四层设计
2. **规划算法**：任务分解、ReAct、Plan-and-Solve 等主流方法
3. **工具调用**：Function Calling 机制、自定义工具封装
4. **记忆系统**：短期记忆管理上下文，长期记忆支持跨会话，摘要机制压缩历史
5. **多 Agent 协作**：角色分工、百炼平台可视化编排

Agent 代表了大模型应用的未来方向，从被动问答走向主动执行。技术决策者应提前布局，构建企业的 Agent 开发能力。

---

## 延伸阅读

1. [ReAct 论文](https://arxiv.org/abs/2210.03629)
2. [阿里云百炼 Agent 开发指南](https://help.aliyun.com/zh/model-studio/agent-development)
3. LangChain Agent 文档：https://python.langchain.com/docs/modules/agents/
4. 《Building Agentic AI Systems》- Stanford HAI

---

**下一章预告**：第 6 章将探讨大模型应用的安全与合规问题，包括内容安全、数据隐私、模型滥用防护、企业合规要求等关键议题。