# 第13章：垂直领域应用

> 本章介绍 AI 在三个典型垂直领域的应用：教育领域的智能问答助手、金融领域的报告摘要生成、法律领域的合同审查辅助。每个领域都有独特的业务逻辑和数据处理需求。

## 13.1 教育领域：智能问答助手

### 13.1.1 需求分析

校园智能问答助手需要处理：

| 类型 | 示例问题 | 技术要点 |
|------|----------|----------|
| 教务信息 | 选课、转专业、学分 | FAQ + 知识库 |
| 校园生活 | 食堂、宿舍、图书馆 | 知识库 + 规则 |
| 政策咨询 | 奖学金、助学贷款 | 政策文档检索 |
| 学习辅助 | 课程内容、作业 | RAG + 专业文档 |

### 13.1.2 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                    校园问答助手架构                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌────────────┐                                                │
│  │   用户     │                                                │
│  │   输入     │                                                │
│  └─────┬──────┘                                                │
│        │                                                        │
│  ┌─────▼──────┐      ┌────────────┐                            │
│  │   意图     │ ───► │   问题     │                            │
│  │   识别     │      │   分类     │                            │
│  └─────┬──────┘      └─────┬──────┘                            │
│        │                   │                                    │
│        │          ┌────────┴────────┐                           │
│        │          ▼                 ▼                           │
│        │    ┌──────────┐      ┌──────────┐                    │
│        │    │ FAQ 检索 │      │ RAG 检索 │                    │
│        │    └────┬─────┘      └────┬─────┘                    │
│        │         │                 │                            │
│        │         └────────┬────────┘                           │
│        │                  ▼                                    │
│  ┌─────▼──────────────────────────┐                             │
│  │         答案生成与后处理        │                             │
│  └───────────────────────────────┘                             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 13.1.3 完整实现

