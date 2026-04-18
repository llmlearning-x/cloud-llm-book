# 第11章：智能客服开发

> 本章介绍如何开发一个完整的智能客服系统。从多轮对话设计、意图识别、槽位填充，到对话管理和路由，帮助你构建能够真正解决用户问题的智能客服。

## 11.1 智能客服系统架构

### 11.1.1 系统组成

```
┌─────────────────────────────────────────────────────────────────┐
│                    智能客服系统架构                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌────────────┐                                                │
│  │   用户     │                                                │
│  │   接入     │                                                │
│  └─────┬──────┘                                                │
│        │                                                        │
│  ┌─────▼──────┐      ┌────────────┐      ┌────────────┐        │
│  │   对话     │ ───► │   意图     │ ───► │   槽位     │        │
│  │   管理     │      │   识别     │      │   填充     │        │
│  └─────┬──────┘      └────────────┘      └─────┬──────┘        │
│        │                                        │                │
│        │         ┌──────────────────────────────┘                │
│        │         │                                              │
│  ┌─────▼─────────▼──────┐      ┌────────────┐                   │
│  │      对话策略       │ ───► │   知识库   │                   │
│  │    (Policy)        │      │   查询     │                   │
│  └─────┬───────────────┘      └────────────┘                   │
│        │                                                        │
│  ┌─────▼──────┐      ┌────────────┐                            │
│  │   回复     │ ───► │   API/工具 │                            │
│  │   生成     │      │   调用     │                            │
│  └────────────┘      └────────────┘                            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 11.1.2 核心模块

| 模块 | 功能 | 技术 |
|------|------|------|
| 对话管理 | 管理对话状态、历史 | 状态机 |
| 意图识别 | 识别用户意图 | 分类模型/规则 |
| 槽位填充 | 提取关键信息 | NER/规则 |
| 知识库 | 检索答案 | RAG |
| 回复生成 | 生成自然回复 | LLM/模板 |

## 11.2 意图识别

### 11.2.1 意图定义

```python
from enum import Enum
from typing import List, Optional
from dataclasses import dataclass

class Intent(Enum):
    """客服意图枚举"""
    GREETING = "greeting"           # 问候
    PRODUCT_INQUIRY = "product_inquiry"  # 产品咨询
    ORDER_STATUS = "order_status"   # 订单查询
    REFUND = "refund"              # 退款申请
    COMPLAINT = "complaint"        # 投诉
    SUGGESTION = "suggestion"      # 建议
    GOODBYE = "goodbye"            # 告别
    UNKNOWN = "unknown"             # 未知

@dataclass
class IntentExample:
    """意图示例"""
    text: str
    intent: Intent

# 意图示例库
INTENT_EXAMPLES = {
    Intent.GREETING: [
        "你好",
        "早上好",
        "在吗",
        "你好，请问有人在吗",
    ],
    Intent.PRODUCT_INQUIRY: [
        "这个产品有什么特点",
        "产品的价格是多少",
        "能介绍一下吗",
        "产品支持什么功能",
    ],
    Intent.ORDER_STATUS: [
        "我的订单到哪了",
        "查一下订单",
        "订单号是XXX",
        "什么时候发货",
    ],
    Intent.REFUND: [
        "我要退款",
        "申请退款",
        "不想要了",
        "申请退货",
    ],
    Intent.COMPLAINT: [
        "太差了",
        "非常不满意",
        "要投诉",
        "服务态度差",
    ],
    Intent.SUGGESTION: [
        "建议你们",
        "希望可以",
        "能不能增加",
        "希望改进",
    ],
    Intent.GOODBYE: [
        "再见",
        "拜拜",
        "谢谢，再见",
        "好了，没事了",
    ],
}
```

### 11.2.2 基于规则的意图识别

```python
import re
from typing import Dict, Tuple

