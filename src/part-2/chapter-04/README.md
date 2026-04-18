# 第4章：大模型技术原理

> 本章将带你了解人工智能从机器学习到深度学习的发展历程，深入理解 Transformer 架构的核心原理，以及大语言模型（LLM）是如何"学会"理解和生成人类语言的。

## 4.1 从机器学习到深度学习

### 4.1.1 人工智能的发展脉络

人工智能（AI）的发展可以追溯到上世纪50年代。1956年的达特茅斯会议被视为人工智能作为独立学科的起点。此后，AI 经历了多次"热潮"与"寒冬"。

**符号主义时代**（1950s-1980s）：研究者们试图用规则和逻辑让计算机"思考"。专家系统是这一时期的代表作——将人类专家的知识整理成规则库，让机器按规则推理。这种方法在特定领域效果不错，但难以泛化，且知识获取成本极高。

**统计学习时代**（1990s-2010s）：随着互联网兴起和数据量爆炸，机器学习开始崭露头角。支持向量机（SVM）、决策树、随机森林等算法相继出现。2010年前后，ImageNet 大规模视觉识别挑战赛启动，深度学习开始爆发。

**深度学习时代**（2012-至今）：2012年，AlexNet 在 ImageNet 挑战赛中以压倒性优势夺冠，卷积神经网络（CNN）一战成名。此后，深度学习在图像、语音、自然语言处理等领域不断突破，最终催生了 GPT、BERT 等大语言模型。

### 4.1.2 机器学习的基本范式

机器学习有三种基本范式：

**监督学习（Supervised Learning）**：模型从标注数据中学习。输入数据有对应的正确输出（标签），模型通过比较预测结果与真实标签来调整参数。分类（如判断邮件是否为垃圾邮件）和回归（如预测房价）是典型任务。

**无监督学习（Unsupervised Learning）**：模型在没有标签的数据中发现规律。聚类（如将用户分群）和降维（如 PCA）是常见任务。自编码器、生成对抗网络（GAN）也属于此类。

**强化学习（Reinforcement Learning）**：智能体通过与环境交互，以最大化累积奖励为目标进行学习。AlphaGo 就是强化学习的杰作。RLHF（基于人类反馈的强化学习）正是训练 ChatGPT 的关键技术。

### 4.1.3 深度学习的革命性突破

深度学习的"深度"指的是神经网络的层数。传统机器学习模型通常只有1-3层，而深度学习模型可以有几十甚至上百层。

```
┌─────────────────────────────────────────────────────────┐
│                    深度神经网络                           │
├─────────────────────────────────────────────────────────┤
│  输入层    隐藏层1    隐藏层2    隐藏层3    输出层       │
│   ●          ●          ●          ●          ●        │
│   ●    →     ●     →     ●     →     ●     →   ●      │
│   ●          ●          ●          ●          ●        │
│   ●          ●          ●          ●          ●        │
│   ●          ●          ●          ●          ●        │
│  特征      抽象特征   更高层抽象   更高层抽象    预测     │
│   ▼          ▼          ▼          ▼          ▼        │
│  词向量   加权组合   语义理解    深层语义      答案      │
└─────────────────────────────────────────────────────────┘
```

深度学习的三大核心组件：

1. **嵌入层（Embedding Layer）**：将离散的高维数据（如单词、图片像素）映射到连续的稠密向量空间。这使得语义相似的对象在向量空间中距离更近。

2. **注意力机制（Attention）**：让模型能够"关注"输入的不同部分。处理一句话时，模型可以同时关注所有词，而不是逐个处理。

3. **残差连接（Residual Connection）**：允许梯度直接流过，缓解深层网络的梯度消失问题，使得训练更深的网络成为可能。

## 4.2 Transformer 架构详解

### 4.2.1 为什么需要 Transformer？

在 Transformer 出现之前，处理序列数据（如文本）主要依赖循环神经网络（RNN）及其变体（LSTM、GRU）。这些模型存在根本性问题：

- **顺序依赖**：必须逐token处理，无法并行
- **长距离依赖困难**：信息需要"记住"走过很长的路径才能传递
- **梯度消失/爆炸**：深层 RNN 训练困难

2017年，Google 在论文《Attention Is All You Need》中提出了 Transformer，完全基于注意力机制，摒弃了循环结构。这些问题迎刃而解：

