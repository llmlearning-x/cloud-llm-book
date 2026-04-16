# 2.2 向量数据库与检索基础设施

## 场景引入

某大型制造企业计划构建企业知识库问答系统，需要处理超过 10 万份技术文档、产品手册和维修记录。技术团队面临的核心挑战是：如何快速存储和检索这些非结构化数据？如何选择向量数据库？自建还是使用托管服务？

这个问题的背后，涉及向量数据库选型、检索性能优化、成本控制等多个维度。本节将系统地解答这些问题。

---

## 2.2.1 为什么需要向量数据库

### 传统数据库的局限性

在传统的关系型数据库中，数据以结构化表格的形式存储，查询基于精确匹配或关键词搜索。然而，大模型应用中的检索需求具有以下特点：

1. **语义相似性**：用户查询"如何重置密码"，系统应能返回包含"忘记密码怎么办""账户密码找回"等语义相关但措辞不同的文档
2. **高维向量表示**：文本经过 Embedding 模型处理后，转化为数百甚至数千维的向量，传统数据库无法高效处理
3. **近似最近邻搜索**：需要在海量向量中找到与查询向量最相似的 Top-K 结果，而非精确匹配

### 向量数据库的核心能力

向量数据库专为高维向量数据的存储和检索而设计，提供以下核心能力：

| 能力 | 说明 | 对大模型应用的意义 |
|-----|------|------------------|
| **向量索引** | HNSW、IVF、PQ 等高效索引算法 | 支持亿级向量的毫秒级检索 |
| **相似度计算** | 余弦相似度、欧氏距离、点积等 | 准确衡量语义相关性 |
| **混合检索** | 向量 + 关键词 + 元数据过滤 | 提升检索精度和灵活性 |
| **动态更新** | 支持实时插入、删除、更新 | 适应知识库的动态变化 |
| **分布式扩展** | 水平扩展支持海量数据 | 满足企业级规模需求 |

---

## 2.2.2 阿里云 OpenSearch 向量检索版

### 产品概述

阿里云 OpenSearch 向量检索版是阿里云推出的托管式向量搜索引擎，深度集成 DashScope Embedding API，提供一站式的向量存储、索引和检索服务。

**核心优势：**

- **免运维**：无需管理底层基础设施，自动扩缩容
- **高性能**：基于阿里巴巴自研的向量索引引擎，支持亿级数据毫秒级检索
- **多模态支持**：支持文本、图像、音频等多种数据类型
- **混合检索**：内置 BM25 关键词检索 + 向量检索，支持加权融合
- **生态集成**：与百炼平台、PAI、函数计算等阿里云产品无缝对接

### 架构设计

```
┌──────────────────────────────────────────────┐
│              应用层                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │ RAG 系统  │  │ 智能搜索  │  │ 推荐引擎  │  │
│  └──────────┘  └──────────┘  └──────────┘  │
├──────────────────────────────────────────────┤
│            OpenSearch 向量检索版              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │ 向量索引  │  │ 关键词索引│  │ 元数据过滤│  │
│  └──────────┘  └──────────┘  └──────────┘  │
├──────────────────────────────────────────────┤
│              基础设施层                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │ 分布式存储│  │ 负载均衡  │  │ 自动扩缩容│  │
│  └──────────┘  └──────────┘  └──────────┘  │
└──────────────────────────────────────────────┘
```

### 快速入门

**步骤一：创建实例**

```python
from alibabacloud_opensearch20171225.client import Client
from alibabacloud_opensearch20171225.models import CreateInstanceRequest

client = Client(
    access_key_id=os.getenv('ALIBABA_CLOUD_ACCESS_KEY_ID'),
    access_key_secret=os.getenv('ALIBABA_CLOUD_ACCESS_KEY_SECRET')
)

request = CreateInstanceRequest(
    instance_name='enterprise-knowledge-base',
    instance_type='vector_search',
    spec='standard',  # standard / professional / enterprise
    zone_count=2,  # 可用区数量
    description='企业知识库向量检索实例'
)

response = client.create_instance(request)
print(f"实例 ID: {response.body.instance_id}")
```

**步骤二：定义表结构**

```python
# 定义向量表结构
table_schema = {
    "fields": [
        {"name": "id", "type": "string", "is_primary": True},
        {"name": "content", "type": "text"},  # 原始文本内容
        {"name": "embedding", "type": "float_vector", "dimension": 1536},  # 向量字段
        {"name": "doc_type", "type": "string"},  # 文档类型（手册/FAQ/案例）
        {"name": "create_time", "type": "int64"},  # 创建时间戳
        {"name": "tags", "type": "string_array"}  # 标签数组
    ],
    "index_settings": {
        "vector_index": {
            "algorithm": "HNSW",  # 索引算法
            "metric_type": "Cosine",  # 相似度度量
            "ef_construction": 200,  # 构建参数
            "M": 16  # 每个节点的连接数
        }
    }
}
```