class RuleBasedIntentClassifier:
    """基于规则的意图分类器"""
    
    def __init__(self):
        self.intent_patterns: Dict[Intent, List[str]] = {
            Intent.GREETING: [
                r"你好",
                r"在吗",
                r"早上好",
                r"您好",
                r"嗨[啊]?",
            ],
            Intent.PRODUCT_INQUIRY: [
                r"产品",
                r"价格",
                r"功能",
                r"特点",
                r"介绍",
                r"怎么样",
            ],
            Intent.ORDER_STATUS: [
                r"订单",
                r"发货",
                r"物流",
                r"到了吗",
                r"什么时候到",
            ],
            Intent.REFUND: [
                r"退款",
                r"退货",
                r"取消订单",
                r"不想要",
            ],
            Intent.COMPLAINT: [
                r"投诉",
                r"太差",
                r"不满意",
                r"垃圾",
                r"问题",
            ],
            Intent.SUGGESTION: [
                r"建议",
                r"希望",
                r"能不能",
                r"应该",
            ],
            Intent.GOODBYE: [
                r"再见",
                r"拜拜",
                r"谢了",
                r"好的",
                r"知道了",
            ],
        }
        
        # 意图优先级（数字越大优先级越高）
        self.intent_priority = {
            Intent.UNKNOWN: 0,
            Intent.GREETING: 1,
            Intent.GOODBYE: 2,
            Intent.PRODUCT_INQUIRY: 3,
            Intent.ORDER_STATUS: 3,
            Intent.REFUND: 4,
            Intent.COMPLAINT: 5,
            Intent.SUGGESTION: 3,
        }
    
    def classify(self, text: str) -> Tuple[Intent, float]:
        """
        识别意图
        
        Returns:
            (意图, 置信度)
        """
        text = text.lower()
        matched_intents = []
        
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text):
                    matched_intents.append(intent)
                    break
        
        if not matched_intents:
            return Intent.UNKNOWN, 0.0
        
        # 按优先级排序
        matched_intents.sort(
            key=lambda x: self.intent_priority[x],
            reverse=True
        )
        
        best_intent = matched_intents[0]
        confidence = min(0.9, 0.5 + 0.1 * len(matched_intents))
        
        return best_intent, confidence
    
    def add_pattern(self, intent: Intent, pattern: str):
        """添加新的模式"""
        if intent not in self.intent_patterns:
            self.intent_patterns[intent] = []
        self.intent_patterns[intent].append(pattern)

# 使用示例
classifier = RuleBasedIntentClassifier()

test_queries = [
    "你好，我想问一下产品",
    "我的订单什么时候到",
    "申请退款",
    "这个产品有什么功能",
]

for query in test_queries:
    intent, confidence = classifier.classify(query)
    print(f"'{query}' → {intent.value} ({confidence:.2f})")
```

### 11.2.3 基于 LLM 的意图识别

```python
from typing import List, Dict

class LLMIntentClassifier:
    """基于 LLM 的意图分类器"""
    
    SYSTEM_PROMPT = """你是一个客服意图分类器。
给定用户消息，输出对应的意图类别。

可用的意图类别：
- greeting: 问候
- product_inquiry: 产品咨询
- order_status: 订单查询
- refund: 退款申请
- complaint: 投诉
- suggestion: 建议
- goodbye: 告别
- unknown: 未知

只输出意图名称，不要其他内容。"""

    def __init__(self, client):
        self.client = client
    
    def classify(self, text: str) -> Tuple[Intent, float]:
        """
        使用 LLM 识别意图
        """
        response = self.client.chat(
            text,
            system_prompt=self.SYSTEM_PROMPT
        )
        
        # 解析意图
        intent_text = response["message"].strip().lower()
        
        # 映射到 Intent 枚举
        intent_map = {
            "greeting": Intent.GREETING,
            "product_inquiry": Intent.PRODUCT_INQUIRY,
            "order_status": Intent.ORDER_STATUS,
            "refund": Intent.REFUND,
            "complaint": Intent.COMPLAINT,
            "suggestion": Intent.SUGGESTION,
            "goodbye": Intent.GOODBYE,
            "unknown": Intent.UNKNOWN,
        }
        
        intent = intent_map.get(intent_text, Intent.UNKNOWN)
        confidence = 0.85 if intent != Intent.UNKNOWN else 0.3
        
        return intent, confidence

