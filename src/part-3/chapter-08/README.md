# 第8章：高级 Prompt 技巧

> 在掌握基础之上，本章介绍高级 Prompt 技巧，包括 Chain of Thought 思维链、Tree of Thought 树状思考、ReAct 推理框架、系统级 Prompt 设计等，帮助你充分发挥大模型的推理能力。

## 8.1 Chain of Thought（思维链）

### 8.1.1 什么是思维链？

**Chain of Thought（CoT）** 是一种引导大模型逐步推理的技术。通过让模型展示思考过程，不仅能得到更准确的答案，还能处理复杂的多步骤问题。

```
┌─────────────────────────────────────────────────────────────────┐
│                   思维链 vs 直接回答                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   直接回答：                                                    │
│   问题：30元买了5支笔，每支多少钱？                                │
│   答案：6元                                                     │
│                                                                  │
│   ─────────────────────────────────────────                     │
│                                                                  │
│   思维链：                                                      │
│   问题：30元买了5支笔，每支多少钱？                                │
│   思考：                                                        │
│   1. 总价 = 30元                                                │
│   2. 数量 = 5支                                                 │
│   3. 单价 = 总价 ÷ 数量 = 30 ÷ 5 = 6元                          │
│   答案：6元                                                     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 8.1.2 Zero-shot CoT

最简单的 CoT 只需要在问题后加一句"**Let's think step by step**"：

```python
# Zero-shot CoT 示例
zero_shot_cot = """
问题：小明有15个苹果，给了小红5个，又买了8个，现在有多少个苹果？

Let's think step by step.
"""

def solve_with_zero_shot_cot(problem: str) -> str:
    """使用零样本思维链解决问题"""
    prompt = f"""
{problem}

请一步一步地思考，然后给出答案。
"""
    return client.chat(prompt)["message"]

# 测试
problem = """
商店里有200件商品，第一天卖出了总数的1/4，
第二天卖出了剩余的1/3，
第三天又进货了50件，
现在商店里有多少件商品？
"""
result = solve_with_zero_shot_cot(problem)
print(result)
```

### 8.1.3 Few-shot CoT

提供完整的推理示例，让模型学习推理模式：

```python
# Few-shot CoT 示例
few_shot_cot = """
请按照以下示例的格式，逐步推理并给出答案。

示例1：
问题：小明有10元，买了3本练习本，每本2元，还剩多少钱？
推理：
- 练习本总价 = 3 × 2 = 6元
- 剩余金额 = 10 - 6 = 4元
答案：还剩4元

示例2：
问题：一个长方形长8厘米，宽5厘米，面积是多少？
推理：
- 长方形面积 = 长 × 宽
- 面积 = 8 × 5 = 40平方厘米
答案：40平方厘米

请解答：
问题：一辆汽车以60公里/小时的速度行驶了2.5小时，行驶了多少公里？
"""

def solve_with_few_shot_cot(problem: str, examples: list) -> str:
    """使用少样本思维链解决问题"""
    prompt = "请按照以下示例的格式，逐步推理并给出答案。\n\n"
    
    for i, ex in enumerate(examples, 1):
        prompt += f"示例{i}：\n"
        prompt += f"问题：{ex['question']}\n"
        prompt += f"推理：\n{ex['reasoning']}\n"
        prompt += f"答案：{ex['answer']}\n\n"
    
    prompt += f"请解答：\n问题：{problem}\n"
    
    return client.chat(prompt)["message"]
```

### 8.1.4 CoT 的适用场景

| 场景 | 效果 | 示例 |
|------|------|------|
| 数学计算 | ✅ 显著提升 | 应用题、几何计算 |
| 逻辑推理 | ✅ 显著提升 | 推理题、证明题 |
| 代码调试 | ✅ 显著提升 | Bug分析、修复建议 |
| 复杂决策 | ✅ 有提升 | 方案对比、风险评估 |
| 简单问答 | ❌ 无明显提升 | 事实查询、定义解释 |
| 创意写作 | ❌ 无需使用 | 写诗、写故事 |

```python
# 复杂推理示例
complex_reasoning_prompt = """
请逐步分析以下业务场景：

场景：某电商平台在"双11"期间推出促销活动
- 原价100元的商品打8折
- 再满100减20
- 使用10元红包
- 需要支付8元运费

问题：购买这件商品最终需要支付多少钱？

请按以下步骤分析：
1. 计算折后价
2. 计算满减后的价格
3. 计算红包抵扣后的价格
4. 计算最终支付金额（包含运费）

最后给出详细的计算过程和结果。
"""