**步骤三：批量导入数据**

```python
import dashscope
from dashscope import TextEmbedding

def generate_embedding(text):
    """使用 DashScope Embedding API 生成向量"""
    response = TextEmbedding.call(
        model='text-embedding-v3',
        input=text
    )
    return response.output['embeddings'][0]['embedding']

# 准备数据
documents = [
    {"id": "doc_001", "content": "如何重置管理员密码？...", "doc_type": "FAQ"},
    {"id": "doc_002", "content": "设备故障代码 E001 表示...", "doc_type": "手册"},
    # ... 更多文档
]

# 生成向量并导入
for doc in documents:
    embedding = generate_embedding(doc['content'])
    doc['embedding'] = embedding
    doc['create_time'] = int(time.time())
    doc['tags'] = extract_tags(doc['content'])  # 提取标签

# 批量写入 OpenSearch
bulk_import_to_opensearch(instance_id, table_name, documents)
```

**步骤四：执行检索**

```python
def search_knowledge_base(query, top_k=5):
    """在知识库中检索相关文档"""
    # 生成查询向量
    query_embedding = generate_embedding(query)
    
    # 构建检索请求
    search_request = {
        "query": {
            "vector": {
                "field": "embedding",
                "value": query_embedding,
                "top_k": top_k,
                "metric": "cosine"
            }
        },
        "filter": {
            "range": {
                "create_time": {"gte": 1704067200}  # 只搜索 2024 年后的文档
            }
        },
        "output_fields": ["id", "content", "doc_type", "tags"]
    }
    
    # 执行检索
    response = opensearch_client.search(instance_id, table_name, search_request)
    
    # 解析结果
    results = []
    for hit in response['result']['items']:
        results.append({
            'id': hit['fields']['id'],
            'content': hit['fields']['content'],
            'score': hit['score'],
            'doc_type': hit['fields']['doc_type']
        })
    
    return results

# 使用示例
results = search_knowledge_base("管理员密码忘记了怎么办？")
for r in results:
    print(f"[{r['score']:.3f}] {r['content'][:100]}...")
```

### 性能调优

**索引参数优化：**

| 参数 | 含义 | 推荐值 | 影响 |
|-----|------|-------|------|
| `ef_construction` | 索引构建时的搜索宽度 | 100-400 | 值越大索引质量越高，但构建越慢 |
| `M` | 每个节点的最大连接数 | 8-32 | 值越大检索越快，但内存占用越高 |
| `ef_search` | 检索时的搜索宽度 | 50-200 | 值越大召回率越高，但延迟增加 |

**实战建议：**

- 对于千万级以下数据量，`ef_construction=200, M=16` 是较好的平衡点
- 对于亿级数据量，建议使用 `ef_construction=400, M=32`，并启用 PQ（乘积量化）压缩
- 检索时 `ef_search` 可根据业务需求动态调整：对精度要求高的场景设为 100-200，对延迟敏感的场景设为 50-80

---

## 2.2.3 AnalyticDB PostgreSQL 向量插件

### 产品概述

AnalyticDB PostgreSQL 是阿里云提供的云原生数据仓库服务，基于 PostgreSQL 内核开发，支持标准的 SQL 查询。通过安装 `vectorscale` 或 `pgvector` 插件，AnalyticDB PostgreSQL 可以作为向量数据库使用。

**适用场景：**

- 已有 PostgreSQL 技术栈的团队，学习成本低
- 需要复杂 SQL 查询和事务支持的场景
- 向量检索与传统关系查询混合的场景（如"查找某客户的所有相关文档并按相似度排序"）

### 快速入门

**步骤一：启用向量插件**

```sql
-- 连接到 AnalyticDB PostgreSQL 实例
CREATE EXTENSION IF NOT EXISTS vector;

-- 验证插件是否安装成功
SELECT * FROM pg_extension WHERE extname = 'vector';
```

**步骤二：创建向量表**

```sql
-- 创建文档表
CREATE TABLE knowledge_documents (
    id VARCHAR(64) PRIMARY KEY,
    content TEXT NOT NULL,
    embedding VECTOR(1536),  -- 1536 维向量（对应 text-embedding-v3）
    doc_type VARCHAR(32),
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    tags TEXT[]
);

-- 创建向量索引（HNSW）
CREATE INDEX idx_embedding ON knowledge_documents 
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 200);
```