- **并行计算**：所有token可以同时处理
- **直接建立长距离依赖**：任意两个位置可以直接交互
- **更稳定训练**：梯度传播更顺畅

### 4.2.2 Transformer 的整体架构

```
┌──────────────────────────────────────────────────────────────────┐
│                        Transformer 编码器                        │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│   输入: "今天天气真好"                                            │
│      ↓                                                           │
│   词嵌入 + 位置编码                                               │
│      ↓                                                           │
│   ┌────────────────────────────────────────────────────────┐    │
│   │              Multi-Head Self-Attention                 │    │
│   │  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐                   │    │
│   │  │Head 1│ │Head 2│ │Head 3│ │Head 4│  并行注意力头       │    │
│   │  └──────┘ └──────┘ └──────┘ └──────┘                   │    │
│   └────────────────────────────────────────────────────────┘    │
│      ↓                                                           │
│   Add & Layer Norm（残差 + 层归一化）                            │
│      ↓                                                           │
│   ┌────────────────────────────────────────────────────────┐    │
│   │                    Feed Forward                         │    │
│   │            全连接前馈网络（两层线性变换）                 │    │
│   └────────────────────────────────────────────────────────┘    │
│      ↓                                                           │
│   Add & Layer Norm                                              │
│      ↓                                                           │
│   （可堆叠多层）                                                  │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

对于大语言模型（只有解码器），架构类似但有所简化。

### 4.2.3 核心组件详解

#### 词嵌入与位置编码

**词嵌入（Word Embedding）**：将每个词映射为一个固定长度的向量。"今天"可能变成 `[0.23, -0.45, 0.78, ...]`，"天气"变成 `[-0.12, 0.56, 0.34, ...]`。

```python
import torch
import torch.nn as nn

class TokenEmbedding(nn.Module):
    """词嵌入层：将token ID映射为稠密向量"""
    def __init__(self, vocab_size, embedding_dim):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embedding_dim)
    
    def forward(self, token_ids):
        # token_ids: [batch_size, seq_len]
        return self.embedding(token_ids)  # [batch_size, seq_len, embedding_dim]

class PositionalEncoding(nn.Module):
    """位置编码：为序列中的每个位置添加位置信息"""
    def __init__(self, d_model, max_len=5000):
        super().__init__()
        # 使用正弦和余弦函数编码位置
        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2).float() * (-torch.log(torch.tensor(10000.0)) / d_model))
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        pe = pe.unsqueeze(0)  # [1, max_len, d_model]
        self.register_buffer('pe', pe)
    
    def forward(self, x):
        # x: [batch_size, seq_len, d_model]
        return x + self.pe[:, :x.size(1), :]
```

**位置编码（Positional Encoding）**：由于注意力机制本身不感知位置信息，需要显式添加位置信号。Transformer 使用正弦/余弦函数，让模型能够学习相对位置关系。

#### 缩放点积注意力

注意力机制的核心是**缩放点积注意力（Scaled Dot-Product Attention）**：

```
公式：Attention(Q, K, V) = softmax(QK^T / √d_k) V

其中：
- Q（Query）：查询向量，"我在找什么"
- K（Key）：键向量，"我包含什么信息"
- V（Value）：值向量，"信息的实际内容"
- √d_k：缩放因子，防止点积过大导致梯度消失
```

```python
import torch
import torch.nn.functional as F
import math

def scaled_dot_product_attention(Q, K, V, mask=None):
    """
    缩放点积注意力
    Q, K, V: [batch_size, num_heads, seq_len, d_k]
    """
    d_k = Q.size(-1)
    
    # 计算点积
    scores = torch.matmul(Q, K.transpose(-2, -1)) / math.sqrt(d_k)
    
    # 应用掩码（如padding mask、causal mask）
    if mask is not None:
        scores = scores.masked_fill(mask == 0, float('-inf'))
    
    # softmax归一化
    attention_weights = F.softmax(scores, dim=-1)
    
    # 加权求和
    output = torch.matmul(attention_weights, V)
    
    return output, attention_weights