def business_calculation(prompt: str) -> str:
    """复杂商业计算"""
    return client.chat(prompt)["message"]
```

## 8.2 Tree of Thought（思维树）

### 8.2.1 什么是思维树？

**Tree of Thought（ToT）** 是思维链的扩展，它不是线性推理，而是探索多条可能的思路，然后选择最佳路径：

```
┌─────────────────────────────────────────────────────────────────┐
│                     Tree of Thought 示意                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│                      ┌──────────────┐                            │
│                      │   问题起始    │                            │
│                      └──────┬───────┘                            │
│                             │                                    │
│              ┌──────────────┼──────────────┐                    │
│              ↓              ↓              ↓                     │
│         ┌────────┐    ┌────────┐     ┌────────┐                │
│         │ 思路A  │    │ 思路B  │     │ 思路C  │                │
│         └───┬────┘    └───┬────┘     └───┬────┘                │
│             │             │              │                       │
│         ┌───┴───┐     ┌───┴───┐      ┌───┴───┐                 │
│         ↓       ↓     ↓       ↓      ↓       ↓                  │
│      继续A1  回退A2  继续B1  回退B2  继续C1  回退C2              │
│         ↓                                                        │
│     ┌───────┴───────┐                                           │
│     │  评估：思路A最优 │                                           │
│     └───────────────┘                                           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 8.2.2 ToT 实现示例

```python
from typing import List, Dict, Callable
from dataclasses import dataclass, field

@dataclass
class Thought:
    """思维节点"""
    content: str
    parent: 'Thought' = None
    children: List['Thought'] = field(default_factory=list)
    score: float = 0.0
    depth: int = 0

class TreeOfThoughts:
    """思维树实现"""
    
    def __init__(self, client, max_depth: int = 3, num_branches: int = 2):
        self.client = client
        self.max_depth = max_depth
        self.num_branches = num_branches
    
    def expand_node(self, thought: Thought) -> List[Thought]:
        """扩展一个思维节点"""
        prompt = f"""
当前思路：{thought.content}

请提出{self.num_branches}个不同的后续思路方向。
每个方向都要有独特的推理路径。

格式：
思路1：[描述]
思路2：[描述]
"""
        response = self.client.chat(prompt)
        
        # 解析响应，生成新的思维节点
        branches = self._parse_branches(response["message"])
        
        new_thoughts = []
        for branch in branches:
            new_thought = Thought(
                content=branch,
                parent=thought,
                depth=thought.depth + 1
            )
            thought.children.append(new_thought)
            new_thoughts.append(new_thought)
        
        return new_thoughts
    
    def evaluate_node(self, thought: Thought) -> float:
        """评估一个思维节点的质量"""
        prompt = f"""
评估以下思路的质量（0-10分）：

思路：{thought.content}

评估标准：
1. 逻辑正确性（0-3分）
2. 完整性（0-3分）
3. 创新性（0-2分）
4. 可行性（0-2分）

只输出分数，如"8"。
"""
        response = self.client.chat(prompt)
        
        # 提取分数
        try:
            score = float(response["message"].strip())
        except:
            score = 5.0
        
        thought.score = score
        return score
    
    def solve(self, problem: str) -> Dict:
        """使用思维树解决问题"""
        # 创建根节点
        root = Thought(content=f"问题：{problem}")
        
        # 广度优先搜索
        frontier = [root]
        best_solution = None
        best_score = 0
        
        while frontier:
            # 扩展当前层的所有节点
            new_frontier = []
            
            for thought in frontier:
                if thought.depth >= self.max_depth:
                    # 评估叶节点
                    self.evaluate_node(thought)
                    if thought.score > best_score:
                        best_score = thought.score
                        best_solution = thought
                    continue
                
                # 扩展节点
                children = self.expand_node(thought)
                new_frontier.extend(children)
            
            frontier = new_frontier
        
        # 回溯找到最佳路径
        path = []
        current = best_solution
        while current:
            path.append(current.content)
            current = current.parent
        path.reverse()
        
        return {
            "solution": best_solution.content if best_solution else None,
            "score": best_score,
            "path": path,
            "tree": root
        }
    
    def _parse_branches(self, text: str) -> List[str]:
        """解析分支"""
        lines = text.strip().split('\n')
        branches = []
        
        for line in lines:
            if '思路' in line or '方向' in line:
                # 提取思路内容
                content = line.split('：')[-1].strip()
                if content:
                    branches.append(content)
        
        return branches[:self.num_branches]
```

