# 第7章：Prompt 工程基础

> Prompt（提示词）是大模型理解用户意图的桥梁。好的 Prompt 可以让模型准确理解需求，输出高质量的结果；糟糕的 Prompt 则可能导致答非所问。本章从零讲解 Prompt 工程的核心概念和基础技巧。

## 7.1 什么是 Prompt？

### 7.1.1 重新认识 Prompt

**Prompt（提示词）** 是用户与大模型交互时输入的文本内容。它告诉模型：

- **任务是什么**：让模型完成什么任务
- **背景信息**：完成任务需要知道什么
- **输出要求**：结果应该是什么格式、什么风格

```
┌─────────────────────────────────────────────────────────────────┐
│                        Prompt = 任务指令                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   用户 ──► [任务描述 + 背景信息 + 输出要求] ──► 大模型 ──► 输出   │
│                                                                  │
│   Prompt = 让模型理解"做什么"+"怎么做"的全部信息                   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 7.1.2 Prompt 的重要性

> "The way you phrase the problem determines how AI solves it."

同样的问题，不同的 Prompt 可能导致截然不同的结果：

| Prompt 版本 | 输出质量 |
|-------------|----------|
| ❌ "写一首诗" | 可能是一首平庸的通用诗 |
| ✅ "写一首关于秋天的七言绝句，要求意境深远、押韵工整" | 更符合期望的高质量诗作 |

**Prompt 工程的价值**：

1. **提升准确性**：让模型准确理解任务意图
2. **控制输出格式**：获得结构化的、可程序化的结果
3. **降低成本**：简洁准确的 Prompt 减少 token 消耗
4. **增强稳定性**：减少随机性带来的不确定性

### 7.1.3 Prompt 的基本结构

一个完整的 Prompt 通常包含以下部分：

```
┌─────────────────────────────────────────────────────────────────┐
│                      Prompt 基本结构                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────┐                                                │
│  │ 角色定义     │ 你是一个资深Python工程师，擅长写出优雅的代码    │
│  └─────────────┘                                                │
│        ↓                                                         │
│  ┌─────────────┐                                                │
│  │ 任务描述     │ 请帮我审查以下代码                               │
│  └─────────────┘                                                │
│        ↓                                                         │
│  ┌─────────────┐                                                │
│  │ 背景信息     │ 代码用于处理用户登录逻辑                         │
│  └─────────────┘                                                │
│        ↓                                                         │
│  ┌─────────────┐                                                │
│  │ 示例输出     │ 你的输出应该包含：1) 问题列表 2) 建议 3) 代码   │
│  └─────────────┘                                                │
│        ↓                                                         │
│  ┌─────────────┐                                                │
│  │ 约束条件     │ 不要修改原有逻辑，只提出优化建议                  │
│  └─────────────┘                                                │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## 7.2 Prompt 的核心要素

### 7.2.1 角色定义（Role）

给模型设定一个角色，可以显著提升输出质量：

```python
# ❌ 没有角色定义
prompt = "如何提高代码质量？"

# ✅ 有角色定义
prompt = "作为一位有10年经验的高级架构师，请分享提高代码质量的最佳实践。"
```

**角色定义的作用**：

- 限定回答的专业角度
- 激活模型的"专业知识"
- 调整输出的语气和风格

```python
# 不同角色的输出风格对比
prompts = {
    "技术面试官": "你是一位技术面试官，面试一位应聘高级Python开发的候选人。请提出3个关于并发编程的问题。",
    "技术讲师": "你是一位Python讲师，用通俗易懂的方式解释什么是并发编程，并给出代码示例。",
    "代码审查员": "你是一位严格的代码审查员，请指出以下代码中可能存在的并发问题..."
}

for role, prompt in prompts.items():
    print(f"\n=== {role} ===")
    print(f"Prompt: {prompt[:30]}...")
```

### 7.2.2 任务描述（Task）

清晰、具体地描述你想要完成的任务：

```python
# ❌ 模糊的任务描述
prompt = "帮我写代码"

# ✅ 清晰的任务描述
prompt = """
请帮我写一个Python函数，实现以下功能：
1. 输入：用户ID（字符串）
2. 处理：从数据库查询该用户的最近10条订单
3. 输出：JSON格式的订单列表
4. 错误处理：如果用户不存在，返回空列表
"""

# ✅ 更具体的任务描述
prompt = """
请写一个装饰器函数 @retry(max_attempts=3, delay=1)，实现以下功能：
- 被装饰的函数执行失败时，自动重试
- 最多重试 max_attempts 次
- 每次重试间隔 delay 秒
- 记录每次失败的错误信息
- 重试失败后抛出原始异常
"""
```