class HybridIntentClassifier:
    """混合意图分类器（规则 + LLM）"""
    
    def __init__(self, client):
        self.rule_classifier = RuleBasedIntentClassifier()
        self.llm_classifier = LLMIntentClassifier(client)
    
    def classify(self, text: str) -> Tuple[Intent, float]:
        """
        先用规则，再用 LLM
        """
        # 先用规则
        rule_intent, rule_conf = self.rule_classifier.classify(text)
        
        # 高置信度直接返回
        if rule_conf > 0.7:
            return rule_intent, rule_conf
        
        # 低置信度用 LLM 验证
        llm_intent, llm_conf = self.llm_classifier.classify(text)
        
        # 如果 LLM 更自信
        if llm_conf > rule_conf:
            return llm_intent, llm_conf
        
        return rule_intent, rule_conf
```

## 11.3 槽位填充

### 11.3.1 槽位定义

```python
from typing import Dict, List, Optional, Any

@dataclass
class Slot:
    """槽位定义"""
    name: str
    description: str
    required: bool
    type: str  # string, number, date, enum
    examples: List[str] = field(default_factory=list)

@dataclass
class SlotValue:
    """槽位值"""
    slot_name: str
    value: Any
    confidence: float
    source: str  # extracted, inferred, requested

class SlotFillingSchema:
    """槽位填充模式"""
    
    def __init__(self):
        self.slots: Dict[str, Slot] = {
            "product_name": Slot(
                name="product_name",
                description="产品名称",
                required=False,
                type="string",
                examples=["iPhone", "MacBook", "AirPods"]
            ),
            "order_id": Slot(
                name="order_id",
                description="订单号",
                required=False,
                type="string",
                examples=["ORD123456", "订单号"]
            ),
            "user_id": Slot(
                name="user_id",
                description="用户ID",
                required=False,
                type="string",
                examples=["用户ID", "我的账号"]
            ),
            "refund_reason": Slot(
                name="refund_reason",
                description="退款原因",
                required=False,
                type="string",
                examples=["不想要了", "质量问题", "发错货了"]
            ),
            "phone": Slot(
                name="phone",
                description="联系电话",
                required=False,
                type="string",
                examples=["手机号", "电话"]
            ),
        }
    
    def get_required_slots(self, intent: Intent) -> List[str]:
        """获取意图所需的槽位"""
        intent_slots = {
            Intent.ORDER_STATUS: ["order_id", "user_id"],
            Intent.REFUND: ["order_id", "refund_reason"],
            Intent.COMPLAINT: ["phone"],
        }
        return intent_slots.get(intent, [])
    
    def get_all_slots(self) -> List[str]:
        """获取所有槽位名"""
        return list(self.slots.keys())
```

### 11.3.2 槽位提取

```python
import re

class RuleBasedSlotExtractor:
    """基于规则的槽位提取器"""
    
    def __init__(self, schema: SlotFillingSchema):
        self.schema = schema
        self.patterns = {
            "order_id": [
                r"订单[号]?[:：]?\s*([A-Z0-9]{8,})",
                r"order[:：]?\s*([A-Z0-9]{8,})",
                r"ORD\d+",
            ],
            "phone": [
                r"1[3-9]\d{9}",  # 手机号
                r"\d{3,4}[-]\d{7,8}",  # 固话
            ],
            "refund_reason": {
                "不想要": "不想要了",
                "质量有问题": "质量问题",
                "错了": "发错货了",
                "太久了": "等待时间过长",
            }
        }
    
    def extract(self, text: str) -> Dict[str, SlotValue]:
        """
        提取槽位
        
        Returns:
            {槽位名: 槽位值}
        """
        results = {}
        
        for slot_name, patterns in self.patterns.items():
            if isinstance(patterns, list):
                # 正则模式
                for pattern in patterns:
                    match = re.search(pattern, text, re.IGNORECASE)
                    if match:
                        value = match.group(1) if match.groups() else match.group(0)
                        results[slot_name] = SlotValue(
                            slot_name=slot_name,
                            value=value,
                            confidence=0.9,
                            source="extracted"
                        )
                        break
            else:
                # 字典映射
                for keyword, value in patterns.items():
                    if keyword in text:
                        results[slot_name] = SlotValue(
                            slot_name=slot_name,
                            value=value,
                            confidence=0.8,
                            source="extracted"
                        )
                        break
        
        return results