### 8.2.3 ToT 应用示例

```python
def use_tot_for_decision():
    """使用思维树做商业决策"""
    tot = TreeOfThoughts(client, max_depth=3, num_branches=2)
    
    problem = """
一家创业公司面临产品方向选择：
A. 开发企业级SaaS产品，客单价高但获客难
B. 开发ToC产品，用户量大但变现难
C. 开发工具类产品，稳定但增长慢

请使用思维树方法分析这三种选择，
考虑市场、竞争、团队、资源等因素，
给出最终建议。
"""
    
    result = tot.solve(problem)
    
    print(f"最佳方案得分：{result['score']}/10")
    print("\n推理路径：")
    for i, step in enumerate(result['path'], 1):
        print(f"{i}. {step}")
    
    return result

# 运行
result = use_tot_for_decision()
```

## 8.3 ReAct 框架

### 8.3.1 什么是 ReAct？

**ReAct = Reasoning + Acting**，即"推理+行动"。它让模型交替进行推理和行动，适用于需要与外部环境交互的任务。

```
┌─────────────────────────────────────────────────────────────────┐
│                      ReAct 循环                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   ┌──────────────┐                                              │
│   │   推理       │                                              │
│   │ (Reasoning)  │                                              │
│   └──────┬───────┘                                              │
│          ↓                                                      │
│   ┌──────────────┐                                              │
│   │   行动       │                                              │
│   │  (Acting)    │──────► 外部工具/API                          │
│   └──────┬───────┘                                              │
│          ↓                                                      │
│   ┌──────────────┐                                              │
│   │   观察       │                                              │
│   │ (Observing) │◄────── 工具返回结果                           │
│   └──────┬───────┘                                              │
│          ↓                                                      │
│   ┌──────────────┐                                              │
│   │   继续推理？ │                                              │
│   └──────┬───────┘                                              │
│          │                                                      │
│     ┌────┴────┐                                                 │
│     ↓         ↓                                                 │
│    Yes        No                                                │
│     ↓         ↓                                                 │
│   继续      结束                                                │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 8.3.2 ReAct 实现

```python
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from enum import Enum

class ActionType(Enum):
    """可用的行动类型"""
    SEARCH = "search"
    CALCULATOR = "calculator"
    LOOKUP = "lookup"
    FINISH = "finish"

@dataclass
class Action:
    """行动"""
    tool: ActionType
    params: Dict[str, Any]
    thought: str  # 推理过程

@dataclass
class Step:
    """推理步骤"""
    step_num: int
    thought: str
    action: Action
    observation: str
    answer: Optional[str] = None