**任务描述的最佳实践**：

1. **使用动词开头**：明确表达需要的动作
2. **分点列举**：复杂任务拆分成多个子任务
3. **包含输入输出**：说明期望的数据格式

### 7.2.3 背景信息（Context）

提供必要的上下文，帮助模型理解任务的特殊要求：

```python
# ❌ 缺少背景信息
prompt = "这段代码有什么问题？"

# ✅ 提供背景信息
prompt = """
我们的系统是一个电商订单处理模块，每秒处理约1000个订单。
当前使用同步处理方式，偶尔会出现超时。
这是订单创建的代码：

def create_order(order_data):
    # 创建订单
    order = Order.objects.create(**order_data)
    # 发送通知邮件
    send_email(order.customer_email)
    # 更新库存
    update_inventory(order.items)
    return order

请问这段代码有什么性能和可靠性问题？请给出优化建议。
"""
```

### 7.2.4 输出格式（Format）

明确指定期望的输出格式：

```python
# 指定JSON格式
prompt_json = """
将以下产品信息转换为JSON格式：

产品名：iPhone 15 Pro
价格：7999元
颜色：深空黑
存储：256GB

要求：
- JSON格式规范
- 使用中文key
- 包含所有属性
"""

# 指定表格格式
prompt_table = """
请以表格形式列出Python中的5种数据结构，包括：
| 数据结构 | 创建方式 | 特点 | 适用场景 |
"""

# 指定列表格式
prompt_list = """
请列出安装Python的5种方法，每种方法用一行描述。
格式：[方法名] - [简要说明]
"""

# 指定步骤格式
prompt_steps = """
解释HTTP请求的工作流程。
请按以下格式回答：
第一步：...
第二步：...
第三步：...
"""
```

## 7.3 Zero-shot 与 Few-shot

### 7.3.1 Zero-shot Prompting

**Zero-shot**（零样本）是指不给模型任何示例，直接描述任务：

```python
# Zero-shot 示例
zero_shot_prompts = [
    # 分类
    "将以下评论分类为正面或负面：'这个产品太棒了，完全超出预期！'",
    
    # 翻译
    "把以下中文翻译成英文：今天天气真好",
    
    # 摘要
    "用一句话概括：人工智能技术正在快速发展，...",
    
    # 问答
    "问：什么是云计算？答：",
]

def test_zero_shot(prompt):
    """测试零样本学习"""
    response = client.chat(prompt)
    return response["message"]
```

**Zero-shot 的适用场景**：

- 简单、明确的任务
- 模型已经具备相关知识
- 需要快速得到答案

### 7.3.2 Few-shot Prompting

**Few-shot**（少样本）是指在 Prompt 中提供几个示例，帮助模型理解任务：

```python
# Few-shot 示例
few_shot_prompt = """
请根据评论内容，判断用户的情感是正面还是负面。

示例：
评论："这家餐厅的服务太差了，等了1小时才上菜" → 负面
评论："电影很精彩，笑中带泪，推荐观看" → 正面

请判断：
评论："这个课程讲解清晰，干货满满" →
"""

# 多示例 Few-shot
multi_shot_prompt = """
将中文成语翻译成英文：

画蛇添足 → to add unnecessary details
掩耳盗铃 → to deceive oneself
守株待兔 → to wait for gains without pains

请翻译：
亡羊补牢 →
"""
```

**Few-shot 的优势**：

1. **提升准确性**：示例帮助模型理解具体要求
2. **控制输出格式**：示例本身就是格式说明
3. **处理边缘情况**：通过示例明确复杂规则

```python
# Few-shot vs Zero-shot 对比
def compare_shot_approaches():
    """对比零样本和少样本的效果"""
    
    # 零样本
    zero_shot = """
    判断以下文本的情感是正面还是负面：
    "物流很快，但产品有瑕疵"
    """
    
    # 少样本
    few_shot = """
    判断以下文本的情感是正面、负面还是中性：
    
    "服务超级好，下次还会来" → 正面
    "等了两周才收到，太慢了" → 负面
    "产品还可以，就是包装有点简陋" → 中性
    
    "物流很快，但产品有瑕疵" →
    """
    
    print("Zero-shot 结果可能：负面（只关注问题）")
    print("Few-shot 结果更可能是：中性（两个观点各占一半）")
```

