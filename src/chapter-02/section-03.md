# 2.3 数据存储与管理

## 场景引入

某在线教育平台计划构建智能辅导系统，需要存储和管理以下类型的数据：

- **非结构化数据**：教学视频、课件 PDF、学生作业图片（存储在 OSS）
- **结构化数据**：用户信息、学习记录、课程元数据（存储在 RDS）
- **半结构化数据**：用户行为日志、系统监控指标（存储在 Tablestore）
- **向量数据**：课程内容 Embedding、学生画像向量（存储在向量数据库）

技术团队面临的核心问题是：如何设计统一的数据存储架构？如何选择合适的数据存储服务？如何确保数据的一致性和安全性？

本节将系统地解答这些问题。

---

## 2.3.1 OSS：非结构化数据存储

### 产品概述

对象存储 OSS（Object Storage Service）是阿里云提供的海量、安全、低成本、高可靠的云存储服务。对于大模型应用，OSS 主要用于存储：

- 文档文件（PDF、Word、Excel、PPT）
- 图片（用户上传的图像、生成的图表）
- 音视频（会议录音、教学视频）
- 模型文件（微调后的模型权重、Embedding 缓存）

### 核心优势

| 特性 | 说明 | 对大模型应用的意义 |
|-----|------|------------------|
| **无限扩展** | 存储空间无上限 | 支持海量非结构化数据 |
| **高可靠性** | 数据持久性 99.999999999%（11 个 9） | 确保数据不丢失 |
| **低成本** | 标准存储约 ¥0.12/GB/月，归档存储更低 | 降低存储成本 |
| **高性能** | 单 bucket QPS 可达 10,000+ | 支持高并发读写 |
| **生态集成** | 与函数计算、CDN、数据处理服务无缝对接 | 简化数据处理流程 |

### 快速入门

**步骤一：创建 Bucket**

```python
import oss2

# 初始化 OSS 客户端
auth = oss2.Auth(
    os.getenv('ALIBABA_CLOUD_ACCESS_KEY_ID'),
    os.getenv('ALIBABA_CLOUD_ACCESS_KEY_SECRET')
)
bucket = oss2.Bucket(
    auth,
    'https://oss-cn-beijing.aliyuncs.com',
    'llm-app-data'
)

# 创建 Bucket（如果不存在）
try:
    bucket.create_bucket(oss2.models.BUCKET_ACL_PRIVATE)
    print("Bucket 创建成功")
except oss2.exceptions.BucketAlreadyExists:
    print("Bucket 已存在")
```

**步骤二：上传文件**

```python
def upload_to_oss(bucket, local_file, oss_key):
    """上传文件到 OSS"""
    bucket.put_object_from_file(oss_key, local_file)
    print(f"文件已上传: {oss_key}")
    
    # 获取文件 URL
    url = bucket.sign_url('GET', oss_key, 3600)  # 1 小时有效期
    return url

# 使用示例
local_pdf = "/path/to/document.pdf"
oss_key = "documents/2024/product_manual.pdf"
url = upload_to_oss(bucket, local_pdf, oss_key)
print(f"访问 URL: {url}")
```

**步骤三：批量上传文档**

```python
import os
from pathlib import Path

def batch_upload_documents(bucket, local_dir, oss_prefix):
    """批量上传文档目录"""
    uploaded_count = 0
    
    for file_path in Path(local_dir).rglob('*'):
        if file_path.is_file():
            # 计算 OSS key
            relative_path = file_path.relative_to(local_dir)
            oss_key = f"{oss_prefix}/{relative_path}"
            
            # 上传文件
            bucket.put_object_from_file(oss_key, str(file_path))
            uploaded_count += 1
            
            if uploaded_count % 100 == 0:
                print(f"已上传 {uploaded_count} 个文件...")
    
    print(f"批量上传完成，共 {uploaded_count} 个文件")
    return uploaded_count

# 使用示例
batch_upload_documents(
    bucket,
    local_dir="/data/knowledge_base",
    oss_prefix="knowledge/2024"
)
```

**步骤四：生成预签名 URL**

对于私有 Bucket，可以通过预签名 URL 临时授权访问：

```python
def generate_presigned_url(bucket, oss_key, expires=3600):
    """生成预签名 URL"""
    url = bucket.sign_url('GET', oss_key, expires)
    return url

# 使用示例：生成 1 小时有效的下载链接
url = generate_presigned_url(bucket, "documents/manual.pdf", expires=3600)
print(f"临时访问链接: {url}")
```

### 生命周期管理

为了降低存储成本，可以配置生命周期规则，自动将旧数据转储到低频访问或归档存储：

