# 第10章：企业知识库问答

> 本章介绍如何构建基于企业知识库的智能问答系统（RAG架构）。从文档处理、向量化、语义检索，到完整的 RAG 流水线，帮助你构建精准、可信赖的 AI 问答系统。

## 10.1 RAG 架构概述

### 10.1.1 什么是 RAG？

**RAG = Retrieval-Augmented Generation（检索增强生成）**

传统的 LLM 有两个主要问题：
- **知识陈旧**：训练数据有截止日期，无法获取最新信息
- **幻觉问题**：可能产生看似合理但错误的答案

RAG 通过检索外部知识来增强 LLM 的能力：

```
┌─────────────────────────────────────────────────────────────────┐
│                      RAG 架构                                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   用户问题 ──►                                                    │
│      │                                                           │
│      ▼                                                           │
│   ┌──────────────┐                                               │
│   │   检索       │ ◄── 知识库（向量数据库）                       │
│   │ (Retrieval) │                                               │
│   └──────┬───────┘                                               │
│          │                                                       │
│          ▼                                                       │
│   ┌──────────────┐                                               │
│   │    增强      │ ◄── 原始问题                                  │
│   │  (Augment)   │                                               │
│   └──────┬───────┘                                               │
│          │                                                       │
│          ▼                                                       │
│   ┌──────────────┐                                               │
│   │    生成      │                                               │
│   │ (Generate)   │                                               │
│   └──────┬───────┘                                               │
│          │                                                       │
│          ▼                                                       │
│      最终答案                                                     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 10.1.2 RAG 核心组件

| 组件 | 职责 |
|------|------|
| **文档加载器** | 读取各种格式的文档（PDF、Word、Markdown等） |
| **文本分割器** | 将长文档分割成适合的片段 |
| **向量化模型** | 将文本转换为向量表示 |
| **向量数据库** | 存储和检索向量 |
| **检索器** | 根据问题检索相关文档 |
| **生成器** | LLM 基于检索结果生成答案 |

### 10.1.3 RAG 应用场景

- 企业内部知识库问答
- 客服机器人
- 文档摘要和问答
- 论文/报告分析
- 法规政策查询

## 10.2 文档处理与向量化

### 10.2.1 安装依赖

```bash
pip install langchain langchain-community pypdf python-docx markdown dashscope faiss-cpu
```

### 10.2.2 文档加载

```python
from langchain.document_loaders import (
    PyPDFLoader,          # PDF
    UnstructuredWordDocumentLoader,  # Word
    TextLoader,           # 文本文件
    MarkdownLoader        # Markdown
)
from langchain.schema import Document

def load_documents(file_path: str) -> list:
    """
    加载文档
    
    Args:
        file_path: 文档路径
    
    Returns:
        文档列表
    """
    if file_path.endswith('.pdf'):
        loader = PyPDFLoader(file_path)
    elif file_path.endswith('.docx'):
        loader = UnstructuredWordDocumentLoader(file_path)
    elif file_path.endswith('.md'):
        loader = MarkdownLoader(file_path)
    else:
        loader = TextLoader(file_path)
    
    documents = loader.load()
    return documents

# 使用示例
docs = load_documents("knowledgebase/manual.pdf")
print(f"加载了 {len(docs)} 页")
print(f"内容预览: {docs[0].page_content[:200]}...")
```

### 10.2.3 文本分割

```python
from langchain.text_splitter import (
    RecursiveCharacterTextSplitter,
    CharacterTextSplitter,
    TokenTextSplitter
)

def split_documents(
    documents: list,
    chunk_size: int = 500,
    chunk_overlap: int = 50
) -> list:
    """
    分割文档
    
    Args:
        documents: 文档列表
        chunk_size: 块大小（字符数）
        chunk_overlap: 块重叠大小
    
    Returns:
        分割后的文档块
    """
    # 使用递归字符分割器
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        # 自定义分割符
        separators=["\n\n", "\n", "。", "！", "？", " ", ""]
    )
    
    splits = text_splitter.split_documents(documents)
    return splits

# 使用示例
splits = split_documents(docs, chunk_size=500, chunk_overlap=50)
print(f"分割成 {len(splits)} 个块")
```

### 10.2.4 向量化与存储

```python
from langchain.embeddings import DashScopeEmbeddings
from langchain.vectorstores import FAISS