class ReActAgent:
    """ReAct 推理代理"""
    
    def __init__(self, client):
        self.client = client
        self.tools = self._init_tools()
    
    def _init_tools(self) -> Dict[ActionType, Callable]:
        """初始化工具"""
        return {
            ActionType.SEARCH: self._search,
            ActionType.CALCULATOR: self._calculate,
            ActionType.LOOKUP: self._lookup,
        }
    
    def think(self, context: str, max_steps: int = 5) -> List[Step]:
        """
        使用 ReAct 框架思考
        
        Args:
            context: 问题上下文
            max_steps: 最大推理步数
        
        Returns:
            推理步骤列表
        """
        history = []
        step_num = 0
        
        while step_num < max_steps:
            step_num += 1
            
            # 构建推理 Prompt
            prompt = self._build_thought_prompt(context, history)
            
            # 获取行动
            response = self.client.chat(prompt)
            action_text = response["message"]
            
            # 解析行动
            action = self._parse_action(action_text)
            
            if action is None:
                break
            
            if action.tool == ActionType.FINISH:
                # 完成任务
                history.append(Step(
                    step_num=step_num,
                    thought=action.thought,
                    action=action,
                    observation="任务完成",
                    answer=action.params.get("answer")
                ))
                break
            
            # 执行行动
            observation = self._execute_action(action)
            
            # 记录步骤
            history.append(Step(
                step_num=step_num,
                thought=action.thought,
                action=action,
                observation=observation
            ))
        
        return history
    
    def _build_thought_prompt(self, context: str, history: List[Step]) -> str:
        """构建推理 Prompt"""
        prompt = f"""
你是一个智能助手，需要通过推理和行动来回答问题。

## 当前问题
{context}

## 可用工具
- search: 搜索互联网获取实时信息
  参数：query (搜索关键词)
- calculator: 进行数学计算
  参数：expression (数学表达式)
- lookup: 查询本地知识库
  参数：query (查询内容)

## 历史步骤
"""
        
        for step in history:
            prompt += f"""
步骤{step.step_num}：
思考：{step.thought}
行动：{step.action.tool.value}({step.action.params})
观察：{step.observation}
"""
        
        prompt += """
## 输出格式
请按照以下格式输出你的推理和行动：

思考：[你的推理过程]
行动：[工具名](参数)
"""
        
        if not history:
            prompt += "\n\n不要使用finish工具，继续推理。"
        else:
            prompt += "\n\n如果问题已解决，使用 finish(answer='你的最终答案')"
        
        return prompt
    
    def _parse_action(self, text: str) -> Optional[Action]:
        """解析行动"""
        lines = text.strip().split('\n')
        
        thought = ""
        tool = None
        params = {}
        
        for line in lines:
            line = line.strip()
            if line.startswith("思考："):
                thought = line[3:].strip()
            elif line.startswith("行动："):
                action_str = line[3:].strip()
                if '(' in action_str and action_str.endswith(')'):
                    tool_name = action_str.split('(')[0].strip()
                    param_str = action_str.split('(')[1].rstrip(')')
                    
                    try:
                        # 简单解析参数
                        tool = ActionType(tool_name)
                        if param_str:
                            params = {"query": param_str.strip("'\"")}
                    except ValueError:
                        pass
        
        if tool:
            return Action(tool=tool, params=params, thought=thought)
        return None
    
    def _execute_action(self, action: Action) -> str:
        """执行行动"""
        tool = self.tools.get(action.tool)
        if tool:
            return tool(**action.params)
        return "未知工具"
    
    # 工具实现
    def _search(self, query: str) -> str:
        """搜索工具"""
        # 实际项目中调用真实搜索API
        return f"搜索'{query}'的结果：[模拟结果]"
    
    def _calculate(self, expression: str) -> str:
        """计算工具"""
        try:
            result = eval(expression)
            return f"计算结果：{result}"
        except:
            return "计算表达式无效"
    
    def _lookup(self, query: str) -> str:
        """查询工具"""
        return f"查询'{query}'的结果：[模拟结果]"
```

### 8.3.3 ReAct 应用示例

```python
def use_react_for_research():
    """使用 ReAct 进行研究"""
    agent = ReActAgent(client)
    
    question = """
2024年诺贝尔物理学奖获得者是谁？
他们的主要贡献是什么？
"""
    
    steps = agent.think(question, max_steps=3)
    
    print("推理过程：")
    for step in steps:
        print(f"\n【步骤 {step.step_num}】")
        print(f"思考：{step.thought}")
        print(f"行动：{step.action.tool.value}({step.action.params})")
        print(f"观察：{step.observation}")
        if step.answer:
            print(f"答案：{step.answer}")
    
    return steps

def use_react_for_calculation():
    """使用 ReAct 进行复杂计算"""
    agent = ReActAgent(client)
    
    question = """
某公司2023年收入1000万元，年增长率20%
2024年收入是多少？2023-2024两年累计收入是多少？
"""
    
    steps = agent.think(question, max_steps=3)
    
    print("推理过程：")
    for step in steps:
        print(f"\n【步骤 {step.step_num}】")
        print(f"思考：{step.thought}")
        print(f"观察：{step.observation}")
        if step.answer:
            print(f"答案：{step.answer}")
```

## 8.4 System Prompt 设计

### 8.4.1 System Prompt vs User Prompt

```
┌─────────────────────────────────────────────────────────────────┐
│                   Prompt 层级架构                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    System Prompt                         │   │
│  │  定义AI的身份、行为规则、能力边界                         │   │
│  │  适用于所有对话，一次设置，持久生效                       │   │
│  └─────────────────────────────────────────────────────────┘   │
│                            ↓                                    │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                   User Prompt                           │   │
│  │  用户输入的具体问题或指令                                 │   │
│  │  每轮对话都需要提供                                      │   │
│  └─────────────────────────────────────────────────────────┘   │
│                            ↓                                    │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    AI Response                         │   │
│  │  AI根据System和User Prompt生成的回复                     │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 8.4.2 System Prompt 核心组件