### 7.3.3 如何选择

| 场景 | 推荐方式 | 说明 |
|------|----------|------|
| 简单分类/翻译 | Zero-shot | 模型本身能力足够强 |
| 格式复杂多变 | Few-shot | 示例直接说明格式要求 |
| 领域特殊术语 | Few-shot | 示例帮助理解术语含义 |
| 边界情况处理 | Few-shot | 示例说明边界判断标准 |

## 7.4 结构化 Prompt 模板

### 7.4.1 为什么需要结构化模板？

在实际应用中，我们通常需要反复使用相同类型的 Prompt。**结构化模板**可以让 Prompt 更易维护、更易复用：

```python
# ❌ 散乱的 Prompt
bad_prompts = [
    "你是一个Python专家，请解释什么是装饰器",
    "作为资深Python开发者，请告诉我装饰器的工作原理",
    "我是Python初学者，请用简单的语言介绍装饰器",
]

# ✅ 结构化模板
class PromptTemplate:
    """Prompt 模板类"""
    
    def __init__(self, template: str):
        self.template = template
    
    def format(self, **kwargs) -> str:
        """格式化模板"""
        return self.template.format(**kwargs)

# 定义模板
code_explainer = PromptTemplate("""
你是一位专业的{language}开发者。

请用{level}的语言解释以下{concept}概念：

{code}

要求：
- 解释清晰易懂
- 包含实际应用场景
- 适当使用比喻
""")

# 使用模板
prompt = code_explainer.format(
    language="Python",
    level="入门级",
    concept="装饰器",
    code="""
def timer(func):
    def wrapper(*args, **kwargs):
        import time
        start = time.time()
        result = func(*args, **kwargs)
        print(f"执行时间: {time.time() - start}s")
        return result
    return wrapper
    """
)
```

### 7.4.2 Jinja2 模板引擎

更复杂的模板可以使用 Jinja2：

```python
from jinja2 import Template

# 定义 Prompt 模板
CODE_REVIEW_TEMPLATE = """
{%- macro review_item(issue, severity, suggestion) -%}
【{{ severity }}】{{ issue }}
建议：{{ suggestion }}
{%- endmacro %}

## 代码审查报告

代码来源：{{ file_path }}
审查时间：{{ review_time }}

{% if issues %}
发现 {{ issues|length }} 个问题：

{% for issue in issues %}
### 问题 {{ loop.index }}
{{ review_item(issue.description, issue.severity, issue.suggestion) }}

```{{ issue.language }}
{{ issue.code_snippet }}
```
{% endfor %}
{% else %}
✅ 未发现问题
{% endif %}

---
审查人：{{ reviewer }}
"""

def generate_review_prompt(issues: list) -> str:
    """生成代码审查 Prompt"""
    template = Template(CODE_REVIEW_TEMPLATE)
    return template.render(
        file_path="src/main.py",
        review_time="2024-01-15",
        issues=issues,
        reviewer="AI代码审查助手"
    )

# 使用示例
issues = [
    {
        "description": "未进行输入验证",
        "severity": "高危",
        "suggestion": "添加参数校验，处理空值和异常格式",
        "language": "python",
        "code_snippet": "user_id = request.params['user_id']"
    }
]

prompt = generate_review_prompt(issues)
print(prompt)
```

### 7.4.3 常用 Prompt 模板库