class KnowledgeBase:
    """知识库类"""
    
    def __init__(self):
        self.embeddings = DashScopeEmbeddings(
            model="text-embedding-v3",
            dashscope_api_key=os.getenv("DASHSCOPE_API_KEY")
        )
        self.vectorstore = None
        self.documents = []
    
    def add_documents(self, documents: list):
        """
        添加文档到知识库
        
        Args:
            documents: 文档列表
        """
        # 分割文档
        splits = split_documents(documents)
        
        # 创建向量存储
        self.vectorstore = FAISS.from_documents(
            documents=splits,
            embedding=self.embeddings
        )
        
        self.documents.extend(splits)
        print(f"已添加 {len(splits)} 个文档块到知识库")
    
    def similarity_search(self, query: str, k: int = 4) -> list:
        """
        相似度搜索
        
        Args:
            query: 查询文本
            k: 返回数量
        
        Returns:
            相关文档列表
        """
        if not self.vectorstore:
            return []
        
        results = self.vectorstore.similarity_search(query, k=k)
        return results
    
    def save(self, path: str):
        """保存向量数据库"""
        if self.vectorstore:
            self.vectorstore.save_local(path)
            print(f"知识库已保存到 {path}")
    
    def load(self, path: str):
        """加载向量数据库"""
        if os.path.exists(path):
            self.vectorstore = FAISS.load_local(
                path,
                self.embeddings,
                allow_dangerous_deserialization=True
            )
            print(f"知识库已从 {path} 加载")

# 使用示例
kb = KnowledgeBase()

# 添加文档
docs = load_documents("knowledgebase/company_policy.pdf")
kb.add_documents(docs)

# 保存
kb.save("vectorstore/company_policy")

# 搜索
results = kb.similarity_search("年假政策是什么？", k=3)
for i, doc in enumerate(results, 1):
    print(f"\n【结果 {i}】")
    print(doc.page_content)
```

## 10.3 语义检索技术

### 10.3.1 检索策略

```python
class SemanticSearch:
    """语义检索器"""
    
    def __init__(self, vectorstore):
        self.vectorstore = vectorstore
    
    def basic_search(self, query: str, k: int = 4) -> list:
        """基础相似度搜索"""
        return self.vectorstore.similarity_search(query, k=k)
    
    def mmr_search(
        self,
        query: str,
        k: int = 4,
        fetch_k: int = 10,
        lambda_mult: float = 0.5
    ) -> list:
        """
        最大边际相关性搜索（MMR）
        
        MMR 可以增加检索结果的多样性，避免返回内容重复的文档。
        
        Args:
            query: 查询文本
            k: 返回数量
            fetch_k: 初始检索数量
            lambda_mult: 多样性参数（0=只取最相似，1=最大多样性）
        """
        results = self.vectorstore.max_marginal_relevance_search(
            query,
            k=k,
            fetch_k=fetch_k,
            lambda_mult=lambda_mult
        )
        return results
    
    def hybrid_search(
        self,
        query: str,
        k: int = 4,
        alpha: float = 0.5
    ) -> list:
        """
        混合搜索（语义 + 关键词）
        
        Args:
            query: 查询文本
            k: 返回数量
            alpha: 混合权重（0=纯关键词，1=纯语义）
        """
        # 这里简化实现，实际项目可以使用混合检索库
        semantic_results = self.basic_search(query, k * 2)
        
        # 简单重排序
        scored_results = []
        for i, doc in enumerate(semantic_results):
            # 简单评分（实际应该使用 BM25 + 向量相似度的混合）
            score = (1 - alpha) * (i / len(semantic_results)) + alpha * (1 - i / len(semantic_results))
            scored_results.append((score, doc))
        
        scored_results.sort(key=lambda x: x[0], reverse=True)
        return [doc for _, doc in scored_results[:k]]

# 使用示例
searcher = SemanticSearch(kb.vectorstore)

# 基础搜索
basic_results = searcher.basic_search("如何使用公司邮箱？")

# MMR 搜索（更多样）
mmr_results = searcher.mmr_search("如何使用公司邮箱？")
```

### 10.3.2 重排序（Reranking）

```python
from dashscope import Rerank