```python
# 高质量的 System Prompt 示例
SYSTEM_PROMPT_TEMPLATE = """
## 身份定义
你是一个[角色名称]，专注于[专业领域]。
你有[X]年的[相关]经验，擅长[具体技能]。

## 核心能力
1. [能力1]
2. [能力2]
3. [能力3]

## 工作原则
1. [原则1]：...
2. [原则2]：...
3. [原则3]：...

## 输出风格
- 语言：[正式/专业/友好/简洁]
- 格式：[结构化/自由]
- 长度：[简短/中等/详细]

## 约束条件
- 不知道就说不知道，不要编造
- 不涉及[敏感话题]
- 不提供[特定限制]

## 示例交互
用户：[示例问题]
你：[示例回答]
"""

# 实际示例：Python教学助手
PYTHON_TUTOR_PROMPT = """
## 身份定义
你是一位资深Python开发者，拥有10年的Python教学经验。
你擅长用通俗易懂的语言解释复杂的概念，
并且能够根据学习者的水平调整讲解深度。

## 核心能力
1. 解释Python概念和语法
2. 分析和优化Python代码
3. 调试和修复代码Bug
4. 指导编程最佳实践

## 工作原则
1. **循序渐进**：从基础开始，逐步深入
2. **实践导向**：每个概念都配合代码示例
3. **因材施教**：根据用户水平调整解释深度
4. **鼓励探索**：引导用户自己思考，而非直接给答案

## 输出风格
- 语言：友好、专业、易懂
- 格式：Markdown代码块
- 长度：根据问题复杂度调整，简单问题简洁回答

## 约束条件
- 不直接给答案，引导用户自己思考
- 代码示例必须有注释
- 涉及高级特性时提醒用户注意版本兼容性
- 如果代码有安全漏洞必须明确指出

## 示例交互
用户：什么是装饰器？
你：
装饰器是Python中一个强大的特性。
让我用一个生活中的例子来解释：

想象你有一封信（函数），你想要：
1. 保留信的内容
2. 但在信封上添加一些功能，比如加密、签名

装饰器就像是一个"信封包装机"，它包裹原函数，
在不改变原函数内容的情况下，添加新功能。

代码示例：
```python
def my_decorator(func):
    def wrapper():
        print("装饰器添加的功能")
        return func()
    return wrapper

@my_decorator
def hello():
    print("Hello!")
```

你想了解装饰器的哪些方面？
"""
```

### 8.4.3 动态 System Prompt

```python
class DynamicSystemPrompt:
    """动态 System Prompt"""
    
    SYSTEM_PROMPT_BASE = """
你是一个智能助手，正在与用户进行对话。
"""
    
    ROLE_TEMPLATES = {
        "python_expert": """
你是一位Python专家，专注于：
1. Python语法和最佳实践
2. 代码审查和优化
3. Python标准库和第三方库推荐

回答时：
- 提供可运行的代码示例
- 解释代码的工作原理
- 指出常见的陷阱和错误
""",
        
        "math_teacher": """
你是一位数学老师，擅长：
1. 解释数学概念
2. 逐步推导公式
3. 提供解题技巧

回答时：
- 清晰展示推导过程
- 解释每一步的数学原理
- 提供多种解法（如果有）
""",
        
        "writing_assistant": """
你是一位专业写作助手，擅长：
1. 文章润色和改进
2. 不同风格的写作
3. 中英互译

回答时：
- 保持原文风格和意图
- 提供修改建议和理由
- 可以给出多个版本供参考
"""
    }
    
    def get_prompt(self, role: str, user_level: str = "intermediate") -> str:
        """获取适合的 System Prompt"""
        role_prompt = self.ROLE_TEMPLATES.get(role, "")
        
        level_prompt = f"""
用户水平：{user_level}
根据用户水平调整解释的深度和速度。
"""
        
        return self.SYSTEM_PROMPT_BASE + role_prompt + level_prompt

def create_role_based_assistant(role: str, level: str = "intermediate"):
    """创建基于角色的助手"""
    prompt_builder = DynamicSystemPrompt()
    system_prompt = prompt_builder.get_prompt(role, level)
    
    def chat(user_input: str) -> str:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input}
        ]
        return client.chat("", messages=messages)["message"]
    
    return chat

# 使用示例
python_tutor = create_role_based_assistant("python_expert")
math_teacher = create_role_based_assistant("math_teacher", "beginner")

print(python_tutor("什么是生成器？"))
print(math_teacher("解释一下微积分的基本概念"))
```

### 8.4.4 System Prompt 优化