```python
from typing import Dict, List, Optional
from enum import Enum

class QuestionCategory(Enum):
    """问题分类"""
    ACADEMIC = "academic"           # 教务相关
    CAMPUS_LIFE = "campus_life"    # 校园生活
    POLICY = "policy"              # 政策咨询
    LEARNING = "learning"          # 学习辅助
    TECHNOLOGY = "technology"      # 技术问题
    OTHER = "other"                # 其他

class CampusQAAgent:
    """校园问答助手"""
    
    SYSTEM_PROMPT = """你是一个热心的校园助手，名为"小智"。
你的职责是帮助学生解决校园生活中的各种问题。

背景信息：
- 当前学期：2024年春季学期
- 校区：北京校区
- 学校类型：综合性大学

你的能力：
1. 回答教务相关问题（选课、转专业、考试等）
2. 提供校园生活指引（食堂、宿舍、图书馆等）
3. 解释学校政策（奖学金、助学贷款等）
4. 辅助学习（课程内容、学习方法等）

回答原则：
1. 友好、耐心、专业
2. 不确定时建议咨询相关部门
3. 涉及个人信息时提醒学生保护隐私
4. 回答简洁明了，避免冗长

如果问题超出你的知识范围，请诚实说明并建议：
"这个问题我不太确定，建议您联系[相关部门]咨询：xxx@school.edu.cn"
"""
    
    def __init__(self, client):
        self.client = client
        self.faq_kb = self._load_faq()
        self.policy_kb = self._load_policies()
    
    def _load_faq(self) -> Dict[str, List[Dict]]:
        """加载常见问题"""
        return {
            QuestionCategory.ACADEMIC: [
                {
                    "question": "如何进行网上选课？",
                    "answer": """网上选课步骤：
1. 登录教务系统（jwc.school.edu.cn）
2. 进入"选课管理"->"正选选课"
3. 选择课程和教学班
4. 确认选课结果

注意事项：
- 选课前先查看培养方案
- 热门课程可能需要抽签
- 退改选一般在开学第一周"""
                },
                {
                    "question": "如何申请转专业？",
                    "answer": """转专业申请条件：
1. 全日制本科一年级学生
2. 无不及格课程
3. 通过转入专业考核

申请流程：
1. 每学期第12周提交申请
2. 参加转专业考核
3. 教务处审核
4. 结果公示

注意事项：不同专业要求可能不同，请以教务处通知为准。"""
                },
            ],
            QuestionCategory.CAMPUS_LIFE: [
                {
                    "question": "图书馆开放时间？",
                    "answer": """图书馆开放时间：
- 阅览室：8:00-22:00（周一至周日）
- 自习室：7:00-23:00
- 借还书：8:30-21:30

寒暑假期间开放时间调整，请关注图书馆通知。"""
                },
                {
                    "question": "食堂营业时间？",
                    "answer": """各食堂营业时间：
- 第一食堂：6:30-20:30
- 第二食堂：7:00-21:00
- 清真食堂：7:00-20:00

夜间食堂（学生活动中心旁）：18:00-23:00"""
                },
            ],
            QuestionCategory.POLICY: [
                {
                    "question": "奖学金如何申请？",
                    "answer": """奖学金类型及申请：

1. 国家奖学金
   - 金额：8000元/年
   - 要求：学业成绩优异、社会实践突出

2. 校级奖学金
   - 一等奖：5000元/年
   - 二等奖：3000元/年
   - 三等奖：1000元/年

申请时间：每学期末
申请方式：辅导员推荐+学院审核"""
                },
            ],
        }
    
    def _load_policies(self) -> List[Dict]:
        """加载政策文档"""
        return [
            {"title": "学籍管理规定", "content": "..."},
            {"title": "考试纪律", "content": "..."},
            {"title": "奖助学金办法", "content": "..."},
        ]
    
    def classify_question(self, question: str) -> QuestionCategory:
        """分类问题"""
        category_keywords = {
            QuestionCategory.ACADEMIC: ["选课", "成绩", "学分", "考试", "转专业", "毕业"],
            QuestionCategory.CAMPUS_LIFE: ["食堂", "宿舍", "图书馆", "校园", "卡", "热水"],
            QuestionCategory.POLICY: ["奖学金", "贷款", "政策", "规定", "申请条件"],
            QuestionCategory.LEARNING: ["课程", "作业", "学习", "考研", "证书"],
            QuestionCategory.TECHNOLOGY: ["校园网", "VPN", "邮箱", "账号", "密码"],
        }
        
        for category, keywords in category_keywords.items():
            if any(kw in question for kw in keywords):
                return category
        
        return QuestionCategory.OTHER
    
    def find_faq(self, question: str, category: QuestionCategory) -> Optional[str]:
        """查找 FAQ"""
        faqs = self.faq_kb.get(category, [])
        
        for faq in faqs:
            # 简单关键词匹配
            if any(kw in question for kw in faq["question"]):
                return faq["answer"]
        
        return None
    
    def answer(self, question: str) -> str:
        """回答问题"""
        # 分类
        category = self.classify_question(question)
        
        # 查找 FAQ
        faq_answer = self.find_faq(question, category)
        if faq_answer:
            return faq_answer
        
        # 使用 LLM 生成回答
        prompt = f"""
问题：{question}

请基于校园助手的角色回答这个问题。
如果不确定，请诚实地说明并提供建议。
"""
        
        response = self.client.chat(
            prompt,
            system_prompt=self.SYSTEM_PROMPT
        )
        
        return response["message"]

# 使用示例
agent = CampusQAAgent(client)

questions = [
    "图书馆几点开门？",
    "奖学金怎么申请？",
    "如何转专业？",
    "食堂中午几点关门？",
]

for q in questions:
    print(f"\n问题: {q}")
    answer = agent.answer(q)
    print(f"回答: {answer}")
```

### 13.1.4 对话界面