class Reranker:
    """重排序器"""
    
    def __init__(self):
        self.rerank_model = "gte-rerank"
    
    def rerank(
        self,
        query: str,
        documents: list,
        top_n: int = 3
    ) -> list:
        """
        重排序检索结果
        
        Args:
            query: 查询文本
            documents: 文档列表（可以是 Document 对象或字符串）
            top_n: 返回数量
        
        Returns:
            重排序后的结果
        """
        # 提取文档内容
        doc_texts = [
            doc.page_content if hasattr(doc, 'page_content') else str(doc)
            for doc in documents
        ]
        
        # 调用重排序 API
        response = Rerank.call(
            model=self.rerank_model,
            query=query,
            documents=doc_texts,
            top_n=top_n
        )
        
        if response.status_code != 200:
            return documents[:top_n]
        
        # 按相关性排序
        results = []
        for item in response.output.results:
            results.append({
                "index": item.index,
                "document": doc_texts[item.index],
                "score": item.relevance_score
            })
        
        # 返回排序后的文档
        reranked = [documents[r["index"]] for r in results]
        return reranked

# 使用示例
reranker = Reranker()
initial_results = searcher.basic_search("年假怎么申请？", k=10)
final_results = reranker.rerank("年假怎么申请？", initial_results, top_n=3)
```

### 10.3.3 查询扩展

```python
class QueryExpander:
    """查询扩展器"""
    
    def __init__(self, client):
        self.client = client
    
    def expand_query(self, query: str) -> str:
        """
        扩展查询：生成多个相关查询
        
        Returns:
            扩展后的查询字符串
        """
        prompt = f"""
请为以下查询生成3个不同的表述方式，以帮助更全面地检索信息。

原始查询：{query}

要求：
1. 保持原意
2. 使用不同的表述角度
3. 可以包含同义词、上下位词

输出格式：
1. [扩展查询1]
2. [扩展查询2]
3. [扩展查询3]
"""
        response = self.client.chat(prompt)
        
        # 解析扩展查询
        expanded = [query]  # 包含原查询
        for line in response["message"].split('\n'):
            line = line.strip()
            if line and line[0].isdigit() and '.' in line[:3]:
                expanded.append(line.split('.', 1)[-1].strip())
        
        return expanded
    
    def multi_query_search(self, query: str, searcher: SemanticSearch) -> list:
        """
        多查询搜索：使用扩展的多个查询进行搜索
        
        Args:
            query: 原始查询
            searcher: 搜索引擎
        
        Returns:
            去重后的搜索结果
        """
        # 扩展查询
        expanded_queries = self.expand_query(query)
        
        # 收集所有结果
        all_results = []
        seen_contents = set()
        
        for q in expanded_queries:
            results = searcher.basic_search(q, k=5)
            for doc in results:
                # 去重
                content_hash = hash(doc.page_content)
                if content_hash not in seen_contents:
                    seen_contents.add(content_hash)
                    all_results.append(doc)
        
        return all_results

# 使用示例
expander = QueryExpander(ai_client)
multi_results = expander.multi_query_search("年假政策", searcher)
```

## 10.4 RAG 流水线实现

### 10.4.1 完整 RAG 实现

```python
from typing import List, Optional
from dataclasses import dataclass
from langchain.schema import Document

@dataclass
class RAGResult:
    """RAG 结果"""
    answer: str
    source_documents: List[Document]
    query: str
    retrieval_time: float

class RAGPipeline:
    """RAG 流水线"""
    
    def __init__(
        self,
        vectorstore,
        llm_client,
        reranker: Optional[Reranker] = None,
        top_k: int = 5,
        final_k: int = 3
    ):
        self.vectorstore = vectorstore
        self.llm_client = llm_client
        self.reranker = reranker
        self.top_k = top_k
        self.final_k = final_k
    
    def retrieve(self, query: str) -> List[Document]:
        """检索相关文档"""
        # 基础检索
        results = self.vectorstore.similarity_search(query, k=self.top_k)
        
        # 重排序（如果可用）
        if self.reranker:
            results = self.reranker.rerank(query, results, top_n=self.final_k)
        else:
            results = results[:self.final_k]
        
        return results
    
    def augment(self, query: str, documents: List[Document]) -> str:
        """构建增强后的 prompt"""
        context = "\n\n".join([
            f"【文档 {i+1}】\n{doc.page_content}"
            for i, doc in enumerate(documents)
        ])
        
        prompt = f"""基于以下参考资料回答问题。如果资料中没有相关信息，请如实说明。

【参考资料】
{context}

【问题】
{query}

【回答要求】
1. 基于资料内容回答，不要编造信息
2. 如果涉及多个文档，可以综合回答
3. 回答要清晰、有条理
4. 如有必要，可以在回答中引用"根据文档X"
"""
        return prompt
    
    def generate(self, query: str, documents: List[Document]) -> str:
        """生成答案"""
        prompt = self.augment(query, documents)
        
        response = self.llm_client.chat(
            prompt,
            system_prompt="你是一个知识库问答助手，基于给定的资料回答问题。"
        )
        
        return response["message"]
    
    def run(self, query: str) -> RAGResult:
        """运行完整的 RAG 流程"""
        import time
        
        start_time = time.time()
        
        # 1. 检索
        documents = self.retrieve(query)
        retrieval_time = time.time() - start_time
        
        # 2. 生成
        if documents:
            answer = self.generate(query, documents)
        else:
            answer = "抱歉，知识库中没有找到相关信息。"
        
        return RAGResult(
            answer=answer,
            source_documents=documents,
            query=query,
            retrieval_time=retrieval_time
        )