```python
# System Prompt 检查清单
SYSTEM_PROMPT_CHECKLIST = """
## System Prompt 优化检查清单

### 1. 身份清晰度
☐ 是否明确定义了AI的身份？
☐ 身份是否符合目标使用场景？
☐ 身份描述是否过于宽泛或狭窄？

### 2. 能力边界
☐ 是否列出了AI的核心能力？
☐ 是否明确了AI不擅长或不能做的事情？
☐ 能力描述是否与实际模型能力匹配？

### 3. 输出格式
☐ 是否指定了输出格式（如Markdown、JSON）？
☐ 是否有长度限制？
☐ 是否提供了示例输出？

### 4. 约束条件
☐ 是否包含了安全/合规约束？
☐ 是否有质量标准（如"不知道就说不知道"）？
☐ 约束是否过于严格导致功能受限？

### 5. 实用性
☐ Prompt长度是否适中（过长会影响性能）？
☐ 指令是否清晰、可执行？
☐ 是否提供了Few-shot示例？

### 6. 可测试性
☐ 是否有明确的质量评判标准？
☐ 是否可以量化评估效果？
☐ 是否有回归测试用例？
"""

def optimize_system_prompt(current_prompt: str) -> str:
    """优化 System Prompt"""
    analysis = client.chat(f"""
请分析以下 System Prompt，识别问题并提供改进建议：

{current_prompt}

请按以下格式输出：

## 问题分析
1. [问题1]
2. [问题2]

## 改进建议
1. [建议1]
2. [建议2]

## 优化后的版本
```[优化后的System Prompt]
```
""")
    return analysis["message"]
```

## 8.5 Prompt 组合策略

### 8.5.1 任务分解与组合

```python
class TaskDecomposer:
    """任务分解器"""
    
    def __init__(self, client):
        self.client = client
    
    def decompose(self, task: str) -> List[str]:
        """将复杂任务分解为简单子任务"""
        prompt = f"""
请将以下任务分解为3-5个简单的子任务：

任务：{task}

要求：
1. 每个子任务应该可以独立完成
2. 子任务之间有明确的依赖关系
3. 按执行顺序列出

格式：
1. [子任务1]
2. [子任务2]
...
"""
        response = self.client.chat(prompt)
        
        # 解析子任务
        tasks = []
        for line in response["message"].split('\n'):
            line = line.strip()
            if line and line[0].isdigit():
                task = line.split('.', 1)[-1].strip()
                tasks.append(task)
        
        return tasks
    
    def execute_sequential(self, task: str) -> str:
        """顺序执行分解后的子任务"""
        subtasks = self.decompose(task)
        
        results = []
        context = ""
        
        for i, subtask in enumerate(subtasks, 1):
            print(f"执行子任务 {i}/{len(subtasks)}: {subtask}")
            
            prompt = f"""
基于之前的任务执行结果：
{context}

当前子任务：{subtask}

请执行这个子任务。
"""
            result = self.client.chat(prompt)
            results.append({
                "task": subtask,
                "result": result["message"]
            })
            context += f"\n\n[子任务{i}]: {subtask}\n结果: {result['message']}"
        
        return results

# 使用示例
decomposer = TaskDecomposer(client)
task = "为我分析竞品并制定差异化策略"

results = decomposer.execute_sequential(task)

for r in results:
    print(f"\n=== {r['task']} ===")
    print(r['result'])
```

### 8.5.2 Prompt 链（Chain of Prompts）