```html
<!-- campus-qa.html -->
<!DOCTYPE html>
<html>
<head>
    <title>校园问答助手</title>
    <style>
        body { font-family: sans-serif; max-width: 700px; margin: 0 auto; padding: 20px; }
        .header { background: #1976d2; color: white; padding: 20px; border-radius: 8px 8px 0 0; }
        .header h1 { margin: 0; font-size: 24px; }
        .header p { margin: 5px 0 0; opacity: 0.9; }
        .chat { background: #f5f5f5; padding: 20px; min-height: 400px; }
        .message { margin: 15px 0; }
        .user-msg { text-align: right; }
        .user-msg .content { background: #e3f2fd; padding: 10px 15px; border-radius: 15px 15px 0 15px; display: inline-block; }
        .bot-msg .content { background: white; padding: 15px; border-radius: 0 15px 15px 15px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
        .input-area { display: flex; gap: 10px; margin-top: 15px; }
        .input-area input { flex: 1; padding: 12px; border: 1px solid #ddd; border-radius: 25px; font-size: 14px; }
        .input-area button { padding: 10px 25px; background: #1976d2; color: white; border: none; border-radius: 25px; cursor: pointer; }
        .quick-questions { margin-top: 15px; }
        .quick-questions span { display: inline-block; background: white; padding: 5px 12px; margin: 3px; border-radius: 15px; font-size: 12px; cursor: pointer; border: 1px solid #ddd; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🎓 校园问答助手</h1>
        <p>小智为您服务 · 7x24小时在线</p>
    </div>
    
    <div class="chat" id="chatBox"></div>
    
    <div class="input-area">
        <input type="text" id="question" placeholder="输入您的问题...">
        <button onclick="ask()">发送</button>
    </div>
    
    <div class="quick-questions">
        <p>快捷问题：</p>
        <span onclick="quickAsk('图书馆开放时间？')">图书馆开放时间</span>
        <span onclick="quickAsk('如何申请奖学金？')">申请奖学金</span>
        <span onclick="quickAsk('网上选课流程？')">网上选课流程</span>
        <span onclick="quickAsk('转专业条件？')">转专业条件</span>
    </div>
    
    <script>
        function addMessage(text, isUser) {
            const chatBox = document.getElementById('chatBox');
            const div = document.createElement('div');
            div.className = 'message ' + (isUser ? 'user-msg' : 'bot-msg');
            div.innerHTML = `<div class="content">${text}</div>`;
            chatBox.appendChild(div);
            chatBox.scrollTop = chatBox.scrollHeight;
        }
        
        function ask() {
            const input = document.getElementById('question');
            const q = input.value.trim();
            if (!q) return;
            
            addMessage(q, true);
            input.value = '';
            
            fetch('/api/campus/ask', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ question: q })
            })
            .then(r => r.json())
            .then(data => addMessage(data.answer, false));
        }
        
        function quickAsk(q) {
            document.getElementById('question').value = q;
            ask();
        }
    </script>
</body>
</html>
```

## 13.2 金融领域：报告摘要生成

### 13.2.1 需求分析

金融报告摘要系统需要：

| 报告类型 | 处理要点 |
|----------|----------|
| 财报 | 营收、利润、关键指标 |
| 研报 | 投资建议、风险提示 |
| 公告 | 重大事项、公告摘要 |
| 新闻 | 舆情摘要、行业动态 |

### 13.2.2 财报摘要生成

```python
from typing import Dict, List, Optional
from datetime import datetime
import re

class FinancialReportSummarizer:
    """金融报告摘要生成器"""
    
    SYSTEM_PROMPT = """你是一个专业的金融分析师，擅长阅读和分析各类金融报告。
你的任务是从原始报告中提取关键信息，生成简洁、准确的摘要。

输出要求：
1. 专业但不晦涩
2. 数据准确，标注单位
3. 突出重点和变化
4. 客观呈现，不添加主观判断

财务指标解释：
- 营收/营业收入：公司销售商品或提供服务获得的收入
- 净利润：扣除所有成本和税费后的利润
- 毛利率：(营收-成本)/营收，反映盈利能力
- 资产负债率：负债/资产，反映财务杠杆
"""
    
    def __init__(self, client):
        self.client = client
    
    def summarize_financial_report(
        self,
        report_text: str,
        company_name: str = "公司",
        period: str = ""
    ) -> Dict[str, str]:
        """生成财报摘要"""
        prompt = f"""请分析以下{company_name}的{period}财务报告，生成摘要：

报告内容：
{report_text}

请输出以下格式的摘要：

## 核心数据
- 营业收入：XXX亿元（同比+XX%）
- 净利润：XXX亿元（同比+XX%）
- 毛利率：XX%
- 每股收益：XX元

## 经营亮点
1. [主要亮点]
2. [主要亮点]

## 主要风险
1. [主要风险]
2. [主要风险]

## 整体评价
[一句话总结]

只输出上述内容，不要其他。"""
        
        response = self.client.chat(
            prompt,
            system_prompt=self.SYSTEM_PROMPT
        )
        
        return self._parse_summary(response["message"])
    
    def _parse_summary(self, text: str) -> Dict[str, str]:
        """解析摘要文本"""
        result = {
            "核心数据": "",
            "经营亮点": "",
            "主要风险": "",
            "整体评价": "",
            "raw": text
        }
        
        current_section = None
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            if '## ' in line:
                current_section = line.replace('## ', '').strip()
            elif current_section and line.startswith('-'):
                result[current_section] += line + "\n"
            elif current_section:
                result[current_section] += line + "\n"
        
        return result
    
    def compare_reports(
        self,
        report1: str,
        report2: str,
        company1_name: str = "公司A",
        company2_name: str = "公司B"
    ) -> str:
        """对比分析两份财报"""
        prompt = f"""请对比分析以下两份财报：

{company1_name}：
{report1}

{company2_name}：
{report2}

请从以下维度对比：
1. 规模对比（营收、资产）
2. 盈利能力对比（净利润、毛利率）
3. 成长性对比（同比增速）
4. 偿债能力对比（资产负债率）

输出格式：对比表格 + 简要结论
"""
        return self.client.chat(prompt)["message"]

# 使用示例
summarizer = FinancialReportSummarizer(client)

sample_report = """
XXX公司2024年年度报告：

一、主要会计数据和财务指标
营业收入：125.8亿元，同比增长15.3%
净利润：18.6亿元，同比增长22.5%
扣非净利润：16.2亿元，同比增长19.8%
基本每股收益：1.85元

二、主营业务构成
产品销售：98.5亿元（占比78.3%）
技术服务：27.3亿元（占比21.7%）

三、经营情况讨论
2024年，公司继续深化技术创新，产品市场份额稳步提升。
海外业务收入达到15.6亿元，同比增长45%。

四、风险提示
1. 行业竞争加剧风险
2. 原材料价格波动风险
3. 汇率风险
"""

summary = summarizer.summarize_financial_report(
    sample_report,
    company_name="XXX公司",
    period="2024年度"
)

print("=== 财报摘要 ===")
print(summary["raw"])
```