# 使用示例
rag_pipeline = RAGPipeline(
    vectorstore=kb.vectorstore,
    llm_client=ai_client,
    reranker=reranker,
    top_k=10,
    final_k=3
)

result = rag_pipeline.run("公司年假政策是什么？")

print(f"问题: {result.query}")
print(f"答案: {result.answer}")
print(f"检索耗时: {result.retrieval_time:.3f}s")
print(f"\n参考文档:")
for i, doc in enumerate(result.source_documents, 1):
    print(f"{i}. {doc.page_content[:100]}...")
```

### 10.4.2 带历史记录的 RAG

```python
class ConversationalRAG:
    """对话式 RAG"""
    
    def __init__(self, rag_pipeline: RAGPipeline):
        self.rag_pipeline = rag_pipeline
        self.conversation_history = []
    
    def run(self, query: str) -> RAGResult:
        """运行对话式 RAG"""
        # 构建完整查询（包含历史）
        full_query = self._build_query_with_history(query)
        
        # 运行 RAG
        result = self.rag_pipeline.run(full_query)
        
        # 保存历史
        self.conversation_history.append({
            "query": query,
            "answer": result.answer
        })
        
        return result
    
    def _build_query_with_history(self, query: str) -> str:
        """结合历史对话构建完整查询"""
        if not self.conversation_history:
            return query
        
        # 最近一轮对话
        last = self.conversation_history[-1]
        
        # 构建查询
        history_summary = f"""
【上一轮对话】
用户问：{last['query']}
助手答：{last['answer']}

【当前问题】
{query}
"""
        
        # 使用 LLM 理解上下文
        expanded_query = self.rag_pipeline.llm_client.chat(
            f"""基于以下对话历史，理解用户的当前问题。

{history_summary}

请将当前问题改写成一个完整的、独立的查询，
确保不依赖对话历史也能理解问题。

只输出改写后的查询，不要其他内容。
"""
        )
        
        return expanded_query["message"]

# 使用示例
conv_rag = ConversationalRAG(rag_pipeline)

# 第一轮
result1 = conv_rag.run("年假有多少天？")
print(result1.answer)

# 第二轮（依赖上文）
result2 = conv_rag.run("那婚假呢？")
print(result2.answer)
```

### 10.4.3 RAG 评估

```python
class RAGEvaluator:
    """RAG 评估器"""
    
    def __init__(self, llm_client):
        self.llm_client = llm_client
    
    def evaluate_answer_quality(
        self,
        question: str,
        answer: str,
        reference: str
    ) -> dict:
        """
        评估答案质量
        
        Args:
            question: 问题
            answer: 待评估答案
            reference: 参考答案/标准答案
        
        Returns:
            评估结果
        """
        prompt = f"""请评估以下问答系统的表现。

【问题】
{question}

【待评估答案】
{answer}

【参考答案】
{reference}

请从以下维度评估，每个维度1-5分：

1. 准确性：答案是否正确
2. 完整性：答案是否完整
3. 相关性：答案是否与问题相关
4. 可读性：答案是否清晰易懂

只输出以下格式：
准确性: X
完整性: X
相关性: X
可读性: X
总分: X
"""
        
        response = self.llm_client.chat(prompt)
        
        # 解析评分
        scores = {}
        for line in response["message"].split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                scores[key.strip()] = int(value.strip())
        
        return scores
    
    def evaluate_retrieval_quality(
        self,
        question: str,
        retrieved_docs: list,
        relevant_docs: list
    ) -> dict:
        """
        评估检索质量
        
        Returns:
            评估指标：Precision@K, Recall@K, F1@K
        """
        k = len(retrieved_docs)
        
        # 获取检索到的文档
        retrieved_set = set([doc.page_content for doc in retrieved_docs])
        
        # 获取相关文档
        relevant_set = set([doc.page_content for doc in relevant_docs])
        
        # 计算指标
        true_positives = len(retrieved_set & relevant_set)
        
        precision = true_positives / len(retrieved_set) if retrieved_set else 0
        recall = true_positives / len(relevant_set) if relevant_set else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
        
        return {
            "precision@k": precision,
            "recall@k": recall,
            "f1@k": f1,
            "retrieved_count": len(retrieved_set),
            "relevant_count": len(relevant_set),
            "true_positives": true_positives
        }