```python
class PromptChain:
    """Prompt 链：多个 Prompt 串联执行"""
    
    def __init__(self, client):
        self.client = client
        self.steps = []
    
    def add_step(self, name: str, prompt_template: str, 
                 extract_key: str = None):
        """
        添加 Prompt 步骤
        
        Args:
            name: 步骤名称
            prompt_template: Prompt模板，支持{previous_result}占位符
            extract_key: 从结果中提取的字段名
        """
        self.steps.append({
            "name": name,
            "prompt_template": prompt_template,
            "extract_key": extract_key
        })
    
    def execute(self, initial_input: str) -> Dict:
        """执行 Prompt 链"""
        results = {}
        current_result = initial_input
        
        for step in self.steps:
            # 填充模板
            prompt = step["prompt_template"].format(
                previous_result=current_result,
                **results  # 可使用之前步骤的结果
            )
            
            # 执行
            response = self.client.chat(prompt)
            step_result = response["message"]
            
            # 存储结果
            results[step["name"]] = step_result
            
            # 提取特定字段（如果有）
            if step["extract_key"] and step["extract_key"] in step_result:
                current_result = step_result[step["extract_key"]]
            else:
                current_result = step_result
        
        return {
            "all_results": results,
            "final_result": current_result
        }

# 示例：文章处理流程
def article_processing_chain():
    """文章处理 Prompt 链"""
    chain = PromptChain(client)
    
    # Step 1: 提取关键信息
    chain.add_step(
        "extract_info",
        """从以下文章中提取关键信息：
        
        {previous_result}
        
        提取以下信息（JSON格式）：
        - title: 标题
        - author: 作者
        - main_points: 3个主要观点
        - keywords: 关键词（5个）
        """
    )
    
    # Step 2: 生成摘要
    chain.add_step(
        "summarize",
        """基于以下关键信息，生成一篇100字的摘要：
        
        {previous_result}
        """
    )
    
    # Step 3: 生成标签
    chain.add_step(
        "tagging",
        """基于文章内容，生成适合的标签：
        
        标题：{extract_info['title']}
        关键词：{extract_info['keywords']}
        
        生成3-5个标签，每个标签不超过5个字。
        """
    )
    
    # Step 4: 生成推荐语
    chain.add_step(
        "recommendation",
        """基于以下内容，生成一句话推荐语（用于分享）：
        
        标题：{extract_info['title']}
        主要观点：{extract_info['main_points']}
        
        推荐语要求：
        - 吸引人点击
        - 不超过30字
        - 不剧透
        """
    )
    
    return chain.execute

# 使用
process_article = article_processing_chain()
article = """
[原始文章内容]...
"""

result = process_article(article)
print("处理结果：")
for key, value in result["all_results"].items():
    print(f"\n【{key}】")
    print(value)
```

### 8.5.3 并行 Prompt 处理

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

class ParallelPromptProcessor:
    """并行 Prompt 处理"""
    
    def __init__(self, client, max_workers: int = 3):
        self.client = client
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
    
    def process_multiple(self, prompts: List[str]) -> List[str]:
        """并行处理多个 Prompt"""
        futures = [
            self.executor.submit(self.client.chat, prompt)
            for prompt in prompts
        ]
        
        results = []
        for future in futures:
            try:
                result = future.result()
                results.append(result["message"])
            except Exception as e:
                results.append(f"Error: {str(e)}")
        
        return results
    
    def batch_analyze(self, items: List[str], analysis_prompt: str) -> List[str]:
        """
        批量分析多个项目
        
        Args:
            items: 待分析项目列表
            analysis_prompt: 分析 Prompt 模板，{item} 为占位符
        """
        prompts = [
            analysis_prompt.format(item=item)
            for item in items
        ]
        
        return self.process_multiple(prompts)

# 使用示例
def parallel_usage():
    processor = ParallelPromptProcessor(client, max_workers=3)
    
    # 批量代码审查
    code_snippets = [
        "def add(a, b): return a + b",
        "def subtract(a, b): return a - b",
        "def multiply(a, b): return a * b"
    ]
    
    review_prompt = """请审查以下Python代码：
    {item}
    
    审查维度：正确性、风格、安全性
    """
    
    reviews = processor.batch_analyze(code_snippets, review_prompt)
    
    for snippet, review in zip(code_snippets, reviews):
        print(f"\n代码: {snippet}")
        print(f"审查: {review}")
    
    return reviews
```

## 8.6 高级技巧实战

### 8.6.1 结构化输出（JSON Mode）

```python
# 强制 JSON 输出
JSON_MODE_PROMPT = """
请将以下信息转换为JSON格式。

信息：
- 姓名：张三
- 年龄：28
- 职业：软件工程师
- 技能：Python, Java, JavaScript

要求：
- 必须输出有效的JSON
- 使用中文key
- 不要输出任何解释
- 不要使用markdown代码块

JSON格式参考：
{
    "姓名": "...",
    "年龄": ...,
    "职业": "...",
    "技能": [...]
}
"""

# 使用 Qwen 的 JSON Mode
def structured_output(prompt: str, schema: dict = None) -> dict:
    """结构化输出"""
    from dashscope import Generation
    
    # 构建带格式要求的 Prompt
    formatted_prompt = f"""
{prompt}

请严格按照以下JSON Schema输出：
{json.dumps(schema, ensure_ascii=False, indent=2)}

只输出JSON，不要有任何其他文字。
"""
    
    response = Generation.call(
        model="qwen-max",
        messages=[
            {"role": "user", "content": formatted_prompt}
        ],
        result_format="message"
    )
    
    # 解析 JSON
    try:
        return json.loads(response.output.choices[0].message.content)
    except json.JSONDecodeError:
        return {"error": "JSON解析失败", "raw": response.output.choices[0].message.content}