class LLMSlotExtractor:
    """基于 LLM 的槽位提取"""
    
    def __init__(self, client, schema: SlotFillingSchema):
        self.client = client
        self.schema = schema
    
    def extract(self, text: str, intent: Intent) -> Dict[str, SlotValue]:
        """使用 LLM 提取槽位"""
        slot_names = self.schema.get_all_slots()
        
        prompt = f"""从以下用户消息中提取信息：

消息：{text}

需要提取的字段：
{chr(10).join(f'- {s}: {self.schema.slots[s].description}' for s in slot_names)}

以JSON格式输出：
{{"字段名": "提取的值"}}
只输出JSON，不要其他内容。
"""
        
        response = self.client.chat(prompt)
        
        # 解析 JSON
        import json
        try:
            extracted = json.loads(response["message"])
            results = {}
            for slot_name, value in extracted.items():
                if value and slot_name in slot_names:
                    results[slot_name] = SlotValue(
                        slot_name=slot_name,
                        value=value,
                        confidence=0.85,
                        source="llm"
                    )
            return results
        except:
            return {}

class HybridSlotExtractor:
    """混合槽位提取器"""
    
    def __init__(self, client, schema: SlotFillingSchema):
        self.schema = schema
        self.rule_extractor = RuleBasedSlotExtractor(schema)
        self.llm_extractor = LLMSlotExtractor(client, schema)
    
    def extract(self, text: str, intent: Intent) -> Dict[str, SlotValue]:
        """先规则后 LLM"""
        # 先用规则提取
        results = self.rule_extractor.extract(text)
        
        # 检查是否缺少必要槽位
        required_slots = self.schema.get_required_slots(intent)
        missing_slots = [s for s in required_slots if s not in results]
        
        if missing_slots:
            # 用 LLM 补充提取
            llm_results = self.llm_extractor.extract(text, intent)
            for slot_name in missing_slots:
                if slot_name in llm_results:
                    results[slot_name] = llm_results[slot_name]
        
        return results
```

## 11.4 对话管理

### 11.4.1 对话状态

```python
from enum import Enum
from typing import Dict, List, Optional
from dataclasses import dataclass, field
import json

class DialogueState(Enum):
    """对话状态"""
    START = "start"
    INTENT_CONFIRM = "intent_confirm"
    SLOT_FILLING = "slot_filling"
    WAITING_ANSWER = "waiting_answer"
    ANSWERING = "answering"
    CONFIRMATION = "confirmation"
    END = "end"

@dataclass
class DialogueContext:
    """对话上下文"""
    session_id: str
    user_id: str
    state: DialogueState = DialogueState.START
    current_intent: Optional[Intent] = None
    slots: Dict[str, SlotValue] = field(default_factory=dict)
    history: List[Dict] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""
    
    def add_turn(self, user_message: str, assistant_message: str):
        """添加对话轮次"""
        self.history.append({
            "user": user_message,
            "assistant": assistant_message
        })
    
    def get_missing_slots(self, schema: SlotFillingSchema) -> List[str]:
        """获取缺失的必要槽位"""
        if not self.current_intent:
            return []
        
        required = schema.get_required_slots(self.current_intent)
        return [s for s in required if s not in self.slots]
    
    def is_complete(self, schema: SlotFillingSchema) -> bool:
        """检查是否收集完所有必要槽位"""
        return len(self.get_missing_slots(schema)) == 0
    
    def to_dict(self) -> dict:
        """序列化为字典"""
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "state": self.state.value,
            "current_intent": self.current_intent.value if self.current_intent else None,
            "slots": {
                k: {"name": v.slot_name, "value": v.value, "confidence": v.confidence}
                for k, v in self.slots.items()
            },
            "history": self.history,
        }