```

#### 多头注意力

**多头注意力（Multi-Head Attention）**：将 Q、K、V 分别投影到多个子空间，并行计算注意力，最后合并。这让模型能够关注不同类型的关联：

```python
class MultiHeadAttention(nn.Module):
    """多头注意力机制"""
    def __init__(self, d_model, num_heads):
        super().__init__()
        assert d_model % num_heads == 0
        
        self.d_model = d_model
        self.num_heads = num_heads
        self.d_k = d_model // num_heads
        
        # Q, K, V 的线性投影
        self.W_q = nn.Linear(d_model, d_model)
        self.W_k = nn.Linear(d_model, d_model)
        self.W_v = nn.Linear(d_model, d_model)
        self.W_o = nn.Linear(d_model, d_model)
    
    def split_heads(self, x, batch_size):
        """将最后一个维度分割成 num_heads 个头"""
        x = x.view(batch_size, -1, self.num_heads, self.d_k)
        return x.transpose(1, 2)  # [batch, num_heads, seq_len, d_k]
    
    def forward(self, Q, K, V, mask=None):
        batch_size = Q.size(0)
        
        # 线性投影 + 分头
        Q = self.split_heads(self.W_q(Q), batch_size)
        K = self.split_heads(self.W_k(K), batch_size)
        V = self.split_heads(self.W_v(V), batch_size)
        
        # 计算注意力
        attn_output, attn_weights = scaled_dot_product_attention(Q, K, V, mask)
        
        # 合并多头
        attn_output = attn_output.transpose(1, 2).contiguous()
        attn_output = attn_output.view(batch_size, -1, self.d_model)
        
        # 最终线性投影
        output = self.W_o(attn_output)
        
        return output, attn_weights
```

#### 前馈神经网络

每个 Transformer 层还包含一个前馈神经网络（FFN），对每个位置独立进行非线性变换：

```python
class FeedForward(nn.Module):
    """前馈神经网络"""
    def __init__(self, d_model, d_ff, dropout=0.1):
        super().__init__()
        self.linear1 = nn.Linear(d_model, d_ff)
        self.linear2 = nn.Linear(d_ff, d_model)
        self.dropout = nn.Dropout(dropout)
    
    def forward(self, x):
        return self.linear2(self.dropout(F.gelu(self.linear1(x))))
```

### 4.2.4 解码器与语言建模

大语言模型（如 GPT）主要使用 Transformer **解码器**架构。与编码器的区别：

1. **掩码注意力（Causal Mask）**：确保生成第 N 个token时，只能看到前 N-1 个token，不能"偷看"未来。

2. **单向注意力**：从左到右，逐步生成。

```
输入: "<BOS> 今 天 天 气"
掩码:
      ↓
      　 今  天  天  气
      　 ■   ■   ■   ■   （已生成的位置）
      　    ■   ■   ■   ■
      　       ■   ■   ■
      　          ■   ■
      　             ■
      　                （对未来位置的注意力设为 -∞）
```

3. **下一个token预测**：训练时，模型预测下一个token是什么。

```python
class TransformerDecoderLayer(nn.Module):
    """Transformer 解码器层"""
    def __init__(self, d_model, num_heads, d_ff, dropout=0.1):
        super().__init__()
        self.self_attn = MultiHeadAttention(d_model, num_heads)
        self.cross_attn = MultiHeadAttention(d_model, num_heads)  # 可选：编码器-解码器注意力
        self.feed_forward = FeedForward(d_model, d_ff, dropout)
        self.norm1 = nn.LayerNorm(d_model)
        self.norm2 = nn.LayerNorm(d_model)
        self.norm3 = nn.LayerNorm(d_model)
        self.dropout = nn.Dropout(dropout)
    
    def forward(self, x, memory=None, tgt_mask=None):
        # 自注意力（带因果掩码）
        attn_output, _ = self.self_attn(x, x, x, tgt_mask)
        x = self.norm1(x + self.dropout(attn_output))
        
        # 编码器-解码器注意力（如果有编码器输出）
        if memory is not None:
            attn_output, _ = self.cross_attn(x, memory, memory)
            x = self.norm2(x + self.dropout(attn_output))
        
        # 前馈网络
        ff_output = self.feed_forward(x)
        x = self.norm3(x + self.dropout(ff_output))
        
        return x