```python
from oss2.models import BucketLifecycle, LifecycleRule, StorageTransition

# 创建生命周期规则
rule = LifecycleRule(
    id='archive-old-documents',
    prefix='documents/',
    status='Enabled',
    storage_transitions=[
        # 30 天后转低频访问
        StorageTransition(
            days=30,
            storage_class=oss2.BUCKET_STORAGE_CLASS_IA
        ),
        # 180 天后转归档存储
        StorageTransition(
            days=180,
            storage_class=oss2.BUCKET_STORAGE_CLASS_ARCHIVE
        )
    ]
)

# 应用规则
lifecycle = BucketLifecycle([rule])
bucket.put_bucket_lifecycle(lifecycle)
print("生命周期规则已配置")
```

**存储类型对比：**

| 存储类型 | 单价（元/GB/月） | 最小存储时间 | 适用场景 |
|---------|----------------|------------|---------|
| 标准存储 | 0.12 | 无 | 频繁访问的热数据 |
| 低频访问 | 0.08 | 30 天 | 偶尔访问的温数据 |
| 归档存储 | 0.033 | 60 天 | 很少访问的冷数据 |
| 冷归档 | 0.015 | 180 天 | 合规存档、备份 |

**成本优化建议：**

- 对于知识库文档，建议设置 30 天转低频、180 天转归档的生命周期规则
- 对于模型文件和 Embedding 缓存，建议使用标准存储（频繁读取）
- 定期清理过期数据，避免无效存储占用

---

## 2.3.2 RDS/PolarDB：结构化元数据管理

### 产品概述

关系型数据库用于存储大模型应用中的结构化元数据，例如：

- 用户信息和权限
- 文档元数据（标题、作者、分类、标签）
- 对话历史记录
- API 调用日志和计费信息

阿里云提供两种主要的关系型数据库服务：

1. **RDS（Relational Database Service）**：传统的关系型数据库，支持 MySQL、PostgreSQL、SQL Server 等引擎
2. **PolarDB**：云原生数据库，兼容 MySQL/PostgreSQL，具备弹性伸缩、高可用等企业级特性

### 选型对比

| 特性 | RDS MySQL | PolarDB MySQL |
|-----|----------|--------------|
| **性能** | 标准 | 更高（共享存储架构） |
| **弹性** | 手动扩容 | 自动弹性伸缩 |
| **高可用** | 主备切换 | 多副本强一致 |
| **成本** | 较低 | 略高（但性价比更好） |
| **适用规模** | 中小规模 | 中大规模 |

**推荐策略：**

- 初创期或小规模应用：选择 RDS MySQL，成本低
- 成长期或中大规模应用：选择 PolarDB，弹性好、性能强
- 已有 MySQL 技术栈：优先选择兼容版本，降低迁移成本

### 表结构设计

以大模型应用的对话历史为例：

```sql
-- 用户表
CREATE TABLE users (
    user_id VARCHAR(64) PRIMARY KEY,
    username VARCHAR(128) NOT NULL,
    email VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_email (email)
);

-- 会话表
CREATE TABLE conversations (
    conversation_id VARCHAR(64) PRIMARY KEY,
    user_id VARCHAR(64) NOT NULL,
    title VARCHAR(255),
    model_name VARCHAR(64),  -- 使用的模型名称
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    INDEX idx_user_created (user_id, created_at)
);

-- 消息表
CREATE TABLE messages (
    message_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    conversation_id VARCHAR(64) NOT NULL,
    role ENUM('user', 'assistant', 'system') NOT NULL,
    content TEXT NOT NULL,
    token_count INT,  -- Token 数量
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (conversation_id) REFERENCES conversations(conversation_id) ON DELETE CASCADE,
    INDEX idx_conversation (conversation_id, created_at)
);

-- API 调用日志表
CREATE TABLE api_logs (
    log_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(64) NOT NULL,
    model_name VARCHAR(64) NOT NULL,
    input_tokens INT,
    output_tokens INT,
    cost DECIMAL(10, 6),  -- 费用（元）
    latency_ms INT,  -- 延迟（毫秒）
    status_code INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_date (user_id, created_at),
    INDEX idx_date (created_at)
);
```

### 性能优化

**索引优化：**

```sql
-- 为高频查询添加复合索引
-- 查询某用户的最近 10 次会话
ALTER TABLE conversations ADD INDEX idx_user_recent (user_id, created_at DESC);

-- 查询某时间段的 API 调用统计
ALTER TABLE api_logs ADD INDEX idx_date_model (created_at, model_name);
```