```python
# 常用模板集合
PROMPT_TEMPLATES = {
    "summarize": {
        "description": "文本摘要",
        "template": """
请将以下文本压缩成{length}字以内的摘要：

{text}

摘要应该：
- 保留核心信息
- 语言简洁流畅
- 不包含原始文本中没有的信息
"""
    },
    
    "translate": {
        "description": "翻译助手",
        "template": """
请将以下{source_lang}文本翻译成{target_lang}：

{text}

翻译要求：
- 准确传达原文含义
- 符合目标语言习惯
- 适当本地化（如有必要）
"""
    },
    
    "classify": {
        "description": "文本分类",
        "template": """
请将以下文本分类到 {categories} 中：

文本：{text}

请只输出分类标签，不需要解释。
"""
    },
    
    "qa": {
        "description": "问答助手",
        "template": """
基于以下背景信息回答问题：

【背景】
{context}

【问题】
{question}

回答要求：
- 基于背景信息
- 如信息不足，请明确说明
- 回答简洁明了
"""
    },
    
    "rewrite": {
        "description": "文本改写",
        "template": """
请将以下文本改写成{style}风格：

原文：
{text}

改写要求：
- 保持原意
- 风格：{style}
- 长度：约{length}
"""
    }
}

def use_template(name: str, **kwargs) -> str:
    """使用模板生成 Prompt"""
    template = PROMPT_TEMPLATES.get(name)
    if not template:
        raise ValueError(f"未知模板: {name}")
    
    return template["template"].format(**kwargs)

# 使用示例
prompt = use_template(
    "summarize",
    length="100",
    text="人工智能技术正在快速发展..."
)
```

## 7.5 Prompt 编写最佳实践

### 7.5.1 清晰具体的指令

```python
# ❌ 模糊的指令
bad = "介绍一下Python"

# ✅ 清晰的指令
good = """
请介绍Python编程语言，包括：
1. Python的设计理念和特点
2. Python的主要应用领域（至少5个）
3. Python与其他语言相比的优势
4. 适合学习Python的人群

请用通俗易懂的语言，适合编程初学者阅读。
"""

# ✅ 更进一步的清晰指令
better = """
## 任务
写一篇面向编程初学者的Python介绍文章。

## 要求
- 字数：800-1000字
- 语言：通俗易懂，避免过多专业术语
- 结构：包含引言、主体（3-4个要点）、总结

## 必须包含的内容
1. Python是什么
2. Python能做什么（举3个实际例子）
3. 为什么选择Python
4. 如何开始学习Python

## 禁止出现的内容
- 不要使用过多技术术语（必须解释的除外）
- 不要写代码示例（这是入门介绍）
- 不要超过1000字
"""
```

### 7.5.2 分解复杂任务

```python
# ❌ 一次性要求所有内容
complex_prompt = """
请写一份完整的产品分析报告，包括：
1. 市场分析
2. 竞品分析
3. 用户调研
4. 产品功能规划
5. 商业模式
6. 财务预测
7. 风险评估
"""

# ✅ 分解为多个步骤
def multi_step_analysis(product):
    """分步骤产品分析"""
    prompts = [
        {
            "step": 1,
            "task": "市场分析",
            "prompt": f"""
请分析"{product}"所在市场的以下方面：
1. 市场规模和增长率
2. 市场趋势
3. 主要玩家

输出格式：
## 市场规模
...
## 市场趋势
...
## 主要玩家
...
"""
        },
        {
            "step": 2,
            "task": "竞品分析",
            "prompt": """
基于上一部分的市场分析，
请分析主要竞品的：
1. 核心功能
2. 差异化优势
3. 定价策略

输出格式：
## 竞品A
...
## 竞品B
...
"""
        },
        {
            "step": 3,
            "task": "SWOT分析",
            "prompt": """
基于前面的市场分析和竞品分析，
请对"{product}"进行SWOT分析。

输出格式：
## 优势 (S)
## 劣势 (W)
## 机会 (O)
## 威胁 (T)
"""
        }
    ]
    
    results = []
    for p in prompts:
        result = client.chat(p["prompt"])
        results.append({"step": p["step"], "task": p["task"], "content": result})
    
    return results
```

### 7.5.3 使用分隔符组织结构

```python
# 使用 Markdown 分隔符
prompt_with_delimiters = """
请分析以下代码并进行代码审查。

---
## 代码
```python
def calculate(a, b):
    return a + b
```

---
## 审查要求
1. 检查代码正确性
2. 检查代码风格
3. 检查性能问题
4. 提出改进建议

---
## 输出格式
请使用以下格式输出审查结果：

### ✅ 正确性
...

### ⚠️ 代码风格
...

### ⚡ 性能
...

### 💡 改进建议
...
"""
```

### 7.5.4 控制输出长度