```

## 4.3 大语言模型的工作原理

### 4.3.1 什么是大语言模型？

大语言模型（Large Language Model, LLM）是一类参数规模巨大（通常数十亿到上千亿）的深度学习模型，专门用于处理和生成自然语言。

**规模带来的涌现能力（Emergent Abilities）**：
- 当模型规模超过某个阈值时，会突然涌现出一些在小模型上没有的能力
- 如复杂推理、多语言理解、代码生成等

### 4.3.2 GPT 系列的技术演进

**GPT-1（2018）**：1.17亿参数，首次证明预训练+微调范式有效

**GPT-2（2019）**：15亿参数，提出"通用语言模型"概念

**GPT-3（2020）**：1750亿参数，In-Context Learning（上下文学习）能力涌现，无需微调即可完成任务

**GPT-3.5 / GPT-4（2023）**：引入RLHF（基于人类反馈的强化学习），大幅提升对齐能力和安全性

### 4.3.3 语言模型的核心能力

**语言理解**：理解文本的含义、情感、意图

**语言生成**：续写、扩写、改写、摘要

**知识推理**：基于已有知识进行逻辑推理、问答

**代码能力**：代码补全、代码解释、代码审查

**工具使用**：调用外部API、搜索、执行代码

### 4.3.4 训练过程

大语言模型的训练通常分为三个阶段：

```
┌─────────────────────────────────────────────────────────────────┐
│                    大语言模型训练流程                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌────────────────┐                                             │
│  │  阶段1: 预训练   │  海量互联网文本（万亿tokens）              │
│  │  Pretraining    │  → 学习通用语言能力、知识、世界常识          │
│  └────────────────┘                                             │
│           ↓                                                      │
│           ↓  模型参数: 随机初始化 → 数十亿参数                    │
│           ↓                                                      │
│  ┌────────────────┐                                             │
│  │  阶段2: 指令微调 │  人工标注的指令数据                         │
│  │  SFT           │  → 学习遵循指令、回答问题                     │
│  └────────────────┘                                             │
│           ↓                                                      │
│           ↓  模型参数: 预训练权重 → 微调                         │
│           ↓                                                      │
│  ┌────────────────┐                                             │
│  │  阶段3: 对齐微调 │  人类反馈（RLHF/DPO）                       │
│  │  Alignment      │  → 更有帮助、更无害、更诚实                 │
│  └────────────────┘                                             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**预训练（Pre-training）**：在大规模无标注文本上训练，通常是"下一个token预测"任务。数据来源包括网页、书籍、代码、论文等。

**监督微调（Supervised Fine-Tuning, SFT）**：在人工标注的指令-响应对上微调，让模型学会遵循指令。

**对齐微调（Alignment）**：使用RLHF（基于人类反馈的强化学习）或DPO（直接偏好优化），让模型的输出更符合人类偏好。

### 4.3.5 Tokenization：模型如何理解文本

模型无法直接处理原始文本，需要先将文本转换为数字。这个过程叫做**分词（Tokenization）**。

```python
# 使用 transformers 库进行分词
from transformers import AutoTokenizer

tokenizer = AutoTokenizer.from_pretrained("qwen/Qwen2.5-7B")

text = "今天天气真好，适合出去散步！"

# 分词
tokens = tokenizer.tokenize(text)
print(f"原始文本: {text}")
print(f"分词结果: {tokens}")

# 转换为token IDs
token_ids = tokenizer.encode(text)
print(f"Token IDs: {token_ids}")

# 解码回来
decoded = tokenizer.decode(token_ids)
print(f"解码结果: {decoded}")

# 统计token数量
num_tokens = len(token_ids)
print(f"Token 数量: {num_tokens}")

# 输出示例：
# 原始文本: 今天天气真好，适合出去散步！
# 分词结果: ['今', '天', '天', '气', '真', '好', '，', '适', '合', '出', '去', '散', '步', '！']
# Token IDs: [514, 1824, 1824, 2175, 3932, 3121, 27, 6435, 3131, 1216, 2675, 6365, 1313, 31]
# 解码结果: 今天天气真好，适合出去散步！
# Token 数量: 14
```

不同的分词器效率不同：
- 中英文混合时，一个汉字通常对应1-2个token
- 英文单词可能被拆成多个子词（如"learning" → "learn" + "ing"）

### 4.3.6 模型推理：如何生成文本

语言模型的推理是一个**自回归（Autoregressive）**过程：每次生成一个token，然后将新token加入输入，继续生成下一个。

