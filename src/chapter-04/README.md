# 第 4 章 RAG 应用架构与实战

> **本章导读**
> 
> 检索增强生成（Retrieval-Augmented Generation，RAG）是解决大模型幻觉问题、提升专业知识准确性的核心技术。本章将深入讲解 RAG 系统的整体架构、知识库构建流程、向量检索优化、文档切分策略等关键议题，并提供基于阿里云百炼平台和 DashVector 的完整实现方案。
> 
> **核心议题：**
> - RAG 技术原理与适用场景
> - 知识库构建全流程（文档采集、清洗、切分、向量化）
> - 向量数据库选型与 DashVector 实战
> - 检索优化策略（混合检索、重排序、多跳检索）
> - 企业级 RAG 系统案例分析

---

## 4.1 RAG 技术概述

### 4.1.1 为什么需要 RAG？

大语言模型虽然强大，但存在三个固有局限：

**局限一：知识截止**
- 训练数据有明确的时间截止点
- 无法获知训练后的新信息
- 例如：GPT-4 的知识截止到 2024 年 4 月

**局限二：私有知识缺失**
- 训练数据来自公开互联网
- 不包含企业内部文档、产品手册、客户案例等私有信息
- 无法回答涉及公司内部流程的问题

**局限三：幻觉问题**
- 面对不确定的问题时倾向于"编造"答案
- 在医疗、法律、金融等专业领域风险极高
- 难以追溯答案的信息来源

RAG 技术通过"先检索后生成"的机制，有效解决了上述问题：

```
用户提问 → 检索相关知识 → 增强 Prompt → 大模型生成 → 带引用的答案
```

### 4.1.2 RAG 工作流程

标准的 RAG 工作流程包含两个阶段：

**阶段一：离线知识库构建**
```
文档采集 → 文本提取 → 数据清洗 → 文档切分 → 向量化 → 存储到向量数据库
```

**阶段二：在线检索增强**
```
用户提问 → 问题向量化 → 相似度检索 → Top-K 召回 → (可选) 重排序 → 拼接 Prompt → 大模型生成
```

### 4.1.3 阿里云百炼 RAG 架构

阿里云百炼平台提供了一站式的 RAG 解决方案，核心组件包括：

| 组件 | 功能 | 对应产品 |
|-----|------|---------|
| 文档处理 | PDF/Word/Excel 解析、OCR、文本清洗 | 百炼数据处理服务 |
| 向量化 | 文本 embedding、多语言支持 | text-embedding-v2/v3 |
| 向量存储 | 高维向量索引、相似度检索 | DashVector / 阿里云 Milvus 版 |
| 检索引擎 | 语义检索、混合检索、多路召回 | 百炼检索服务 |
| 生成模型 | 基于检索结果生成答案 | Qwen 系列模型 |

---

## 4.2 知识库构建

### 4.2.1 文档采集

企业知识通常分散在多种载体中：

**常见文档类型：**
- Office 文档：Word、PPT、Excel
- PDF 文件：产品手册、技术文档、合同
- 网页内容：官网 FAQ、帮助中心
- 数据库记录：工单系统、CRM、知识库
- 即时通讯：钉钉聊天记录、邮件往来

**采集方式：**

```python
# 示例：多种文档类型的文本提取
from langchain.document_loaders import (
    PyPDFLoader,
    Docx2txtLoader,
    UnstructuredMarkdownLoader,
    WebBaseLoader
)

# PDF 加载
pdf_loader = PyPDFLoader("product_manual.pdf")
pdf_docs = pdf_loader.load()

# Word 加载
docx_loader = Docx2txtLoader("specifications.docx")
docx_docs = docx_loader.load()

# 网页加载
web_loader = WebBaseLoader("https://help.example.com/faq")
web_docs = web_loader.load()

# 合并所有文档
all_docs = pdf_docs + docx_docs + web_docs
print(f"共加载 {len(all_docs)} 个文档片段")
```

### 4.2.2 数据清洗

原始文档通常包含大量噪声，需要清洗：

**常见噪声类型：**
- 页眉页脚、页码
- 广告、导航菜单
- 特殊字符、乱码
- 无意义的短文本
- 重复内容

**清洗策略：**

```python
import re

def clean_text(text):
    # 移除多余空白
    text = re.sub(r'\s+', ' ', text).strip()
    
    # 移除页眉页脚（假设格式固定）
    text = re.sub(r'^第\d+页.*', '', text, flags=re.MULTILINE)
    
    # 移除特殊字符
    text = re.sub(r'[^\w\s\u4e00-\u9fff.,!?;:()""\'\-]', '', text)
    
    # 移除过短片段（少于 10 字）
    if len(text) < 10:
        return None
    
    return text

# 批量清洗
cleaned_docs = []
for doc in all_docs:
    cleaned_text = clean_text(doc.page_content)
    if cleaned_text:
        doc.page_content = cleaned_text
        cleaned_docs.append(doc)

print(f"清洗后剩余 {len(cleaned_docs)} 个有效片段")
```

### 4.2.3 文档切分

合理的切分策略直接影响检索效果：