### 13.2.3 研报摘要生成

```python
class ResearchReportSummarizer:
    """研报摘要生成器"""
    
    def __init__(self, client):
        self.client = client
    
    def summarize_research_report(
        self,
        report_text: str,
        stock_code: str = "",
        stock_name: str = ""
    ) -> Dict[str, str]:
        """生成研报摘要"""
        header = f"""
研报标的：{stock_name}（{stock_code}）
生成时间：{datetime.now().strftime('%Y-%m-%d')}
"""
        
        prompt = f"""{header}
请分析以下研究报告，生成结构化摘要：

研报内容：
{report_text}

输出格式：

## 投资要点
1. [核心投资逻辑]
2. [关键看点]

## 核心数据
| 指标 | 数值 | 同比变化 |
|------|------|----------|
| ...  | ...  | ...      |

## 投资建议
- 评级：[强烈推荐/推荐/中性/回避]
- 目标价：XXX元（当前价XXX元）
- 建议理由：...

## 风险提示
1. [主要风险]
2. [主要风险]

只输出上述内容。"""
        
        response = self.client.chat(prompt)
        
        return {
            "header": header,
            "summary": response["message"]
        }
    
    def extract_key_metrics(self, report_text: str) -> List[Dict]:
        """提取关键指标"""
        prompt = f"""从以下报告中提取关键财务指标：

{report_text}

以JSON格式输出指标列表：
{{"metrics": [{{"name": "指标名", "value": "数值", "yoy": "同比变化", "unit": "单位"}}]}}

只输出JSON。"""
        
        response = self.client.chat(prompt)
        
        # 解析 JSON
        import json
        try:
            data = json.loads(response["message"])
            return data.get("metrics", [])
        except:
            return []

# 使用示例
research_report = """
海通证券研报：XXX公司深度报告

投资评级：推荐
目标价：45元（当前价38元）

核心观点：
公司作为行业龙头，受益于市场需求持续增长。
我们预计公司2024-2026年净利润CAGR为25%。

关键数据：
- 2024年EPS预期：1.85元
- 2025年EPS预期：2.31元
- PE估值：20.5倍（行业平均25倍）

风险因素：
1. 行业政策变化风险
2. 市场需求不及预期风险
3. 原材料成本上升风险
"""

summarizer = ResearchReportSummarizer(client)
result = summarizer.summarize_research_report(
    research_report,
    stock_code="600000",
    stock_name="XXX公司"
)
print(result["summary"])
```

## 13.3 法律领域：合同审查辅助

### 13.3.1 需求分析

合同审查辅助系统需要：

| 功能 | 说明 |
|------|------|
| 条款提取 | 识别合同关键条款 |
| 风险识别 | 发现潜在风险点 |
| 合规检查 | 验证法律合规性 |
| 建议生成 | 提供修改建议 |

### 13.3.2 合同审查实现

