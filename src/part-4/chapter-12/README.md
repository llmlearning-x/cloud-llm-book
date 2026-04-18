# 第12章：内容生成与创作助手

> 本章介绍如何使用 AI 构建内容生成与创作助手。从文本生成、结构化输出，到批量处理和任务队列，帮助你构建高效的内容创作系统。

## 12.1 内容生成概述

### 12.1.1 应用场景

| 场景 | 示例 |
|------|------|
| **营销文案** | 产品描述、广告语、社交媒体帖子 |
| **新闻摘要** | 文章摘要、标题生成 |
| **内容改写** | 风格转换、长度调整 |
| **结构化输出** | JSON、表格、代码 |
| **批量生成** | SEO文章、产品描述 |

### 12.1.2 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                    内容生成系统架构                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌────────────┐      ┌────────────┐      ┌────────────┐         │
│  │  内容     │ ───► │   Prompt  │ ───► │    AI      │         │
│  │  模板库   │      │   引擎     │      │    API     │         │
│  └────────────┘      └────────────┘      └────────────┘         │
│                                                    │             │
│  ┌────────────┐      ┌────────────┐              │             │
│  │  质量     │ ◄── │   输出     │ ◄─────────────┘             │
│  │  控制     │      │   处理     │                              │
│  └────────────┘      └────────────┘                              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## 12.2 结构化输出

### 12.2.1 JSON 输出

```python
import json
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime

class Product(BaseModel):
    """产品数据模型"""
    name: str = Field(description="产品名称")
    price: float = Field(description="价格（元）")
    category: str = Field(description="产品类别")
    tags: List[str] = Field(default_factory=list, description="产品标签")
    description: Optional[str] = Field(None, description="产品描述")

def generate_structured_content(
    client,
    prompt: str,
    output_schema: dict
) -> Dict[str, Any]:
    """
    生成结构化内容
    
    Args:
        client: AI 客户端
        prompt: 内容要求
        output_schema: JSON Schema
    
    Returns:
        结构化数据
    """
    schema_str = json.dumps(output_schema, ensure_ascii=False, indent=2)
    
    full_prompt = f"""{prompt}

请严格按照以下JSON Schema输出，只输出JSON，不要任何其他内容：

```json
{schema_str}
```
"""
    
    response = client.chat(full_prompt)
    content = response["message"].strip()
    
    # 尝试解析 JSON
    # 去掉可能的markdown代码块
    if content.startswith("```"):
        lines = content.split('\n')
        content = '\n'.join(lines[1:-1])
    
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        return {"error": "解析失败", "raw": content}

# 使用示例
schema = {
    "type": "object",
    "properties": {
        "name": {"type": "string", "description": "产品名称"},
        "price": {"type": "number", "description": "价格"},
        "category": {"type": "string", "description": "类别"},
        "tags": {"type": "array", "items": {"type": "string"}},
        "description": {"type": "string"}
    },
    "required": ["name", "price", "category"]
}

result = generate_structured_content(
    client,
    prompt="为一台新款笔记本电脑生成产品信息",
    output_schema=schema
)
print(json.dumps(result, ensure_ascii=False, indent=2))
```

### 12.2.2 表格输出

```python
from typing import List

def generate_table_content(
    client,
    headers: List[str],
    rows: int,
    topic: str
) -> str:
    """
    生成表格内容
    
    Args:
        headers: 表头
        rows: 行数
        topic: 表格主题
    
    Returns:
        Markdown 表格
    """
    headers_str = " | ".join(headers)
    separator = " | ".join(["---"] * len(headers))
    
    prompt = f"""请生成一个关于"{topic}"的表格：

表头：{headers_str}

生成 {rows} 行数据，以 Markdown 表格格式输出。

要求：
1. 数据要合理、真实
2. 每列内容要多样化
3. 只输出表格，不要其他内容
"""
    
    response = client.chat(prompt)
    return response["message"]

# 使用示例
table = generate_table_content(
    client,
    headers=["书名", "作者", "价格", "评分"],
    rows=5,
    topic="Python 编程书籍推荐"
)
print(table)
```

### 12.2.3 带验证的输出

```python
from typing import Callable, Any
import re