```

### 11.4.2 对话管理器

```python
class DialogueManager:
    """对话管理器"""
    
    def __init__(
        self,
        intent_classifier,
        slot_extractor,
        schema: SlotFillingSchema,
        knowledge_base: KnowledgeBase = None
    ):
        self.intent_classifier = intent_classifier
        self.slot_extractor = slot_extractor
        self.schema = schema
        self.knowledge_base = knowledge_base
        
        # 对话上下文存储
        self.contexts: Dict[str, DialogueContext] = {}
        
        # 意图确认阈值
        self.intent_confirm_threshold = 0.6
    
    def get_context(self, session_id: str, user_id: str) -> DialogueContext:
        """获取或创建对话上下文"""
        if session_id not in self.contexts:
            self.contexts[session_id] = DialogueContext(
                session_id=session_id,
                user_id=user_id
            )
        return self.contexts[session_id]
    
    def process(self, session_id: str, user_id: str, message: str) -> str:
        """
        处理用户消息，返回助手回复
        """
        # 获取上下文
        context = self.get_context(session_id, user_id)
        
        # 根据状态处理
        if context.state == DialogueState.START:
            return self._handle_start(context, message)
        
        elif context.state == DialogueState.INTENT_CONFIRM:
            return self._handle_intent_confirm(context, message)
        
        elif context.state == DialogueState.SLOT_FILLING:
            return self._handle_slot_filling(context, message)
        
        elif context.state == DialogueState.ANSWERING:
            return self._handle_answering(context, message)
        
        elif context.state == DialogueState.CONFIRMATION:
            return self._handle_confirmation(context, message)
        
        else:
            return self._handle_end(context, message)
    
    def _handle_start(self, context: DialogueContext, message: str) -> str:
        """处理开始状态"""
        # 意图识别
        intent, confidence = self.intent_classifier.classify(message)
        context.current_intent = intent
        
        # 简单意图直接处理
        if intent in [Intent.GREETING]:
            context.state = DialogueState.ANSWERING
            return self._generate_greeting()
        
        if intent in [Intent.GOODBYE]:
            context.state = DialogueState.END
            return "再见！有什么问题随时再来问我。"
        
        # 需要确认或需要槽位填充
        if confidence < self.intent_confirm_threshold:
            context.state = DialogueState.INTENT_CONFIRM
            return f"您是想了解'{intent.value}'吗？请确认或更正。"
        
        # 提取槽位
        self._extract_slots(context, message)
        
        # 检查是否需要更多信息
        return self._check_and_collect_slots(context)
    
    def _handle_intent_confirm(self, context: DialogueContext, message: str) -> str:
        """处理意图确认"""
        # 用户确认
        if any(word in message for word in ["是", "对的", "没错", "正确"]):
            context.state = DialogueState.SLOT_FILLING
            return self._check_and_collect_slots(context)
        
        # 用户更正
        intent, confidence = self.intent_classifier.classify(message)
        context.current_intent = intent
        
        if confidence > self.intent_confirm_threshold:
            self._extract_slots(context, message)
            return self._check_and_collect_slots(context)
        
        return "抱歉，我没能理解。请问您想咨询什么问题？"
    
    def _handle_slot_filling(self, context: DialogueContext, message: str) -> str:
        """处理槽位填充"""
        # 提取槽位
        self._extract_slots(context, message)
        
        # 检查是否完整
        return self._check_and_collect_slots(context)
    
    def _handle_answering(self, context: DialogueContext, message: str) -> str:
        """处理回答状态"""
        # 如果用户继续问问题
        intent, confidence = self.intent_classifier.classify(message)
        
        if intent == Intent.GOODBYE:
            context.state = DialogueState.END
            return "再见！有什么问题随时再来问我。"
        
        # 作为新问题处理
        context.current_intent = intent
        return self._handle_start(context, message)
    
    def _handle_confirmation(self, context: DialogueContext, message: str) -> str:
        """处理确认"""
        if any(word in message for word in ["是", "好的", "确认", "同意"]):
            return self._execute_action(context)
        
        if any(word in message for word in ["否", "不对", "取消"]):
            context.state = DialogueState.SLOT_FILLING
            return "好的，请告诉我正确的信息。"
        
        return "请确认以上信息是否正确（是/否）"
    
    def _handle_end(self, context: DialogueContext, message: str) -> str:
        """处理结束状态"""
        return "对话已结束。输入新消息开始新的对话。"
    
    def _extract_slots(self, context: DialogueContext, message: str):
        """提取槽位"""
        if not context.current_intent:
            return
        
        slots = self.slot_extractor.extract(message, context.current_intent)
        
        for slot_name, slot_value in slots.items():
            # 如果已存在，保留置信度高的
            if slot_name not in context.slots or \
               slot_value.confidence > context.slots[slot_name].confidence:
                context.slots[slot_name] = slot_value
    
    def _check_and_collect_slots(self, context: DialogueContext) -> str:
        """检查并收集槽位"""
        missing = context.get_missing_slots(self.schema)
        
        if not missing:
            # 槽位已收集完整
            context.state = DialogueState.CONFIRMATION
            return self._summarize_and_confirm(context)
        
        # 请求缺失的槽位
        context.state = DialogueState.SLOT_FILLING
        slot = self.schema.slots[missing[0]]
        
        # 友好的询问方式
        slot_questions = {
            "order_id": "请问您的订单号是多少？",
            "refund_reason": "请问退款的原因是什么？",
            "phone": "请留下您的联系电话，方便我们联系您。",
            "user_id": "请问您的用户ID是？",
        }
        
        return slot_questions.get(missing[0], f"请提供您的{slot.description}。")
    
    def _summarize_and_confirm(self, context: DialogueContext) -> str:
        """总结并确认"""
        intent = context.current_intent.value
        slots_info = "\n".join([
            f"- {self.schema.slots[k].description}: {v.value}"
            for k, v in context.slots.items()
        ])
        
        return f"""好的，我来帮您处理{intent}：

{slots_info}

请确认以上信息是否正确。"""
    
    def _generate_greeting(self) -> str:
        """生成问候语"""
        return """您好！我是智能客服，很高兴为您服务。

我可以帮您：
📦 查询订单状态
💰 申请退款
📋 了解产品信息
📝 提供建议
❓ 解答其他问题

请告诉我您想了解什么？"""
    
    def _execute_action(self, context: DialogueContext) -> str:
        """执行业务动作"""
        # 根据意图执行不同的动作
        if context.current_intent == Intent.ORDER_STATUS:
            return self._handle_order_status(context)
        elif context.current_intent == Intent.REFUND:
            return self._handle_refund(context)
        else:
            return self._handle_general_inquiry(context)
    
    def _handle_order_status(self, context: DialogueContext) -> str:
        """处理订单查询"""
        order_id = context.slots.get("order_id")
        
        if order_id:
            # 实际项目中调用订单系统 API
            return f"根据订单号 {order_id.value}，您的订单正在配送中，预计明天送达。"
        
        return "抱歉，未能查询到您的订单信息。"
    
    def _handle_refund(self, context: DialogueContext) -> str:
        """处理退款申请"""
        return "您的退款申请已提交，我们将在1-3个工作日内处理，请保持手机畅通。"
    
    def _handle_general_inquiry(self, context: DialogueContext) -> str:
        """处理一般咨询"""
        # 使用知识库
        if self.knowledge_base:
            result = self.knowledge_base.similarity_search(
                context.current_intent.value,
                k=1
            )
            if result:
                return result[0].page_content
        
        return "抱歉，这个问题我暂时无法回答，请联系人工客服。"