**切分原则：**
- 保持语义完整性（不要在句子中间切断）
- 控制片段长度（通常 200-500 字）
- 设置重叠区域（避免上下文丢失）
- 考虑文档结构（按章节、段落切分）

**常用切分方法：**

```python
from langchain.text_splitter import (
    CharacterTextSplitter,
    RecursiveCharacterTextSplitter,
    MarkdownHeaderTextSplitter
)

# 方法 1：按字符切分（简单但可能切断语义）
splitter1 = CharacterTextSplitter(
    separator="\n",
    chunk_size=300,
    chunk_overlap=50
)

# 方法 2：递归字符切分（推荐）
splitter2 = RecursiveCharacterTextSplitter(
    separators=["\n\n", "\n", "。", "！", "？", " ", ""],
    chunk_size=300,
    chunk_overlap=50,
    length_function=len
)

# 方法 3：按 Markdown 结构切分
splitter3 = MarkdownHeaderTextSplitter(
    headers_to_split_on=[
        ("#", "Header 1"),
        ("##", "Header 2"),
        ("###", "Header 3")
    ]
)

# 执行切分
chunks = splitter2.split_documents(cleaned_docs)
print(f"切分为 {len(chunks)} 个片段")
print(f"平均长度：{sum(len(c.page_content) for c in chunks) / len(chunks):.0f} 字")
```

### 4.2.4 向量化（Embedding）

将文本转换为高维向量：

**阿里云 Embedding 模型：**

| 模型 | 维度 | 最大输入 | 特点 |
|-----|------|---------|------|
| text-embedding-v2 | 1536 | 512 tokens | 通用场景，性价比高 |
| text-embedding-v3 | 2048 | 8192 tokens | 高精度，支持多语言 |

**向量化代码示例：**

```python
import dashscope
from dashscope import TextEmbedding

dashscope.api_key = "sk-xxx"

def get_embedding(text):
    response = TextEmbedding.call(
        model='text-embedding-v3',
        input=text
    )
    if response.status_code == 200:
        return response.output['embeddings'][0]['embedding']
    else:
        raise Exception(f"Embedding 失败：{response.message}")

# 批量向量化
for chunk in chunks:
    chunk.vector = get_embedding(chunk.page_content)
```

### 4.2.5 向量存储

使用向量数据库存储和索引：

**DashVector 快速入门：**

```python
from dashvector import Client, Doc

# 初始化客户端
client = Client(api_key="sk-xxx", endpoint="https://xxx.dashvector.aliyuncs.com")

# 创建集合（Collection）
client.create(
    name='knowledge_base',
    dimension=2048,  # 与 embedding 维度一致
    metric='cosine'  # 余弦相似度
)

# 插入文档
docs = [
    Doc(
        id=f"doc_{i}",
        vector=chunk.vector,
        fields={
            'content': chunk.page_content,
            'source': chunk.metadata.get('source', ''),
            'page': chunk.metadata.get('page', 0)
        }
    )
    for i, chunk in enumerate(chunks)
]

collection = client.get('knowledge_base')
collection.upsert(docs)
print(f"成功插入 {len(docs)} 条向量")
```

---

## 4.3 检索优化策略

### 4.3.1 相似度检索

基础向量检索：

```python
def search(query, top_k=5):
    # 问题向量化
    query_vector = get_embedding(query)
    
    # 相似度检索
    collection = client.get('knowledge_base')
    result = collection.query(
        vector=query_vector,
        topk=top_k,
        include_fields=['content', 'source']
    )
    
    return [doc.fields['content'] for doc in result.docs]

# 使用示例
contexts = search("如何重置密码？", top_k=5)
```

### 4.3.2 混合检索（Hybrid Search）

结合语义检索和关键词检索的优势：

```python
from elasticsearch import Elasticsearch

# ES 关键词检索
es = Elasticsearch("http://localhost:9200")

def hybrid_search(query, top_k=5):
    # 1. 向量检索
    query_vector = get_embedding(query)
    vector_results = collection.query(
        vector=query_vector,
        topk=top_k * 2
    )
    
    # 2. 关键词检索
    es_results = es.search(
        index="knowledge_base",
        query={
            "multi_match": {
                "query": query,
                "fields": ["content", "title"]
            }
        },
        size=top_k * 2
    )
    
    # 3. 结果融合（RRF 倒数排名融合）
    fused_scores = {}
    for rank, doc in enumerate(vector_results.docs):
        doc_id = doc.id
        fused_scores[doc_id] = fused_scores.get(doc_id, 0) + 1 / (rank + 1)
    
    for rank, hit in enumerate(es_results['hits']['hits']):
        doc_id = hit['_id']
        fused_scores[doc_id] = fused_scores.get(doc_id, 0) + 1 / (rank + 1)
    
    # 4. 取 Top-K
    sorted_docs = sorted(fused_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
    
    return sorted_docs
```

### 4.3.3 重排序（Re-ranking）

对初筛结果进行精细排序：