**分区表：**

对于大规模数据，可以使用分区表提升查询性能：

```sql
-- 按月份分区的 API 日志表
CREATE TABLE api_logs_partitioned (
    log_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(64) NOT NULL,
    model_name VARCHAR(64) NOT NULL,
    input_tokens INT,
    output_tokens INT,
    cost DECIMAL(10, 6),
    latency_ms INT,
    status_code INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) PARTITION BY RANGE (YEAR(created_at) * 100 + MONTH(created_at)) (
    PARTITION p202401 VALUES LESS THAN (202402),
    PARTITION p202402 VALUES LESS THAN (202403),
    PARTITION p202403 VALUES LESS THAN (202404),
    -- ... 更多分区
    PARTITION p_future VALUES LESS THAN MAXVALUE
);
```

**读写分离：**

对于读多写少的场景，可以启用读写分离：

```python
import pymysql

# 主库（写）
write_conn = pymysql.connect(
    host='rm-xxx.mysql.rds.aliyuncs.com',
    user='admin',
    password='password',
    database='llm_app'
)

# 只读实例（读）
read_conn = pymysql.connect(
    host='rr-xxx.mysql.rds.aliyuncs.com',  # 只读实例地址
    user='admin',
    password='password',
    database='llm_app'
)

def save_message(conversation_id, role, content, token_count):
    """写入消息（主库）"""
    cursor = write_conn.cursor()
    cursor.execute("""
        INSERT INTO messages (conversation_id, role, content, token_count)
        VALUES (%s, %s, %s, %s)
    """, (conversation_id, role, content, token_count))
    write_conn.commit()
    cursor.close()

def get_conversation_history(conversation_id, limit=20):
    """读取对话历史（只读实例）"""
    cursor = read_conn.cursor(pymysql.cursors.DictCursor)
    cursor.execute("""
        SELECT role, content, token_count, created_at
        FROM messages
        WHERE conversation_id = %s
        ORDER BY created_at ASC
        LIMIT %s
    """, (conversation_id, limit))
    results = cursor.fetchall()
    cursor.close()
    return results
```

---

## 2.3.3 表格存储 Tablestore：大规模数据索引

### 产品概述

表格存储 Tablestore 是阿里云提供的分布式 NoSQL 数据库，具有以下特点：

- **海量数据**：支持 PB 级数据存储
- **高并发**：百万级 QPS
- **低延迟**：毫秒级读写
- **灵活 Schema**：无需预先定义列
- **多元索引**：支持全文检索、地理位置、嵌套字段等复杂查询

对于大模型应用，Tablestore 适合存储：

- 用户行为日志（点击、浏览、停留时间）
- 实时监控指标（QPS、延迟、错误率）
- 大规模向量索引的元数据
- 事件溯源数据

### 快速入门

**步骤一：创建实例和数据表**

```python
from tablestore import OTSClient, TableMeta, TableOptions, ReservedThroughput, CapacityUnit

# 初始化客户端
client = OTSClient(
    'https://llm-app.cn-beijing.ots.aliyuncs.com',
    os.getenv('ALIBABA_CLOUD_ACCESS_KEY_ID'),
    os.getenv('ALIBABA_CLOUD_ACCESS_KEY_SECRET'),
    'llm-app'
)

# 创建数据表
table_meta = TableMeta('user_behavior')
table_meta.add_primary_key('user_id', 'STRING')
table_meta.add_primary_key('timestamp', 'INTEGER')

table_options = TableOptions(time_to_live=-1, max_version=1)
reserved_throughput = ReservedThroughput(CapacityUnit(0, 0))  # 按量付费

client.create_table(table_meta, table_options, reserved_throughput)
print("数据表创建成功")
```

**步骤二：写入数据**

```python
from tablestore import Row, Condition, ReturnType

def record_behavior(client, user_id, action, target, metadata=None):
    """记录用户行为"""
    primary_key = [
        ('user_id', user_id),
        ('timestamp', int(time.time() * 1000))  # 毫秒级时间戳
    ]
    
    attribute_columns = [
        ('action', action),  # 行为类型：click, view, search 等
        ('target', target),  # 目标对象 ID
    ]
    
    if metadata:
        attribute_columns.append(('metadata', json.dumps(metadata)))
    
    row = Row(primary_key, attribute_columns)
    condition = Condition(RowExistenceExpectation.IGNORE)
    
    client.put_row('user_behavior', row, condition, ReturnType.NONE)

# 使用示例
record_behavior(
    client,
    user_id='user_12345',
    action='search',
    target='knowledge_base',
    metadata={'query': '如何重置密码', 'result_count': 5}
)
```