# 使用示例
evaluator = RAGEvaluator(ai_client)

# 评估答案
scores = evaluator.evaluate_answer_quality(
    question="年假政策是什么？",
    answer="公司员工每年享有带薪年假...",
    reference="根据公司制度..."
)
print(scores)
```

## 10.5 企业知识库实战

### 10.5.1 项目结构

```
knowledge-base-project/
├── data/
│   ├── policies/         # 规章制度
│   ├── products/         # 产品文档
│   └── faqs/            # 常见问题
├── src/
│   ├── __init__.py
│   ├── loader.py         # 文档加载
│   ├── processor.py      # 文档处理
│   ├── vectorstore.py    # 向量存储
│   ├── retriever.py      # 检索器
│   ├── rag.py           # RAG 流水线
│   └── api.py           # API 服务
├── tests/
├── config.py
├── main.py
└── requirements.txt
```

### 10.5.2 批量文档处理

```python
import os
from pathlib import Path
from typing import List

class DocumentProcessor:
    """文档处理器"""
    
    def __init__(self, kb: KnowledgeBase):
        self.kb = kb
    
    def process_directory(
        self,
        directory: str,
        file_extensions: List[str] = ['.pdf', '.docx', '.txt', '.md'],
        metadata: dict = None
    ) -> int:
        """
        处理目录下的所有文档
        
        Args:
            directory: 目录路径
            file_extensions: 要处理的文件扩展名
            metadata: 附加元数据
        
        Returns:
            处理的文档数量
        """
        directory = Path(directory)
        count = 0
        
        for ext in file_extensions:
            for file_path in directory.rglob(f'*{ext}'):
                try:
                    self.process_file(file_path, metadata)
                    count += 1
                    print(f"✓ 已处理: {file_path}")
                except Exception as e:
                    print(f"✗ 处理失败: {file_path} - {e}")
        
        return count
    
    def process_file(
        self,
        file_path: str,
        metadata: dict = None
    ):
        """处理单个文件"""
        # 加载文档
        documents = load_documents(file_path)
        
        # 添加元数据
        for doc in documents:
            if metadata:
                doc.metadata.update(metadata)
            doc.metadata['source'] = str(file_path)
        
        # 添加到知识库
        self.kb.add_documents(documents)
    
    def process_with_categories(self, data_dir: str):
        """按分类处理文档"""
        categories = {
            'policies': {'category': '规章制度', 'department': '人力资源'},
            'products': {'category': '产品文档', 'department': '产品部'},
            'faqs': {'category': '常见问题', 'department': '客服部'},
        }
        
        for folder, metadata in categories.items():
            folder_path = os.path.join(data_dir, folder)
            if os.path.exists(folder_path):
                count = self.process_directory(folder_path, metadata=metadata)
                print(f"处理了 {count} 个 {metadata['category']} 文档")