class OutputValidator:
    """输出验证器"""
    
    def __init__(self):
        self.validators = {}
    
    def register(self, field: str, validator: Callable):
        """注册验证器"""
        self.validators[field] = validator
    
    def validate(self, data: dict) -> tuple[bool, List[str]]:
        """
        验证数据
        
        Returns:
            (是否通过, 错误列表)
        """
        errors = []
        
        for field, validator in self.validators.items():
            if field in data:
                try:
                    if not validator(data[field]):
                        errors.append(f"{field} 验证失败")
                except Exception as e:
                    errors.append(f"{field} 验证错误: {str(e)}")
        
        return len(errors) == 0, errors

# 内置验证器
Validators = {
    "email": lambda x: bool(re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', x)),
    "phone": lambda x: bool(re.match(r'^1[3-9]\d{9}$', x)),
    "price": lambda x: isinstance(x, (int, float)) and x > 0,
    "url": lambda x: x.startswith(("http://", "https://")),
    "non_empty": lambda x: bool(x and len(str(x).strip()) > 0),
}

def generate_with_validation(
    client,
    prompt: str,
    schema: dict,
    validators: dict = None
) -> dict:
    """
    生成并验证结构化内容
    """
    # 生成
    result = generate_structured_content(client, prompt, schema)
    
    if "error" in result:
        return result
    
    # 验证
    validator = OutputValidator()
    if validators:
        for field, validator_name in validators.items():
            if validator_name in Validators:
                validator.register(field, Validators[validator_name])
    
    is_valid, errors = validator.validate(result)
    
    if is_valid:
        result["_validation"] = "passed"
    else:
        result["_validation"] = "failed"
        result["_errors"] = errors
    
    return result
```

## 12.3 批量内容生成

### 12.3.1 基础批量处理

```python
import asyncio
from typing import List, Dict, Callable
from concurrent.futures import ThreadPoolExecutor
import time

class BatchGenerator:
    """批量内容生成器"""
    
    def __init__(self, client, max_workers: int = 3):
        self.client = client
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.results = []
    
    def generate_batch(
        self,
        prompts: List[str],
        template: str = None,
        show_progress: bool = True
    ) -> List[Dict]:
        """
        批量生成内容
        
        Args:
            prompts: 提示词列表
            template: 可选的输出模板
            show_progress: 显示进度
        
        Returns:
            生成结果列表
        """
        results = []
        
        for i, prompt in enumerate(prompts):
            if show_progress:
                print(f"处理 {i+1}/{len(prompts)}...")
            
            try:
                if template:
                    prompt = template.format(prompt=prompt)
                
                response = self.client.chat(prompt)
                results.append({
                    "prompt": prompt,
                    "result": response["message"],
                    "status": "success",
                    "usage": response.get("usage", {})
                })
            except Exception as e:
                results.append({
                    "prompt": prompt,
                    "result": None,
                    "status": "error",
                    "error": str(e)
                })
        
        self.results = results
        return results
    
    def generate_product_descriptions(
        self,
        products: List[Dict]
    ) -> List[Dict]:
        """
        批量生成产品描述
        """
        prompts = []
        for product in products:
            prompt = f"""为以下产品生成一段吸引人的产品描述：

产品名称：{product.get('name', '')}
产品类别：{product.get('category', '')}
产品特点：{product.get('features', '')}

要求：
1. 50-100字
2. 突出产品卖点
3. 吸引目标用户
4. 包含行动号召
"""
            prompts.append(prompt)
        
        return self.generate_batch(prompts)

# 使用示例
products = [
    {"name": "无线蓝牙耳机", "category": "电子产品", "features": "降噪、长续航、舒适佩戴"},
    {"name": "运动跑步鞋", "category": "运动鞋", "features": "轻便、透气、防滑"},
    {"name": "保温杯", "category": "生活用品", "features": "不锈钢、保冷保热、大容量"},
]

generator = BatchGenerator(client, max_workers=2)
results = generator.generate_product_descriptions(products)

for i, r in enumerate(results):
    print(f"\n【产品 {i+1}】")
    print(f"描述: {r['result']}")
```

### 12.3.2 异步批量处理

```python
import asyncio
from typing import List
import aiohttp

class AsyncBatchGenerator:
    """异步批量生成器"""
    
    def __init__(self, client, semaphore: int = 5):
        self.client = client
        self.semaphore = asyncio.Semaphore(semaphore)
    
    async def generate_one(self, prompt: str) -> Dict:
        """生成单个内容"""
        async with self.semaphore:
            try:
                # 模拟异步调用
                await asyncio.sleep(0.1)  # 模拟网络延迟
                
                response = await asyncio.to_thread(
                    self.client.chat, prompt
                )
                
                return {
                    "prompt": prompt,
                    "result": response["message"],
                    "status": "success"
                }
            except Exception as e:
                return {
                    "prompt": prompt,
                    "result": None,
                    "status": "error",
                    "error": str(e)
                }
    
    async def generate_batch(self, prompts: List[str]) -> List[Dict]:
        """批量异步生成"""
        tasks = [self.generate_one(p) for p in prompts]
        results = await asyncio.gather(*tasks)
        return results
    
    async def generate_with_progress(
        self,
        prompts: List[str],
        callback: Callable = None
    ) -> List[Dict]:
        """带进度的批量生成"""
        results = []
        total = len(prompts)
        
        for i, prompt in enumerate(prompts):
            result = await self.generate_one(prompt)
            results.append(result)
            
            if callback:
                callback(i + 1, total, result)
        
        return results

async def main():
    generator = AsyncBatchGenerator(client, semaphore=3)
    
    prompts = [f"生成关于主题{i}的内容" for i in range(10)]
    
    def progress_callback(current, total, result):
        print(f"进度: {current}/{total}")
    
    results = await generator.generate_with_progress(prompts, progress_callback)
    
    for r in results:
        print(f"✓ {r['prompt'][:30]}...")

# 运行
asyncio.run(main())
```

### 12.3.3 任务队列

```python
import queue
import threading
from enum import Enum
from dataclasses import dataclass
from typing import Callable, Optional
import uuid

class TaskStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class GenerationTask:
    """生成任务"""
    task_id: str
    prompt: str
    template: Optional[str] = None
    metadata: dict = None
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[str] = None
    error: Optional[str] = None
    created_at: str = ""
    completed_at: str = ""

class TaskQueue:
    """任务队列"""
    
    def __init__(self, client, num_workers: int = 2):
        self.client = client
        self.num_workers = num_workers
        self.queue = queue.Queue()
        self.tasks: Dict[str, GenerationTask] = {}
        self.workers: List[threading.Thread] = []
        self.running = False
    
    def start(self):
        """启动工作线程"""
        self.running = True
        for _ in range(self.num_workers):
            t = threading.Thread(target=self._worker, daemon=True)
            t.start()
            self.workers.append(t)
    
    def stop(self):
        """停止工作线程"""
        self.running = False
        for _ in range(self.num_workers):
            self.queue.put(None)  # 发送停止信号
        for t in self.workers:
            t.join(timeout=1)
    
    def _worker(self):
        """工作线程"""
        while self.running:
            task = self.queue.get()
            if task is None:
                break
            
            self._process_task(task)
    
    def _process_task(self, task: GenerationTask):
        """处理任务"""
        task.status = TaskStatus.PROCESSING
        
        try:
            prompt = task.prompt
            if task.template:
                prompt = task.template.format(**task.metadata or {})
            
            response = self.client.chat(prompt)
            task.result = response["message"]
            task.status = TaskStatus.COMPLETED
        except Exception as e:
            task.error = str(e)
            task.status = TaskStatus.FAILED
    
    def submit(self, prompt: str, template: str = None, metadata: dict = None) -> str:
        """
        提交任务
        
        Returns:
            任务ID
        """
        task_id = str(uuid.uuid4())
        task = GenerationTask(
            task_id=task_id,
            prompt=prompt,
            template=template,
            metadata=metadata
        )
        
        self.tasks[task_id] = task
        self.queue.put(task)
        
        return task_id
    
    def get_status(self, task_id: str) -> Optional[GenerationTask]:
        """获取任务状态"""
        return self.tasks.get(task_id)
    
    def get_result(self, task_id: str, timeout: float = 30) -> Optional[str]:
        """
        获取任务结果（阻塞等待）
        """
        task = self.tasks.get(task_id)
        if not task:
            return None
        
        # 轮询等待
        import time
        start = time.time()
        while task.status in [TaskStatus.PENDING, TaskStatus.PROCESSING]:
            if time.time() - start > timeout:
                return None
            time.sleep(0.1)
        
        return task.result if task.status == TaskStatus.COMPLETED else None

# 使用示例
task_queue = TaskQueue(client, num_workers=2)
task_queue.start()

# 提交任务
task_ids = []
for i in range(5):
    task_id = task_queue.submit(
        prompt=f"写一篇关于主题{i}的短文",
        metadata={"index": i}
    )
    task_ids.append(task_id)
    print(f"提交任务: {task_id}")

# 获取结果
time.sleep(5)  # 等待处理

for task_id in task_ids:
    task = task_queue.get_status(task_id)
    print(f"任务 {task_id}: {task.status.value}")

task_queue.stop()
```

## 12.4 内容创作模板

### 12.4.1 营销文案模板

```python
class MarketingContentGenerator:
    """营销内容生成器"""
    
    def __init__(self, client):
        self.client = client
    
    def generate_product_description(
        self,
        product_name: str,
        category: str,
        features: List[str],
        target_audience: str,
        tone: str = "professional"
    ) -> str:
        """生成产品描述"""
        prompt = f"""为以下产品生成营销文案：

产品名称：{product_name}
产品类别：{category}
产品特点：
{chr(10).join(f'- {f}' for f in features)}
目标用户：{target_audience}
文案风格：{tone}

要求：
1. 开头引人注目
2. 突出核心卖点
3. 针对目标用户痛点
4. 包含行动号召
5. 100-200字
"""
        return self.client.chat(prompt)["message"]
    
    def generate_social_media_post(
        self,
        content: str,
        platform: str = "wechat"
    ) -> str:
        """生成社交媒体帖子"""
        platform_guide = {
            "wechat": "微信公众号风格，可读性强，适当使用emoji",
            "weibo": "微博风格，140字以内，适当话题标签",
            "xiaohongshu": "小红书风格，种草笔记，亲切分享",
        }
        
        prompt = f"""将以下内容改写成{platform}风格的帖子：

原文：
{content}

平台特点：{platform_guide.get(platform, '')}

要求：
1. 适应平台风格
2. 吸引目标读者
3. 适当添加互动元素
"""
        return self.client.chat(prompt)["message"]
    
    def generate_email(
        self,
        subject: str,
        purpose: str,
        content: str,
        recipient: str = "客户"
    ) -> str:
        """生成营销邮件"""
        prompt = f"""撰写一封营销邮件：

主题：{subject}
目的：{purpose}
收件人：{recipient}

主要内容：
{content}

要求：
1. 主题行吸引人
2. 正文结构清晰
3. 包含明确的CTA
4. 专业但不生硬
"""
        return self.client.chat(prompt)["message"]

# 使用示例
gen = MarketingContentGenerator(client)

# 产品描述
desc = gen.generate_product_description(
    product_name="智能手环",
    category="可穿戴设备",
    features=[
        "24小时心率监测",
        "睡眠质量分析",
        "7天超长续航",
        "50米防水"
    ],
    target_audience="注重健康的年轻人",
    tone="活力、专业"
)
print(desc)
```

### 12.4.2 文章生成模板

```python
class ArticleGenerator:
    """文章生成器"""
    
    def __init__(self, client):
        self.client = client
    
    def generate_blog_post(
        self,
        topic: str,
        target_length: int = 1000,
        style: str = "informative"
    ) -> Dict[str, str]:
        """生成博客文章"""
        # 生成标题
        title_prompt = f"""为"{topic}"生成5个吸引人的博客标题：

要求：
1. 简洁有力
2. SEO友好
3. 引起读者兴趣
4. 格式：只输出标题，每行一个
"""
        titles_response = self.client.chat(title_prompt)
        titles = [
            t.strip() for t in titles_response["message"].split('\n')
            if t.strip()
        ]
        
        # 生成正文
        body_prompt = f"""写一篇关于"{topic}"的博客文章：

要求：
- 字数：约{target_length}字
- 风格：{style}
- 结构：引言、3-5个要点、总结
- 包含实用信息和见解
"""
        body_response = self.client.chat(body_prompt)
        
        return {
            "title": titles[0] if titles else topic,
            "titles": titles,
            "body": body_response["message"]
        }
    
    def generate_seo_article(
        self,
        keyword: str,
        competitors: List[str] = None
    ) -> Dict[str, str]:
        """生成 SEO 文章"""
        competitor_info = ""
        if competitors:
            competitor_info = f"\n竞争对手标题参考：\n" + "\n".join(f"- {c}" for c in competitors)
        
        # 生成大纲
        outline_prompt = f"""为关键词"{keyword}"生成文章大纲：

{competitor_info}

要求：
1. 覆盖关键词的各个方面
2. 有独特视角
3. 便于搜索引擎收录
4. 格式：列出H2、H3标题
"""
        outline_response = self.client.chat(outline_prompt)
        
        # 生成内容
        content_prompt = f"""根据以下大纲，写一篇关于"{keyword}"的SEO文章：

大纲：
{outline_response['message']}

SEO要求：
1. 关键词自然出现3-5次
2. 包含小标题
3. 有列表和段落
4. 500-800字
5. 结尾有总结和CTA
"""
        content_response = self.client.chat(content_prompt)
        
        return {
            "outline": outline_response["message"],
            "content": content_response["message"],
            "keyword": keyword
        }

# 使用示例
article_gen = ArticleGenerator(client)

article = article_gen.generate_blog_post(
    topic="Python异步编程",
    target_length=800,
    style="技术教程"
)

print(f"标题: {article['title']}")
print(f"\n正文:\n{article['body']}")
```

### 12.4.3 代码生成模板

```python
class CodeGenerator:
    """代码生成器"""
    
    def __init__(self, client):
        self.client = client
    
    def generate_code(
        self,
        description: str,
        language: str = "python",
        framework: str = None
    ) -> str:
        """生成代码"""
        framework_info = f"\n使用框架：{framework}" if framework else ""
        
        prompt = f"""请生成{language}代码：

需求描述：
{description}
{language}语言
{framework_info}

要求：
1. 代码完整可运行
2. 有适当的注释
3. 包含错误处理
4. 遵循最佳实践
"""
        response = self.client.chat(prompt)
        return response["message"]
    
    def explain_code(self, code: str, language: str = "python") -> str:
        """解释代码"""
        prompt = f"""解释以下{language}代码的工作原理：

```{language}
{code}
```

请解释：
1. 整体功能
2. 关键逻辑
3. 重要的函数或变量
"""
        return self.client.chat(prompt)["message"]
    
    def review_code(self, code: str, language: str = "python") -> Dict[str, str]:
        """代码审查"""
        prompt = f"""审查以下{language}代码：

```{language}
{code}
```

请从以下维度审查：
1. 正确性
2. 安全性
3. 性能
4. 可维护性

输出格式：
## 问题列表
### 正确性
...
### 安全性
...
### 性能
...
### 改进建议
...
"""
        response = self.client.chat(prompt)
        
        # 简单解析
        sections = {}
        current_section = None
        
        for line in response["message"].split('\n'):
            if line.startswith('## '):
                current_section = line[3:].strip()
                sections[current_section] = []
            elif current_section and line.strip():
                sections[current_section].append(line)
        
        return {
            "review": response["message"],
            "sections": {k: '\n'.join(v) for k, v in sections.items()}
        }

# 使用示例
code_gen = CodeGenerator(client)

code = code_gen.generate_code(
    description="一个Web服务，接收用户上传的图片，缩放到800x600，保存到本地",
    language="python",
    framework="Flask"
)
print(code)
```

## 12.5 质量控制

### 12.5.1 输出质量评估

```python
class QualityChecker:
    """质量检查器"""
    
    def __init__(self, client):
        self.client = client
        self.quality_rules = {
            "min_length": 50,
            "max_length": 2000,
            "required_elements": [],
            "forbidden_words": ["假的", "假的", "不可能", "绝对"],
        }
    
    def check_quality(self, content: str, rules: dict = None) -> Dict[str, Any]:
        """检查内容质量"""
        rules = rules or self.quality_rules
        issues = []
        
        # 长度检查
        if len(content) < rules["min_length"]:
            issues.append(f"内容过短（{len(content)}字 < {rules['min_length']}字）")
        
        if len(content) > rules["max_length"]:
            issues.append(f"内容过长（{len(content)}字 > {rules['max_length']}字）")
        
        # 敏感词检查
        for word in rules["forbidden_words"]:
            if word in content:
                issues.append(f"包含敏感词：{word}")
        
        # 必需元素检查
        for element in rules.get("required_elements", []):
            if element not in content:
                issues.append(f"缺少必需内容：{element}")
        
        return {
            "passed": len(issues) == 0,
            "issues": issues,
            "length": len(content),
            "word_count": len(content.replace(" ", ""))
        }
    
    def auto_fix(self, content: str, issues: List[str]) -> str:
        """自动修复问题"""
        prompt = f"""请修复以下内容中的问题：

原文：
{content}

问题列表：
{chr(10).join(f'- {issue}' for issue in issues)}

请修改后输出完整内容，确保：
1. 修复所有问题
2. 保持原意
3. 质量达标
"""
        return self.client.chat(prompt)["message"]

def generate_with_quality_control(
    client,
    prompt: str,
    quality_rules: dict = None
) -> str:
    """
    带质量控制的内容生成
    """
    checker = QualityChecker(client)
    
    # 生成
    response = client.chat(prompt)
    content = response["message"]
    
    # 检查
    result = checker.check_quality(content, quality_rules)
    
    if not result["passed"]:
        # 尝试修复
        content = checker.auto_fix(content, result["issues"])
        
        # 再次检查
        result = checker.check_quality(content, quality_rules)
        
        if not result["passed"]:
            return {
                "content": content,
                "quality": "failed",
                "issues": result["issues"]
            }
    
    return {
        "content": content,
        "quality": "passed",
        "issues": []
    }
```

### 12.5.2 多版本生成与选择

```python
def generate_multiple_versions(
    client,
    prompt: str,
    num_versions: int = 3
) -> List[Dict]:
    """
    生成多个版本并评估
    """
    versions = []
    
    for i in range(num_versions):
        # 轻微变化 temperature
        temperature = 0.7 + i * 0.1
        
        response = client.chat(
            prompt,
            temperature=temperature,
            metadata={"version": i + 1}
        )
        
        versions.append({
            "version": i + 1,
            "content": response["message"],
            "temperature": temperature
        })
    
    return versions

def select_best_version(
    client,
    versions: List[Dict],
    criteria: str = "质量"
) -> Dict:
    """
    选择最佳版本
    """
    version_contents = "\n\n".join([
        f"=== 版本 {v['version']} ===\n{v['content']}"
        for v in versions
    ])
    
    prompt = f"""请根据以下标准，从{len(versions)}个版本中选择最佳的一个：

选择标准：{criteria}

{version_contents}

请分析每个版本的优缺点，然后输出：
最佳版本：X
理由：...
"""
    response = client.chat(prompt)
    
    # 解析响应
    for v in versions:
        if str(v["version"]) in response["message"]:
            return v
    
    return versions[0]  # 默认返回第一个

# 使用示例
versions = generate_multiple_versions(
    client,
    prompt="为一篇关于AI的文章写开头",
    num_versions=3
)

best = select_best_version(client, versions, "可读性和吸引力")
print(f"最佳版本: {best['version']}")
print(best['content'])
```

## 本章小结

本章介绍了内容生成与创作助手：

1. **结构化输出**：JSON、表格、带验证的输出
2. **批量处理**：多线程/异步批量生成
3. **任务队列**：异步任务管理
4. **创作模板**：营销文案、文章、代码生成
5. **质量控制**：评估、修复、多版本选择

下一章我们将学习垂直领域应用，探索 AI 在教育、金融、法律等领域的具体应用。

---

## 思考与练习

1. **实践练习**：构建一个批量生成产品描述的工具。

2. **系统设计**：设计一个带质量控制的内容生成系统。

3. **优化思考**：如何提高批量生成的效率和质量？

4. **扩展功能**：添加内容版权检测、抄袭检查功能。