**步骤三：插入数据**

```python
import psycopg2
import dashscope
from dashscope import TextEmbedding

def insert_document(conn, doc_id, content, doc_type, tags):
    """插入文档及其向量表示"""
    # 生成向量
    response = TextEmbedding.call(
        model='text-embedding-v3',
        input=content
    )
    embedding = response.output['embeddings'][0]['embedding']
    
    # 插入数据库
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO knowledge_documents (id, content, embedding, doc_type, tags)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (id) DO UPDATE SET 
            content = EXCLUDED.content,
            embedding = EXCLUDED.embedding,
            doc_type = EXCLUDED.doc_type,
            tags = EXCLUDED.tags
    """, (doc_id, content, str(embedding), doc_type, tags))
    conn.commit()
    cursor.close()

# 使用示例
conn = psycopg2.connect(
    host="your-adb-instance.pg.rds.aliyuncs.com",
    database="knowledge_base",
    user="admin",
    password="your_password"
)

insert_document(
    conn,
    doc_id="doc_001",
    content="如何重置管理员密码？...",
    doc_type="FAQ",
    tags=["密码", "管理员", "重置"]
)
```

**步骤四：执行向量检索**

```sql
-- 基本向量检索
SELECT id, content, doc_type, 
       1 - (embedding <=> '[0.1, 0.2, ...]') AS similarity
FROM knowledge_documents
ORDER BY embedding <=> '[0.1, 0.2, ...]'
LIMIT 5;

-- 带元数据过滤的向量检索
SELECT id, content, doc_type, 
       1 - (embedding <=> '[0.1, 0.2, ...]') AS similarity
FROM knowledge_documents
WHERE doc_type = 'FAQ'
  AND create_time >= '2024-01-01'
ORDER BY embedding <=> '[0.1, 0.2, ...]'
LIMIT 5;

-- 混合检索：向量 + 关键词
SELECT id, content, 
       0.7 * (1 - (embedding <=> '[0.1, 0.2, ...]')) + 
       0.3 * ts_rank(to_tsvector('chinese', content), plainto_tsquery('chinese', '密码重置')) AS combined_score
FROM knowledge_documents
ORDER BY combined_score DESC
LIMIT 5;
```

### 性能对比

| 特性 | OpenSearch 向量检索版 | AnalyticDB PostgreSQL |
|-----|---------------------|----------------------|
| 检索性能 | 更高（专用向量引擎） | 中等（通用数据库） |
| SQL 支持 | 有限 | 完整 PostgreSQL SQL |
| 事务支持 | 不支持 | 支持 ACID 事务 |
| 学习成本 | 需学习新 API | 低（熟悉 SQL 即可） |
| 适用规模 | 亿级 | 千万级 |
| 成本 | 中等 | 较低（复用现有实例） |

**选型建议：**

- 如果团队已有 PostgreSQL 技术栈，且数据量在千万级以内，优先选择 AnalyticDB PostgreSQL
- 如果需要处理亿级向量数据，或对检索性能有极致要求，选择 OpenSearch 向量检索版
- 也可以采用混合架构：用 AnalyticDB PostgreSQL 存储元数据和中小规模向量，用 OpenSearch 处理大规模向量检索

---

## 2.2.4 自建向量库 vs 托管服务

### 方案对比

| 维度 | 自建（Milvus/Faiss） | 托管服务（OpenSearch/ADB） |
|-----|---------------------|--------------------------|
| **初始成本** | 低（开源软件免费） | 中（按实例规格计费） |
| **运维成本** | 高（需专职 DBA） | 低（阿里云负责运维） |
| **可扩展性** | 需手动扩容 | 自动扩缩容 |
| **高可用** | 需自行搭建集群 | 内置多副本冗余 |
| **安全性** | 需自行配置 | 内置 VPC、RAM、加密 |
| **技术支持** | 社区支持 | 阿里云工单 + 专属客服 |
| **总拥有成本（3 年）** | 高（人力成本高） | 中（按需付费） |

### 自建方案示例：Milvus

如果企业决定自建向量数据库，Milvus 是最流行的开源选择之一。

**部署架构：**