```python
from dashscope import TextRank

def rerank(query, documents, top_k=3):
    """
    使用 Cross-Encoder 模型对文档重排序
    """
    response = TextRank.call(
        model='gte-rerank',
        query=query,
        docs=[doc for doc in documents]
    )
    
    # 获取排序后的索引
    ranked_indices = [item['index'] for item in response.output['results']]
    
    # 返回 Top-K
    return [documents[i] for i in ranked_indices[:top_k]]

# 完整流程
initial_results = hybrid_search(query, top_k=10)
final_results = rerank(query, initial_results, top_k=5)
```

### 4.3.4 多跳检索（Multi-hop Retrieval）

对于复杂问题，可能需要多次检索：

```python
def multi_hop_search(question, max_hops=3):
    contexts = []
    current_question = question
    
    for hop in range(max_hops):
        # 第 1 跳：检索
        results = search(current_question, top_k=3)
        contexts.extend(results)
        
        # 判断是否需要继续检索
        synthesis_prompt = f"""
        基于以下信息，能否完整回答问题？
        
        问题：{question}
        已有信息：{''.join(results)}
        
        如果信息充足，回复"充足"；否则，指出还需要什么信息。
        """
        
        llm_response = call_qwen(synthesis_prompt)
        
        if "充足" in llm_response:
            break
        else:
            # 生成下一跳的检索问题
            next_query_prompt = f"""
            为了回答问题：{question}
            还需要补充什么信息？请生成一个具体的检索问题。
            """
            current_question = call_qwen(next_query_prompt)
    
    return contexts
```

---

## 4.4 完整 RAG 系统实现

### 4.4.1 系统架构

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   用户界面   │────▶│  API Gateway  │────▶│  应用服务   │
│ (Web/App)   │◀────│              │◀────│  (Flask)    │
└─────────────┘     └──────────────┘     └──────┬──────┘
                                                 │
                    ┌────────────────────────────┼────────────────────────────┐
                    │                            │                            │
             ┌──────▼──────┐            ┌───────▼───────┐           ┌───────▼───────┐
             │  向量数据库  │            │   关系数据库   │           │   大模型 API   │
             │ DashVector  │            │  MySQL/RDS    │           │  百炼 Qwen    │
             └─────────────┘            └───────────────┘           └───────────────┘
```

### 4.4.2 核心代码

```python
from flask import Flask, request, jsonify
from dashscope import Generation
import dashvector

app = Flask(__name__)

# 初始化客户端
dv_client = dashvector.Client(api_key="xxx", endpoint="xxx")
collection = dv_client.get('knowledge_base')

@app.route('/api/rag/query', methods=['POST'])
def rag_query():
    data = request.json
    question = data.get('question', '')
    
    if not question:
        return jsonify({'error': '问题不能为空'}), 400
    
    # 1. 问题向量化
    query_vector = get_embedding(question)
    
    # 2. 检索 Top-5 相关文档
    result = collection.query(
        vector=query_vector,
        topk=5,
        include_fields=['content', 'source']
    )
    
    contexts = [doc.fields['content'] for doc in result.docs]
    sources = [doc.fields['source'] for doc in result.docs]
    
    # 3. 构建增强 Prompt
    prompt = build_rag_prompt(question, contexts)
    
    # 4. 调用大模型生成答案
    response = Generation.call(
        model='qwen3.6-plus',
        messages=[{'role': 'user', 'content': prompt}],
        temperature=0.7
    )
    
    answer = response.output.choices[0].message.content
    
    # 5. 返回结果
    return jsonify({
        'answer': answer,
        'contexts': contexts,
        'sources': list(set(sources)),
        'model': 'qwen3.6-plus'
    })

def build_rag_prompt(question, contexts):
    context_text = "\n\n".join([f"[资料{i+1}]\n{ctx}" for i, ctx in enumerate(contexts)])
    
    return f"""基于以下参考资料，回答问题。如果资料中没有答案，请如实告知。

参考资料：
{context_text}

问题：{question}

回答："""

if __name__ == '__main__':
    app.run(debug=True, port=5000)
```

---

## 本章小结

本章深入讲解了 RAG 技术的原理与实战：

1. **RAG 价值**：解决大模型的知识截止、私有知识缺失、幻觉三大问题
2. **知识库构建**：文档采集→清洗→切分→向量化→存储的完整流程
3. **检索优化**：混合检索、重排序、多跳检索等多种提升精度的策略
4. **系统实现**：基于阿里云百炼和 DashVector 的企业级 RAG 架构

RAG 已成为企业构建专业知识问答系统的首选方案，掌握这项技术对于技术决策者至关重要。

---

## 延伸阅读

1. [阿里云百炼知识库官方文档](https://help.aliyun.com/zh/model-studio/knowledge-base)
2. [DashVector 向量数据库](https://help.aliyun.com/zh/dashvector/)
3. 《Retrieval-Augmented Generation for Large Language Models》- Facebook AI
4. LangChain RAG 最佳实践：https://python.langchain.com/docs/use_cases/retrievers

---

**下一章预告**：第 5 章将探讨 Agent 应用架构与实战，包括 Agent 的核心组件、规划能力、工具调用、记忆机制，以及基于阿里云百炼的 Agent 开发框架。