```python
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

def generate_text(
    model_name: str,
    prompt: str,
    max_new_tokens: int = 100,
    temperature: float = 0.7,
    top_p: float = 0.9
) -> str:
    """使用语言模型生成文本"""
    # 加载模型和分词器
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch.float16,
        device_map="auto"
    )
    
    # 输入编码
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    
    # 生成
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            temperature=temperature,  # 控制随机性
            top_p=top_p,              # 核采样
            do_sample=True,           # 启用采样（否则用贪婪）
            pad_token_id=tokenizer.pad_token_id
        )
    
    # 解码输出
    generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
    
    return generated_text

# 使用示例
prompt = "用Python写一个快速排序算法："
result = generate_text("qwen/Qwen2.5-7B", prompt)
print(result)
```

**采样策略**：

- **贪婪解码（Greedy Decoding）**：每个step选择概率最高的token。速度快，但容易陷入重复。

- **温度采样（Temperature Sampling）**：用温度参数调整概率分布。温度高→更随机；温度低→更确定性。

- **Top-K 采样**：限制只在概率最高的K个token中采样。

- **Top-P（Nucleus）采样**：限制在累积概率达到P的最小token集合中采样。通常效果更好。

## 4.4 主流大模型盘点

### 4.4.1 国际主流模型

| 模型 | 开发者 | 参数量 | 特点 |
|------|--------|--------|------|
| GPT-4o | OpenAI | ~1.8万亿 | 多模态，强推理，已开源语音 |
| Claude 3.5 | Anthropic | 未公开 | 长上下文，安全性强 |
| Gemini 1.5 | Google | 未公开 | 超长上下文（100万token） |
| Llama 3 | Meta | 8B/70B | 开源，社区活跃 |
| Mistral | Mistral AI | 7B/8x22B | 高效率，专家混合架构 |

### 4.4.2 国内主流模型

| 模型 | 开发者 | 特点 |
|------|--------|------|
| 通义千问 Qwen | 阿里云 | 开源系列，中文优化 |
| 文心一言 | 百度 | 知识增强 |
| 智谱 GLM | 智谱AI | ChatGLM系列 |
| 讯飞星火 | 科大讯飞 | 语音交互强 |
| Kimi (Moonshot) | 月之暗面 | 超长上下文 |
| DeepSeek | 深度求索 | 高性价比，开源 |

### 4.4.3 模型选择指南

```
┌─────────────────────────────────────────────────────────────────┐
│                        模型选择决策树                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│                    ┌───────────────────┐                        │
│                    │   你的应用场景？    │                        │
│                    └─────────┬─────────┘                        │
│                              │                                  │
│          ┌───────────────────┼───────────────────┐             │
│          ↓                   ↓                   ↓             │
│    ┌───────────┐      ┌───────────┐       ┌───────────┐         │
│    │ 通用对话  │      │ 专用任务  │       │ 本地部署  │         │
│    │ 智能客服  │      │ 代码生成  │       │ 私有化    │         │
│    └─────┬─────┘      │ 知识问答  │       └─────┬─────┘         │
│          ↓            └─────┬─────┘             ↓              │
│    ┌───────────┐      ┌───────────┐       ┌───────────┐       │
│    │ API调用   │      │ Fine-tune │       │ 开源模型  │       │
│    │ Qwen/GLM │      │ Qwen/LLaMA│       │ LLaMA/Mistral│     │
│    └───────────┘      └───────────┘       └───────────┘       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## 本章小结

本章介绍了大语言模型的技术基础：

1. **AI发展脉络**：从符号主义到统计学习，再到深度学习
2. **Transformer架构**：自注意力机制、多头注意力、位置编码
3. **大模型原理**：预训练-微调范式、涌现能力、自回归生成
4. **主流模型**：国际与国内代表性模型及选型建议

理解这些基础原理，将帮助你更好地使用和优化大模型应用。下一章我们将具体介绍阿里云的大模型产品体系。

---

## 思考与练习

1. **概念理解**：Transformer 的注意力机制相比 RNN 有哪些优势？

2. **原理分析**：为什么大模型需要进行"对齐微调"（RLHF）？这解决了什么问题？

3. **实践探索**：使用 transformers 库加载一个小模型（如 GPT-2），观察不同采样策略（贪婪、温度、Top-P）对生成结果的影响。

4. **扩展思考**：大语言模型有哪些局限性？在实际应用中应该如何规避？

5. **选型设计**：为一个校园问答助手系统选择合适的大模型，说明理由。