```

## 11.5 智能客服实战

### 11.5.1 完整实现

```python
#!/usr/bin/env python3
"""
smart_customer_service.py
智能客服完整实现
"""

from typing import Dict
import uuid
from dataclasses import dataclass, field

class SmartCustomerService:
    """智能客服"""
    
    def __init__(self, knowledge_base=None):
        self.intent_classifier = RuleBasedIntentClassifier()
        self.slot_extractor = RuleBasedSlotExtractor(SlotFillingSchema())
        self.dialogue_manager = DialogueManager(
            self.intent_classifier,
            self.slot_extractor,
            SlotFillingSchema(),
            knowledge_base
        )
        
        # 会话管理
        self.sessions: Dict[str, str] = {}  # user_id -> session_id
    
    def chat(self, user_id: str, message: str) -> str:
        """处理用户消息"""
        # 获取或创建会话
        if user_id not in self.sessions:
            self.sessions[user_id] = str(uuid.uuid4())
        
        session_id = self.sessions[user_id]
        
        # 处理消息
        response = self.dialogue_manager.process(session_id, user_id, message)
        
        return response
    
    def reset_session(self, user_id: str):
        """重置会话"""
        if user_id in self.sessions:
            del self.sessions[user_id]

# 使用示例
service = SmartCustomerService()

print("=== 智能客服对话 ===\n")