```yaml
# docker-compose.yml（简化版）
version: '3.5'
services:
  etcd:
    image: quay.io/coreos/etcd:v3.5.5
    environment:
      - ETCD_AUTO_COMPACTION_MODE=revision
      - ETCD_AUTO_COMPACTION_RETENTION=1000
    volumes:
      - ${DOCKER_VOLUME_DIRECTORY:-.}/volumes/etcd:/etcd

  minio:
    image: minio/minio:RELEASE.2023-03-20T20-16-18Z
    environment:
      MINIO_ACCESS_KEY: minioadmin
      MINIO_SECRET_KEY: minioadmin
    volumes:
      - ${DOCKER_VOLUME_DIRECTORY:-.}/volumes/minio:/minio_data
    command: minio server /minio_data

  milvus-standalone:
    image: milvusdb/milvus:v2.3.0
    command: ["milvus", "run", "standalone"]
    environment:
      ETCD_ENDPOINTS: etcd:2379
      MINIO_ADDRESS: minio:9000
    volumes:
      - ${DOCKER_VOLUME_DIRECTORY:-.}/volumes/milvus:/var/lib/milvus
    ports:
      - "19530:19530"
    depends_on:
      - "etcd"
      - "minio"
```

**Python 客户端使用：**

```python
from pymilvus import connections, Collection, FieldSchema, CollectionSchema, DataType

# 连接 Milvus
connections.connect(host='localhost', port='19530')

# 定义集合 Schema
fields = [
    FieldSchema(name="id", dtype=DataType.INT64, is_primary=True),
    FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=1536),
    FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=65535),
    FieldSchema(name="doc_type", dtype=DataType.VARCHAR, max_length=64)
]
schema = CollectionSchema(fields, "Knowledge Base Collection")

# 创建集合
collection = Collection("knowledge_base", schema)

# 创建索引
index_params = {
    "metric_type": "COSINE",
    "index_type": "HNSW",
    "params": {"M": 16, "efConstruction": 200}
}
collection.create_index(field_name="embedding", index_params=index_params)

# 插入数据
entities = [
    [1, 2, 3],  # IDs
    [[0.1]*1536, [0.2]*1536, [0.3]*1536],  # Embeddings
    ["文档 1", "文档 2", "文档 3"],  # Contents
    ["FAQ", "手册", "案例"]  # Doc types
]
collection.insert(entities)

# 加载集合
collection.load()

# 执行检索
search_params = {"metric_type": "COSINE", "params": {"ef": 100}}
results = collection.search(
    data=[[0.15]*1536],  # 查询向量
    anns_field="embedding",
    param=search_params,
    limit=5,
    output_fields=["content", "doc_type"]
)

for hits in results:
    for hit in hits:
        print(f"ID: {hit.id}, Score: {hit.score}, Content: {hit.entity.get('content')[:50]}")
```

### 决策框架

技术决策者在选择向量数据库时，可以参考以下决策流程：

```
是否需要处理亿级向量数据？
├─ 是 → 选择 OpenSearch 向量检索版或 Milvus 集群
│         ├─ 希望免运维 → OpenSearch
│         └─ 有专职 DBA 团队 → Milvus
└─ 否 → 数据量是否在千万级以内？
          ├─ 是 → 是否有 PostgreSQL 技术栈？
          │         ├─ 是 → AnalyticDB PostgreSQL
          │         └─ 否 → OpenSearch 或 Milvus 单机版
          └─ 否 → 参考上一条分支
```

**关键考量因素：**

1. **团队技能**：如果团队熟悉 PostgreSQL，AnalyticDB 的学习成本最低
2. **运维能力**：如果没有专职 DBA，托管服务更合适
3. **数据规模**：千万级以下可选 ADB，亿级以上建议 OpenSearch 或 Milvus 集群
4. **预算约束**：自建初期成本低，但长期运维成本高；托管服务反之
5. **合规要求**：金融、医疗等行业可能需要私有化部署，此时自建更合适

---

## 2.2.5 检索优化策略

### 混合检索

单一向量检索在某些场景下可能不够准确，例如：

- 用户查询包含专有名词（产品型号、人名），向量相似度可能无法精确匹配
- 用户希望结合时间、类别等元数据进行过滤

**混合检索方案：**

```python
def hybrid_search(query, filters=None, top_k=5):
    """混合检索：向量 + 关键词 + 元数据过滤"""
    # 1. 生成查询向量
    query_embedding = generate_embedding(query)
    
    # 2. 向量检索
    vector_results = vector_db.search(
        embedding=query_embedding,
        top_k=top_k * 2,  # 先召回更多候选
        filters=filters
    )
    
    # 3. 关键词检索（BM25）
    keyword_results = keyword_db.search(
        query=query,
        top_k=top_k * 2,
        filters=filters
    )
    
    # 4. 结果融合（RRF - Reciprocal Rank Fusion）
    merged_results = rrf_fusion(vector_results, keyword_results, top_k)
    
    return merged_results

def rrf_fusion(vector_results, keyword_results, top_k, k=60):
    """RRF 融合算法"""
    scores = {}
    
    # 向量检索得分
    for rank, result in enumerate(vector_results, 1):
        doc_id = result['id']
        scores[doc_id] = scores.get(doc_id, 0) + 1 / (k + rank)
    
    # 关键词检索得分
    for rank, result in enumerate(keyword_results, 1):
        doc_id = result['id']
        scores[doc_id] = scores.get(doc_id, 0) + 1 / (k + rank)
    
    # 排序并返回 Top-K
    sorted_results = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
    return [{'id': doc_id, 'score': score} for doc_id, score in sorted_results]
```