```python
from typing import Dict, List, Optional
import re

class ContractReviewer:
    """合同审查辅助"""
    
    SYSTEM_PROMPT = """你是一个专业的法律顾问，擅长审查各类商业合同。
你的任务是识别合同中的关键条款、潜在风险，并提供修改建议。

审查原则：
1. 客观公正，不偏袒任何一方
2. 风险提示要明确具体
3. 建议要有法律依据
4. 注意保护商业秘密

常见的合同风险类型：
- 条款不明确导致争议
- 违约责任过轻或过重
- 免责条款不合理
- 知识产权归属不清
- 保密条款不完善
- 争议解决机制缺失或不公
"""
    
    def __init__(self, client):
        self.client = client
    
    def review_contract(
        self,
        contract_text: str,
        contract_type: str = "通用合同"
    ) -> Dict[str, any]:
        """审查合同"""
        prompt = f"""请审查以下{contract_type}：

{contract_text}

请从以下维度进行审查：

## 一、合同基本信息
- 合同双方：[识别当事人]
- 合同标的：[识别标的]
- 合同金额：[识别金额]
- 合同期限：[识别期限]

## 二、关键条款分析
识别并分析以下关键条款：
1. 权利义务条款
2. 付款条款
3. 违约条款
4. 保密条款
5. 知识产权条款
6. 争议解决条款

## 三、风险识别
列出发现的潜在风险点，格式：
- 【风险】[风险描述] - 风险等级：[高/中/低]
- 【建议】[对应的修改建议]

## 四、总体评价
- 合同完整性：[完整/缺失条款]
- 条款公平性：[公平/需修改]
- 建议：[整体修改建议]

请详细分析，不要遗漏重要信息。"""
        
        response = self.client.chat(
            prompt,
            system_prompt=self.SYSTEM_PROMPT
        )
        
        return self._parse_review(response["message"])
    
    def _parse_review(self, text: str) -> Dict[str, any]:
        """解析审查结果"""
        result = {
            "basic_info": {},
            "clause_analysis": {},
            "risks": [],
            "overall": "",
            "raw": text
        }
        
        # 简化解析
        sections = text.split('## ')
        for section in sections:
            if not section.strip():
                continue
            
            lines = section.split('\n')
            title = lines[0].strip()
            
            if '基本信息' in title:
                result["basic_info"]["content"] = '\n'.join(lines[1:])
            elif '风险识别' in title:
                result["risks"] = [l for l in lines[1:] if l.strip()]
            elif '总体评价' in title:
                result["overall"] = '\n'.join(lines[1:])
        
        return result
    
    def check_compliance(
        self,
        contract_text: str,
        laws: List[str] = None
    ) -> Dict[str, List[str]]:
        """合规性检查"""
        laws_str = "\n".join(f"- {law}" for law in laws) if laws else "《民法典》《合同法》"
        
        prompt = f"""请检查以下合同的合规性：

{contract_text}

需要检查的法律法规：
{laws_str}

请指出：
1. 符合法律规定的条款
2. 可能违反法律的条款及依据
3. 建议修改方式

输出格式：
## 合规条款
- [符合条款及依据]

## 违规风险
- 【违规】[条款内容] - 依据：[法律依据]
- 【修改建议】[建议内容]

## 合规结论
[总体评价]
"""
        return self.client.chat(prompt)["message"]
    
    def extract_key_terms(
        self,
        contract_text: str
    ) -> Dict[str, str]:
        """提取合同关键条款"""
        prompt = f"""请提取以下合同的关键条款：

{contract_text}

提取以下信息（JSON格式）：
{{
    "parties": ["甲方", "乙方"],
    "subject": "合同标的",
    "amount": "金额",
    "start_date": "开始日期",
    "end_date": "结束日期",
    "payment_terms": "付款条件",
    "breach_consequences": "违约后果",
    "dispute_resolution": "争议解决方式"
}}

只输出JSON。"""
        
        response = self.client.chat(prompt)
        
        import json
        try:
            return json.loads(response["message"])
        except:
            return {"error": "解析失败"}

# 使用示例
reviewer = ContractReviewer(client)

sample_contract = """
技术服务合同

甲方：北京科技有限公司
乙方：上海软件公司

一、服务内容
乙方为甲方提供软件开发服务，包括需求分析、设计、开发、测试及部署。

二、合同金额
合同总价为人民币50万元整。

三、付款方式
1. 合同签订后5个工作日内支付30%预付款
2. 项目验收合格后支付剩余70%

四、项目周期
项目周期为6个月，自合同签订之日起计算。

五、知识产权
项目成果的知识产权归甲方所有。

六、保密条款
双方应对合作过程中知悉的对方商业秘密保密，保密期限为合同终止后2年。

七、违约责任
如一方违约，应向对方支付合同总价20%的违约金。

八、争议解决
因本合同产生的争议，提交甲方所在地人民法院管辖。

九、合同期限
本合同自双方签字盖章之日起生效，有效期至项目验收合格后一年。
"""

result = reviewer.review_contract(sample_contract, "技术服务合同")
print("=== 合同审查结果 ===")
print(result["raw"])
```