dialogue = [
    ("user123", "你好"),
    ("user123", "我想查一下订单"),
    ("user123", "订单号是ORD123456"),
    ("user123", "好的"),
    ("user123", "谢谢，再见"),
]

for user_id, message in dialogue:
    print(f"用户: {message}")
    response = service.chat(user_id, message)
    print(f"客服: {response}\n")
```

### 11.5.2 Web API

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="智能客服 API")

# 全局客服实例
service = SmartCustomerService(knowledge_base=kb)

class ChatRequest(BaseModel):
    user_id: str
    message: str
    reset: bool = False

class ChatResponse(BaseModel):
    response: str
    session_id: str

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """对话接口"""
    if request.reset:
        service.reset_session(request.user_id)
    
    response = service.chat(request.user_id, request.message)
    
    session_id = service.sessions.get(request.user_id, "")
    
    return ChatResponse(response=response, session_id=session_id)

@app.get("/api/history/{user_id}")
async def get_history(user_id: str):
    """获取对话历史"""
    context = service.dialogue_manager.contexts.get(
        service.sessions.get(user_id, "")
    )
    
    if not context:
        return {"history": []}
    
    return {"history": context.history}

@app.post("/api/reset/{user_id}")
async def reset(user_id: str):
    """重置会话"""
    service.reset_session(user_id)
    return {"status": "reset"}
```

### 11.5.3 前端界面

```html
<!-- customer-service.html -->
<!DOCTYPE html>
<html>
<head>
    <title>智能客服</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; }
        .chat-box { border: 1px solid #ddd; border-radius: 8px; height: 400px; overflow-y: auto; padding: 15px; }
        .message { margin: 10px 0; padding: 10px; border-radius: 8px; }
        .user { background: #e3f2fd; margin-left: 20%; }
        .bot { background: #f5f5f5; margin-right: 20%; }
        .input-area { display: flex; margin-top: 15px; }
        .input-area input { flex: 1; padding: 10px; border: 1px solid #ddd; border-radius: 4px; }
        .input-area button { padding: 10px 20px; background: #1976d2; color: white; border: none; border-radius: 4px; cursor: pointer; }
        .status { font-size: 12px; color: #666; margin-top: 5px; }
    </style>
</head>
<body>
    <h1>🤖 智能客服</h1>
    
    <div id="chatBox" class="chat-box"></div>
    
    <div class="input-area">
        <input type="text" id="messageInput" placeholder="输入您的问题...">
        <button onclick="sendMessage()">发送</button>
    </div>
    
    <script>
        let userId = 'user_' + Math.random().toString(36).substr(2, 9);
        
        function addMessage(text, isUser) {
            const chatBox = document.getElementById('chatBox');
            const div = document.createElement('div');
            div.className = 'message ' + (isUser ? 'user' : 'bot');
            div.textContent = text;
            chatBox.appendChild(div);
            chatBox.scrollTop = chatBox.scrollHeight;
        }
        
        async function sendMessage() {
            const input = document.getElementById('messageInput');
            const message = input.value.trim();
            if (!message) return;
            
            addMessage(message, true);
            input.value = '';
            
            try {
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ user_id: userId, message })
                });
                
                const data = await response.json();
                addMessage(data.response, false);
            } catch (error) {
                addMessage('抱歉，服务暂时不可用。', false);
            }
        }
        
        // 回车发送
        document.getElementById('messageInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') sendMessage();
        });
    </script>
</body>
</html>
```

## 本章小结

本章介绍了智能客服系统的开发：

1. **意图识别**：基于规则和 LLM 的意图分类
2. **槽位填充**：提取关键信息（订单号、电话等）
3. **对话管理**：状态机驱动的对话流程
4. **知识集成**：与知识库结合的回答机制
5. **实战案例**：完整的客服系统实现

下一章我们将学习内容生成与创作助手，掌握批量处理和结构化输出的技术。

---

## 思考与练习

1. **概念理解**：解释意图识别和槽位填充在对话系统中的作用。

2. **实践练习**：实现一个简单的 FAQ 问答机器人。

3. **系统设计**：设计一个多轮对话的客服系统，处理用户投诉。

4. **优化思考**：如何提高意图识别的准确率？

5. **扩展功能**：为客服系统添加转人工功能。