### 重排序（Re-ranking）

向量检索召回的候选集可能包含一些语义相关但实际不匹配的结果。通过重排序模型（Cross-Encoder）可以进一步提升精度。

```python
from transformers import AutoModelForSequenceClassification, AutoTokenizer

# 加载重排序模型
reranker_model = AutoModelForSequenceClassification.from_pretrained(
    'BAAI/bge-reranker-v2-m3'
)
reranker_tokenizer = AutoTokenizer.from_pretrained('BAAI/bge-reranker-v2-m3')

def rerank(query, candidates, top_k=5):
    """对候选结果进行重排序"""
    pairs = [(query, cand['content']) for cand in candidates]
    
    # 计算相关性得分
    inputs = reranker_tokenizer(
        pairs,
        padding=True,
        truncation=True,
        return_tensors='pt',
        max_length=512
    )
    
    with torch.no_grad():
        outputs = reranker_model(**inputs)
        scores = outputs.logits.squeeze().tolist()
    
    # 如果只有一个样本，scores 是标量
    if isinstance(scores, float):
        scores = [scores]
    
    # 附加得分并排序
    for cand, score in zip(candidates, scores):
        cand['rerank_score'] = score
    
    sorted_candidates = sorted(candidates, key=lambda x: x['rerank_score'], reverse=True)
    return sorted_candidates[:top_k]

# 使用示例
candidates = hybrid_search("如何重置密码？", top_k=20)
final_results = rerank("如何重置密码？", candidates, top_k=5)
```

**性能与精度权衡：**

| 策略 | 延迟增加 | 精度提升 | 适用场景 |
|-----|---------|---------|---------|
| 纯向量检索 | 基准 | 基准 | 对延迟敏感的场景 |
| 向量 + 关键词 | +10-20ms | +5-10% | 通用场景 |
| 向量 + 关键词 + 重排序 | +50-100ms | +10-20% | 对精度要求高的场景 |

**最佳实践：**

- 第一阶段（召回）：使用向量检索快速召回 Top-50 候选
- 第二阶段（精排）：使用重排序模型对 Top-50 进行精排，返回 Top-5
- 这种两阶段策略在精度和延迟之间取得良好平衡

---

## 本节小结

本节系统介绍了向量数据库与检索基础设施的核心内容：

1. **向量数据库的价值**：解决传统数据库在语义检索上的局限性，支持高维向量的高效存储和检索

2. **阿里云产品选型**：
   - OpenSearch 向量检索版：适合大规模、高性能场景，免运维
   - AnalyticDB PostgreSQL：适合已有 PostgreSQL 技术栈的团队，支持复杂 SQL

3. **自建 vs 托管**：根据团队技能、数据规模、预算等因素做出合理选择

4. **检索优化策略**：
   - 混合检索：结合向量和关键词的优势
   - 重排序：进一步提升检索精度
   - 两阶段策略：在精度和延迟之间取得平衡

技术决策者在选择向量数据库时，应避免"一刀切"的思维，而是根据具体的业务场景、技术栈和团队能力做出最适合的选择。

---

## 延伸阅读

1. **官方文档**
   - [OpenSearch 向量检索版产品文档](https://help.aliyun.com/zh/opensearch/)
   - [AnalyticDB PostgreSQL 向量检索教程](https://help.aliyun.com/zh/analyticdb/analyticdb-for-postgresql/)

2. **开源项目**
   - [Milvus 官方文档](https://milvus.io/docs)
   - [pgvector GitHub](https://github.com/pgvector/pgvector)

3. **学术论文**
   - Efficient and Robust Approximate Nearest Neighbor Search Using Hierarchical Navigable Small World Graphs (FAISS/HNSW 论文)
   - Relevance-guided Supervision for OpenQA with Transformer (重排序模型研究)

4. **实践案例**
   - 某电商平台商品搜索向量检索优化实践
   - 某金融机构智能投顾知识库架构设计