```python
# ❌ 不限制长度
no_limit = "介绍一下人工智能"

# ✅ 明确长度要求
with_limit = """
请用一句话（不超过50字）解释什么是机器学习。
"""

# ✅ 更精确的长度控制
precise_limit = """
请用恰好3个句子介绍Python语言的特点。
每句不超过25个字。
"""
```

## 7.6 常见场景 Prompt 示例

### 7.6.1 文本处理类

```python
# 文本摘要
SUMMARIZE_PROMPT = """
请为以下文章写一个摘要。

要求：
- 摘要长度：{max_length}字
- 必须包含文章的3个核心要点
- 使用客观中性的语言
- 不添加原文没有的信息

文章：
{content}
"""

# 关键词提取
KEYWORDS_PROMPT = """
从以下文本中提取5-10个关键词：

{text}

要求：
- 按重要性排序
- 包含技术术语
- 用逗号分隔
"""

# 情感分析
SENTIMENT_PROMPT = """
分析以下评论的情感倾向：

{review}

请从以下选项中选择一个：
A. 非常正面
B. 正面
C. 中性
D. 负面
E. 非常负面

同时给出0-100的情感强度评分。
"""
```

### 7.6.2 内容创作类

```python
# 博客文章
BLOG_POST_PROMPT = """
请撰写一篇关于"{topic}"的博客文章。

## 要求
- 标题：吸引人、有SEO友好
- 受众：{audience}
- 风格：{style}
- 字数：{word_count}字
- 结构：引言、3-5个要点、总结

## 必须包含
1. 实用性内容，读者可以直接应用
2. 至少2个真实案例
3. 3个可操作的建议

## 禁止出现
- 空话套话
- 与主题无关的内容
- 超过字数限制
"""

# 产品描述
PRODUCT_DESC_PROMPT = """
请为以下产品写一段产品描述：

产品名：{name}
特点：{features}
目标用户：{target}

要求：
- 长度：100-150字
- 突出核心卖点
- 引起目标用户共鸣
- 使用有感染力的语言
"""
```

### 7.6.3 代码相关类

```python
# 代码解释
CODE_EXPLAIN_PROMPT = """
请解释以下代码的工作原理：

```{language}
{code}
```

请用通俗的语言解释：
1. 这段代码在做什么
2. 主要的逻辑流程
3. 关键的函数或变量

适合阅读对象：{level}
"""

# 代码审查
CODE_REVIEW_PROMPT = """
请审查以下代码，找出潜在问题：

文件：{file_path}

```{language}
{code}
```

审查维度：
1. **正确性**：逻辑错误、边界条件
2. **安全性**：SQL注入、XSS等安全漏洞
3. **性能**：效率问题、资源浪费
4. **可维护性**：代码风格、可读性
5. **最佳实践**：是否符合语言规范

输出格式：
## 问题列表
| 严重程度 | 问题描述 | 位置 | 建议 |
|----------|----------|------|------|
"""
```

### 7.6.4 教学辅导类

```python
# 概念解释
CONCEPT_EXPLAIN_PROMPT = """
请解释"{concept}"这个概念。

目标受众：{audience}
详细程度：{detail_level}

请包含：
1. 一句话定义
2. 核心要点（3-5个）
3. 实际应用场景（2-3个）
4. 相关概念对比（如有）
5. 学习建议
"""

# 练习题生成
EXERCISE_PROMPT = """
请为"{topic}"生成{count}道练习题。

难度：{difficulty}
题型：{question_types}

要求：
- 每道题都要有明确的考察点
- 提供参考答案和评分标准
- 题目之间难度要有梯度
"""

# 学习计划
LEARNING_PLAN_PROMPT = """
请为"{skill}"技能制定一个学习计划。

学习时长：{duration}
当前水平：{current_level}
学习目标：{goal}

请包含：
1. 学习阶段划分（每个阶段的目标）
2. 每日/每周学习内容
3. 练习项目建议
4. 里程碑和验收标准
5. 学习资源推荐
"""
```

## 7.7 Prompt 调试与优化

### 7.7.1 Prompt 迭代流程