```

### 10.5.3 API 服务

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI(title="企业知识库问答 API")

# 全局实例
kb = KnowledgeBase()
rag_pipeline = RAGPipeline(kb.vectorstore, ai_client)

# 请求模型
class QuestionRequest(BaseModel):
    question: str
    top_k: int = 5
    include_sources: bool = True

class QuestionResponse(BaseModel):
    answer: str
    sources: Optional[List[dict]]

# API 端点
@app.post("/api/ask", response_model=QuestionResponse)
async def ask_question(request: QuestionRequest):
    """问答接口"""
    try:
        result = rag_pipeline.run(request.question)
        
        sources = None
        if request.include_sources and result.source_documents:
            sources = [
                {
                    "content": doc.page_content[:200] + "...",
                    "source": doc.metadata.get('source', 'Unknown'),
                    "score": 1.0  # 简化，实际可以从检索器获取
                }
                for doc in result.source_documents
            ]
        
        return QuestionResponse(
            answer=result.answer,
            sources=sources
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/rebuild")
async def rebuild_knowledge_base():
    """重建知识库"""
    try:
        global kb, rag_pipeline
        
        # 重新加载文档
        kb = KnowledgeBase()
        processor = DocumentProcessor(kb)
        processor.process_with_categories('data/')
        
        # 重新创建 RAG 流水线
        rag_pipeline = RAGPipeline(kb.vectorstore, ai_client)
        
        return {"status": "success", "message": "知识库已重建"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stats")
async def get_stats():
    """获取知识库统计"""
    return {
        "document_count": len(kb.documents),
        "vectorstore_size": kb.vectorstore.index.ntotal if kb.vectorstore else 0
    }
```

### 10.5.4 前端界面

```html
<!-- templates/rag-chat.html -->
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>企业知识库问答</title>
    <style>
        body { font-family: sans-serif; max-width: 900px; margin: 0 auto; padding: 20px; }
        .qa-container { background: #f9f9f9; border-radius: 8px; padding: 20px; }
        .question { color: #1a73e8; font-weight: bold; margin-bottom: 10px; }
        .answer { background: white; padding: 15px; border-radius: 8px; margin-bottom: 15px; }
        .sources { font-size: 0.9em; color: #666; margin-top: 10px; }
        .source-item { background: #eee; padding: 8px; margin: 5px 0; border-radius: 4px; }
        .loading { color: #999; font-style: italic; }
    </style>
</head>
<body>
    <h1>🔍 企业知识库问答</h1>
    
    <div class="qa-container">
        <div>
            <input type="text" id="question" placeholder="输入您的问题..."
                   style="width: 70%; padding: 10px; font-size: 16px;">
            <button onclick="ask()" style="padding: 10px 20px; font-size: 16px;">提问</button>
        </div>
        
        <div id="result" style="margin-top: 20px;"></div>
    </div>
    
    <script>
        async function ask() {
            const question = document.getElementById('question').value;
            if (!question) return;
            
            const resultDiv = document.getElementById('result');
            resultDiv.innerHTML = `<p class="loading">正在检索知识库并生成答案...</p>`;
            
            try {
                const response = await fetch('/api/ask', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ question, include_sources: true })
                });
                
                const data = await response.json();
                
                let html = `<div class="question">Q: ${question}</div>`;
                html += `<div class="answer"><strong>答案:</strong><br>${data.answer}</div>`;
                
                if (data.sources && data.sources.length > 0) {
                    html += `<div class="sources"><strong>参考文档:</strong>`;
                    data.sources.forEach((src, i) => {
                        html += `<div class="source-item">${i+1}. ${src.content}</div>`;
                    });
                    html += `</div>`;
                }
                
                resultDiv.innerHTML = html;
            } catch (error) {
                resultDiv.innerHTML = `<p style="color: red;">出错了: ${error.message}</p>`;
            }
        }
    </script>
</body>
</html>
```

## 本章小结

本章介绍了企业知识库问答系统的构建：

1. **RAG 架构**：检索增强生成的工作原理
2. **文档处理**：PDF/Word/Markdown 加载与分割
3. **向量化**：使用 DashScope Embedding 模型
4. **语义检索**：基础搜索、MMR、重排序
5. **完整流水线**：检索 + 增强 + 生成的实现
6. **企业实战**：批量处理、API 服务、前端界面

下一章我们将学习智能客服开发，掌握多轮对话和意图识别的技术。

---

## 思考与练习

1. **概念理解**：解释 RAG 架构相比纯 LLM 的优势。

2. **实践练习**：使用 LangChain 构建一个简单的 RAG 系统。

3. **性能优化**：思考如何优化 RAG 系统的检索质量和响应速度。

4. **功能扩展**：为知识库系统添加以下功能：
   - 文档自动更新
   - 知识图谱增强
   - 多语言支持

5. **评估设计**：设计一套 RAG 系统的评估指标。