**步骤三：范围查询**

```python
from tablestore import Direction, RangeRowQueryCriteria

def query_user_behaviors(client, user_id, start_time, end_time, limit=100):
    """查询用户行为记录"""
    # 构造主键范围
    inclusive_start = [('user_id', user_id), ('timestamp', start_time)]
    exclusive_end = [('user_id', user_id), ('timestamp', end_time)]
    
    # 构造查询条件
    criteria = RangeRowQueryCriteria('user_behavior')
    criteria.inclusive_start_primary_key = inclusive_start
    criteria.exclusive_end_primary_key = exclusive_end
    criteria.limit = limit
    criteria.direction = Direction.FORWARD  # 正序
    
    # 执行查询
    rows = []
    next_start = inclusive_start
    
    while next_start is not None:
        criteria.inclusive_start_primary_key = next_start
        result = client.get_range(criteria)
        rows.extend(result.rows)
        next_start = result.next_start_primary_key
        
        if len(rows) >= limit:
            break
    
    return rows[:limit]

# 使用示例：查询过去 24 小时的行为
start_time = int((time.time() - 86400) * 1000)
end_time = int(time.time() * 1000)
behaviors = query_user_behaviors(client, 'user_12345', start_time, end_time)

for row in behaviors:
    attrs = {col[0]: col[1] for col in row.attribute_columns}
    print(f"[{row.primary_key[1][1]}] {attrs['action']} -> {attrs['target']}")
```

### 多元索引

对于复杂查询需求（如全文检索、多条件过滤），可以创建多元索引：

```python
from tablestore import SearchIndexSchema, FieldSchema, FieldType, IndexSetting

# 创建多元索引
schema = SearchIndexSchema([
    FieldSchema('user_id', FieldType.KEYWORD, index=True, enable_sort_and_agg=True),
    FieldSchema('action', FieldType.KEYWORD, index=True, enable_sort_and_agg=True),
    FieldSchema('target', FieldType.TEXT, index=True, analyzer='max_word'),
    FieldSchema('metadata.query', FieldType.TEXT, index=True, analyzer='max_word'),
    FieldSchema('timestamp', FieldType.LONG, index=True, enable_sort_and_agg=True)
])

index_setting = IndexSetting(routing_fields=['user_id'])
client.create_search_index('user_behavior', 'behavior_index', schema, index_setting)
print("多元索引创建成功")
```

**使用多元索引进行复杂查询：**

```python
from tablestore import SearchQuery, TermQuery, RangeQuery, BoolQuery, Sort, FieldSort

def advanced_search(client, user_id=None, action=None, keyword=None, start_time=None, end_time=None, limit=100):
    """高级搜索：支持多条件组合"""
    queries = []
    
    # 用户 ID 过滤
    if user_id:
        queries.append(TermQuery('user_id', user_id))
    
    # 行为类型过滤
    if action:
        queries.append(TermQuery('action', action))
    
    # 关键词搜索
    if keyword:
        queries.append(TermQuery('metadata.query', keyword))
    
    # 时间范围过滤
    if start_time or end_time:
        range_query = RangeQuery('timestamp')
        if start_time:
            range_query.greater_than = start_time
        if end_time:
            range_query.less_than = end_time
        queries.append(range_query)
    
    # 组合查询
    if len(queries) == 1:
        query = queries[0]
    else:
        query = BoolQuery(must_queries=queries)
    
    # 排序
    sort = Sort(sorters=[FieldSort('timestamp', SortOrder.SORT_ORDER_DESC)])
    
    # 执行搜索
    search_query = SearchQuery(query, offset=0, limit=limit, sort=sort, get_total_count=True)
    response = client.search('user_behavior', 'behavior_index', search_query)
    
    return response.rows, response.total_count

# 使用示例：查询某用户过去的搜索行为
rows, total = advanced_search(
    client,
    user_id='user_12345',
    action='search',
    start_time=int((time.time() - 86400) * 1000),
    limit=50
)
print(f"找到 {total} 条记录")
```

---

## 2.3.4 数据一致性保障

### 最终一致性 vs 强一致性

在分布式系统中，数据一致性是一个重要考量：

| 一致性模型 | 说明 | 适用场景 |
|-----------|------|---------|
| **强一致性** | 写入后立即读取一定能读到最新数据 | 金融交易、库存扣减 |
| **最终一致性** | 写入后可能在短时间内读到旧数据，但最终会一致 | 用户行为日志、监控指标 |

**阿里云产品的一致性保证：**