# 使用示例
schema = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "age": {"type": "integer"},
        "skills": {
            "type": "array",
            "items": {"type": "string"}
        }
    },
    "required": ["name", "age", "skills"]
}

result = structured_output("提取姓名、年龄和技能", schema)
print(result)
```

### 8.6.2 自我一致性（Self-Consistency）

```python
# 多次采样，选择最一致的答案
def self_consistency(prompt: str, n_samples: int = 5) -> str:
    """
    自我一致性：多次采样，选择最常见的答案
    
    Args:
        prompt: 原始问题
        n_samples: 采样次数
    
    Returns:
        最一致的答案
    """
    from collections import Counter
    
    # 生成多个解答
    answers = []
    for _ in range(n_samples):
        response = client.chat(
            f"{prompt}\n\n请给出你的最终答案。"
        )
        answers.append(response["message"].strip())
    
    # 统计最常见的答案
    counter = Counter(answers)
    most_common = counter.most_common(1)[0]
    
    return {
        "answer": most_common[0],
        "confidence": most_common[1] / n_samples,
        "all_answers": answers,
        "distribution": dict(counter)
    }

# 示例
result = self_consistency(
    "一个盒子有10个红球和5个蓝球，"
    "随机抽取3个球，至少有1个红球的概率是多少？",
    n_samples=5
)

print(f"最一致答案: {result['answer']}")
print(f"置信度: {result['confidence']:.0%}")
print(f"答案分布: {result['distribution']}")
```

### 8.6.3 反思与验证

```python
def reflective_reasoning(problem: str) -> Dict:
    """
    反思推理：生成答案，然后验证和修正
    
    1. 初始解答
    2. 自我验证
    3. 如有问题，修正
    4. 最终确认
    """
    # Step 1: 初始解答
    initial = client.chat(f"""
问题：{problem}

请详细解答这个问题。
""")
    
    # Step 2: 自我验证
    verification = client.chat(f"""
你刚刚给出了以下解答：

{initial['message']}

请验证这个解答是否正确：
1. 逻辑是否严密？
2. 是否有遗漏的关键点？
3. 答案是否正确？

如果有问题，说明问题并给出修正后的解答。
如果正确，确认答案。
""")
    
    # Step 3: 最终输出
    if "正确" in verification["message"] or "没有问题" in verification["message"]:
        return {
            "answer": initial["message"],
            "verified": True,
            "verification": verification["message"]
        }
    else:
        return {
            "answer": verification["message"],
            "verified": False,
            "verification": verification["message"]
        }

# 示例
result = reflective_reasoning(
    "如果x + 5 = 12，那么x的平方是多少？"
)
print(result["answer"])
```

## 本章小结

本章介绍了高级 Prompt 技巧：

1. **Chain of Thought（思维链）**：通过引导模型逐步推理，提升复杂任务的准确性
2. **Tree of Thought（思维树）**：探索多条推理路径，选择最佳方案
3. **ReAct 框架**：结合推理与行动，适用于需要外部工具的任务
4. **System Prompt 设计**：定义AI身份、能力边界和输出规范
5. **Prompt 组合策略**：任务分解、Prompt链、并行处理
6. **高级技巧实战**：JSON Mode、自我一致性、反思验证

掌握这些技巧，你将能够构建更加智能、可靠的 AI 应用。

---

## 思考与练习

1. **概念理解**：对比 Chain of Thought 和 Tree of Thought 的适用场景。

2. **实践练习**：为以下场景设计 ReAct Agent：
   - 天气查询助手
   - 股票分析机器人
   - 旅行规划助手

3. **System Prompt 优化**：为你的应用场景设计一个完整的 System Prompt，包含身份、能力、约束和示例。

4. **代码实现**：实现一个简单的 Chain of Thought 处理器，并测试在不同类型问题上的效果。

5. **对比实验**：使用同一个问题，分别测试 Zero-shot、Few-shot、CoT 三种方式的效果和效率。

6. **综合应用**：设计一个 AI 助手，能够：
   - 理解用户意图
   - 分解复杂任务
   - 使用工具获取信息
   - 整合信息给出完整答案