### 13.3.3 合同生成辅助

```python
class ContractGenerator:
    """合同生成辅助"""
    
    def __init__(self, client):
        self.client = client
    
    def generate_clause(
        self,
        clause_type: str,
        context: Dict[str, str]
    ) -> str:
        """生成合同条款"""
        context_str = "\n".join(f"- {k}：{v}" for k, v in context.items())
        
        prompt = f"""请生成以下类型的合同条款：

条款类型：{clause_type}

背景信息：
{context_str}

要求：
1. 条款要完整、清晰
2. 符合法律法规
3. 保护甲方合法权益
4. 条款表述要准确、无歧义

只输出条款内容。"""
        
        return self.client.chat(prompt)["message"]
    
    def generate_full_contract(
        self,
        contract_type: str,
        party_a: str,
        party_b: str,
        subject: str,
        amount: str,
        other_terms: str = ""
    ) -> str:
        """生成完整合同"""
        prompt = f"""请生成一份{contract_type}：

合同双方：
- 甲方：{party_a}
- 乙方：{party_b}

合同标的：{subject}
合同金额：{amount}

其他约定：{other_terms}

请生成完整的合同文本，包含：
1. 合同标题
2. 合同双方信息
3. 合同标的
4. 权利义务
5. 付款条款
6. 违约责任
7. 保密条款
8. 知识产权（如适用）
9. 争议解决
10. 其他约定
11. 签署栏

条款要专业、完整、符合法律规范。"""
        
        return self.client.chat(prompt)["message"]

# 使用示例
generator = ContractGenerator(client)

# 生成保密条款
clause = generator.generate_clause(
    clause_type="保密条款",
    context={
        "保密内容": "双方在合作中知悉的任何商业秘密",
        "保密期限": "合作期间及结束后3年",
        "违约责任": "泄露方承担因此造成的全部损失"
    }
)
print("=== 保密条款 ===")
print(clause)
```

## 13.4 应用部署

### 13.4.1 API 服务

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional

app = FastAPI(title="垂直领域 AI 应用")

# 各领域服务实例
campus_agent = CampusQAAgent(client)
financial_summarizer = FinancialReportSummarizer(client)
contract_reviewer = ContractReviewer(client)

# ============== 校园问答 ==============

class CampusQuestion(BaseModel):
    question: str

@app.post("/api/campus/ask")
async def campus_ask(request: CampusQuestion):
    """校园问答"""
    answer = campus_agent.answer(request.question)
    return {"answer": answer, "category": campus_agent.classify_question(request.question).value}

# ============== 财报摘要 ==============

class FinancialReportRequest(BaseModel):
    report_text: str
    company_name: str = ""
    period: str = ""

@app.post("/api/financial/summarize")
async def financial_summarize(request: FinancialReportRequest):
    """财报摘要"""
    summary = financial_summarizer.summarize_financial_report(
        request.report_text,
        request.company_name,
        request.period
    )
    return summary

# ============== 合同审查 ==============

class ContractReviewRequest(BaseModel):
    contract_text: str
    contract_type: str = "通用合同"

@app.post("/api/legal/review")
async def contract_review(request: ContractReviewRequest):
    """合同审查"""
    result = contract_reviewer.review_contract(
        request.contract_text,
        request.contract_type
    )
    return result
```

## 本章小结

本章介绍了三个垂直领域的 AI 应用：

1. **教育领域**：校园问答助手，处理教务、生活、政策等问题
2. **金融领域**：财报和研报摘要，自动提取关键数据
3. **法律领域**：合同审查辅助，识别风险、提供建议

每个领域都有独特的业务逻辑，需要：
- 领域专业知识
- 定制化的 Prompt 设计
- 专业的输出格式

---

## 思考与练习

1. **领域调研**：选择一个你熟悉的垂直领域，分析其 AI 应用需求。

2. **实践练习**：为校园问答助手添加更多 FAQ 数据。

3. **系统设计**：设计一个金融舆情监控系统。

4. **功能扩展**：为合同审查系统添加合同模板生成功能。

5. **思考**：垂直领域 AI 应用的通用性和专业性如何平衡？