```
┌─────────────────────────────────────────────────────────────────┐
│                    Prompt 迭代优化流程                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   1. 明确目标 ──► 2. 编写初版 ──► 3. 测试运行                    │
│        ↑                    ↓                                    │
│        │                    ↓                                    │
│        │              4. 评估输出                                │
│        │                    ↓                                    │
│        │              5. 问题诊断 ──► 6. 优化修改                  │
│        │                    ↑        ↓                            │
│        └─────────────────────────────                            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

```python
class PromptOptimizer:
    """Prompt 优化器"""
    
    def __init__(self, client):
        self.client = client
        self.history = []
    
    def evaluate(self, prompt: str, test_cases: list) -> dict:
        """
        评估 Prompt 质量
        
        Args:
            prompt: 待评估的 Prompt
            test_cases: 测试用例列表
        
        Returns:
            评估报告
        """
        results = []
        for case in test_cases:
            # 填充模板
            filled_prompt = prompt.format(**case["input"])
            
            # 执行
            response = self.client.chat(filled_prompt)
            
            # 评估
            evaluation = self._evaluate_response(
                response["message"],
                case["expected"]
            )
            
            results.append({
                "input": case["input"],
                "output": response["message"],
                "expected": case["expected"],
                "evaluation": evaluation
            })
        
        return self._generate_report(results)
    
    def _evaluate_response(self, actual: str, expected: str) -> dict:
        """评估单次响应"""
        # 简化的评估逻辑
        return {
            "accuracy": 0.85 if len(actual) > 50 else 0.6,
            "format_correct": "JSON" in expected or actual.startswith("{"),
            "length_appropriate": 50 < len(actual) < 500
        }
    
    def _generate_report(self, results: list) -> dict:
        """生成评估报告"""
        total = len(results)
        passed = sum(1 for r in results if r["evaluation"]["accuracy"] > 0.7)
        
        return {
            "total_tests": total,
            "passed": passed,
            "pass_rate": passed / total,
            "results": results,
            "suggestions": self._generate_suggestions(results)
        }
```

### 7.7.2 常见问题与解决方案

```python
# 问题1：输出格式不稳定
# 原因：没有明确指定格式
# 解决：提供具体格式要求

FIX_FORMAT_ISSUE = """
## 问题
模型输出的JSON格式不稳定，有时多空格，有时缺少引号。

## 解决方案
1. 提供完整的JSON示例
2. 明确每个字段的数据类型
3. 使用XML或Markdown代码块包裹

示例 Prompt：
请将以下信息转换为JSON格式：
{"name": "张三", "age": 25, "city": "北京"}

必须符合以下JSON Schema：
{
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "age": {"type": "integer"},
        "city": {"type": "string"}
    },
    "required": ["name", "age", "city"]
}
"""

# 问题2：输出过长
# 原因：没有限制长度
# 解决：明确字数或条数限制

FIX_LENGTH_ISSUE = """
## 问题
模型输出过于冗长，包含太多解释。

## 解决方案
1. 明确限制输出长度
2. 指定只输出核心内容
3. 禁止添加额外解释

示例 Prompt：
请列出Python的5个主要应用领域。
要求：
- 每条不超过20个字
- 只列出领域名称
- 不要解释
"""
```

## 本章小结

本章介绍了 Prompt 工程的基础知识：

1. **Prompt 的本质**：任务指令 + 背景信息 + 输出要求
2. **核心要素**：角色定义、任务描述、背景信息、输出格式
3. **Zero-shot vs Few-shot**：何时使用示例
4. **结构化模板**：提高复用性和可维护性
5. **最佳实践**：清晰具体、分解任务、控制长度
6. **调试优化**：迭代改进 Prompt 质量

掌握这些基础，你已经能够编写出基本合格的 Prompt。下一章我们将学习高级 Prompt 技巧，进一步提升与大模型交互的效率和质量。

---

## 思考与练习

1. **概念理解**：对比 Zero-shot 和 Few-shot 的适用场景，举例说明。

2. **实践练习**：为以下场景编写 Prompt：
   - 邮件撰写（回复客户投诉）
   - 数据分析报告生成
   - 技术文档翻译

3. **模板设计**：设计一个通用的"代码解释"Prompt 模板，支持不同编程语言和难度级别。

4. **迭代优化**：选择一个现有的 Prompt，通过添加角色、示例、格式要求等方式进行优化，对比优化前后的效果。

5. **工具实践**：使用 LangChain 或类似框架，创建一个 Prompt 模板管理系统。

6. **思考题**：Prompt 工程与大模型能力的关系是什么？模型能力提升后，Prompt 工程是否还重要？