- **RDS/PolarDB**：强一致性（基于事务）
- **OSS**：最终一致性（新上传文件可能短暂不可见）
- **Tablestore**：单行强一致性，跨行最终一致性
- **OpenSearch**：最终一致性（索引更新有延迟）

### 最佳实践

**1. 幂等性设计**

对于可能重试的操作，确保幂等性：

```python
def save_message_idempotent(conversation_id, message_id, role, content):
    """幂等保存消息"""
    try:
        cursor = write_conn.cursor()
        cursor.execute("""
            INSERT INTO messages (message_id, conversation_id, role, content)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE content = VALUES(content)
        """, (message_id, conversation_id, role, content))
        write_conn.commit()
        cursor.close()
    except Exception as e:
        logging.error(f"保存消息失败: {e}")
        raise
```

**2. 补偿机制**

对于最终一致性的场景，实现补偿机制：

```python
def sync_oss_to_vector_db(oss_key, retry_count=3):
    """将 OSS 文档同步到向量数据库（带重试）"""
    for attempt in range(retry_count):
        try:
            # 从 OSS 下载文档
            document = bucket.get_object(oss_key).read()
            
            # 解析并生成向量
            chunks = split_document(document)
            embeddings = [generate_embedding(chunk) for chunk in chunks]
            
            # 写入向量数据库
            vector_db.batch_insert(chunks, embeddings)
            
            print(f"同步成功: {oss_key}")
            return True
            
        except Exception as e:
            logging.warning(f"同步失败 (尝试 {attempt + 1}/{retry_count}): {e}")
            if attempt < retry_count - 1:
                time.sleep(2 ** attempt)  # 指数退避
            else:
                logging.error(f"同步最终失败: {oss_key}")
                return False
```

**3. 数据校验**

定期校验数据一致性：

```python
def validate_data_consistency():
    """校验 OSS 和向量数据库的数据一致性"""
    # 获取 OSS 中的文档列表
    oss_docs = list_oss_documents(prefix='knowledge/')
    
    # 获取向量数据库中的文档 ID 列表
    vector_doc_ids = vector_db.list_all_doc_ids()
    
    # 找出不一致的文档
    missing_in_vector = set(oss_docs.keys()) - set(vector_doc_ids)
    extra_in_vector = set(vector_doc_ids) - set(oss_docs.keys())
    
    if missing_in_vector:
        logging.warning(f"向量数据库中缺失 {len(missing_in_vector)} 个文档")
        for doc_id in list(missing_in_vector)[:10]:  # 只打印前 10 个
            logging.warning(f"  - {doc_id}")
    
    if extra_in_vector:
        logging.warning(f"向量数据库中多出 {len(extra_in_vector)} 个文档")
        for doc_id in list(extra_in_vector)[:10]:
            logging.warning(f"  - {doc_id}")
    
    return len(missing_in_vector) == 0 and len(extra_in_vector) == 0
```

---

## 本节小结

本节系统介绍了大模型应用中的数据存储与管理策略：

1. **OSS 非结构化存储**：适合存储文档、图片、音视频等大文件，通过生命周期管理降低成本

2. **RDS/PolarDB 结构化存储**：适合存储用户信息、对话历史、API 日志等结构化数据，通过索引优化和读写分离提升性能

3. **Tablestore 大规模索引**：适合存储用户行为日志、监控指标等海量数据，通过多元索引支持复杂查询

4. **数据一致性保障**：根据业务场景选择合适的一致性模型，通过幂等性设计、补偿机制和数据校验确保数据可靠性

技术决策者在设计数据存储架构时，应遵循"合适的数据存到合适的地方"的原则，避免用单一数据库解决所有问题。混合使用多种存储服务，可以在性能、成本和复杂度之间取得最佳平衡。

---

## 延伸阅读

1. **官方文档**
   - [OSS 产品文档](https://help.aliyun.com/zh/oss/)
   - [RDS 产品文档](https://help.aliyun.com/zh/rds/)
   - [PolarDB 产品文档](https://help.aliyun.com/zh/polardb/)
   - [Tablestore 产品文档](https://help.aliyun.com/zh/tablestore/)

2. **最佳实践**
   - [OSS 生命周期管理最佳实践](https://help.aliyun.com/zh/oss/user-guide/lifecycle-rules)
   - [PolarDB 性能优化指南](https://help.aliyun.com/zh/polardb/user-guide/performance-optimization)

3. **架构案例**
   - 某电商平台海量商品图片存储方案
   - 某社交平台用户行为数据分析架构
   - 某 IoT 平台实时监控数据存储设计
