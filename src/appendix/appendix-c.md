# 附录 C：术语表

> 本术语表收录了大模型应用开发过程中常用的中英文技术术语，便于读者查阅和理解。

## C.1 大模型基础

| 英文术语 | 中文术语 | 说明 |
|----------|----------|------|
| **Large Language Model (LLM)** | 大语言模型 | 基于大规模语料训练的语言模型 |
| **Foundation Model** | 基座模型 | 大规模预训练模型，可适配多种任务 |
| **Multimodal Model** | 多模态模型 | 能处理文本、图像、音频等多种模态 |
| **Prompt** | 提示词 | 输入给模型的指令或问题 |
| **Prompt Engineering** | 提示工程 | 设计和优化提示词的技术 |
| **Token** | 词元 | 模型处理的最小单位 |
| **Context Window** | 上下文窗口 | 模型一次能处理的最大 token 数 |
| **Temperature** | 温度参数 | 控制模型输出随机性 |
| **Top-p Sampling** | Top-p 采样 | 核采样，一种输出生成策略 |

## C.2 Transformer 架构

| 英文术语 | 中文术语 | 说明 |
|----------|----------|------|
| **Transformer** | Transformer | 一种神经网络架构 |
| **Self-Attention** | 自注意力机制 | Transformer 的核心组件 |
| **Multi-Head Attention** | 多头注意力 | 多个注意力头并行计算 |
| **Feed-Forward Network (FFN)** | 前馈神经网络 | Transformer 中的全连接层 |
| **Positional Encoding** | 位置编码 | 为序列添加位置信息 |
| **Layer Normalization** | 层归一化 | 稳定训练的归一化技术 |
| **Residual Connection** | 残差连接 | 缓解梯度消失的跳跃连接 |
| **KV Cache** | 键值缓存 | 加速推理的缓存机制 |

## C.3 RAG 相关

| 英文术语 | 中文术语 | 说明 |
|----------|----------|------|
| **Retrieval-Augmented Generation (RAG)** | 检索增强生成 | 结合检索和生成的架构 |
| **Vector Database** | 向量数据库 | 存储和检索向量的数据库 |
| **Embedding** | 向量嵌入 | 将文本转为数值向量 |
| **Chunk** | 文本块 | 文档切分后的片段 |
| **Hybrid Search** | 混合检索 | 结合向量和关键词的检索 |
| **Reranking** | 重排序 | 优化检索结果排序 |
| **BM25** | BM25 | 基于关键词的经典检索算法 |
| **HNSW** | HNSW | 一种高效向量索引算法 |
| **MMR (Maximal Marginal Relevance)** | 最大边际相关性 | 兼顾相关性和多样性的检索 |
| **HyDE (Hypothetical Document Embeddings)** | 假设文档嵌入 | 一种检索增强技术 |

## C.4 Agent 相关

| 英文术语 | 中文术语 | 说明 |
|----------|----------|------|
| **Agent** | 智能体 | 能自主决策和执行任务的 AI 系统 |
| **ReAct** | ReAct | 推理+行动的 Agent 框架 |
| **Function Calling** | 函数调用 | 模型调用外部工具的机制 |
| **Tool Use** | 工具使用 | Agent 调用外部工具的能力 |
| **Chain of Thought (CoT)** | 思维链 | 引导模型逐步推理的技术 |
| **Tree of Thought (ToT)** | 思维树 | 探索多种解决路径的框架 |
| **Planning** | 规划 | Agent 分解和计划任务的能力 |
| **Memory** | 记忆 | Agent 存储和回忆信息的能力 |
| **Short-term Memory** | 短期记忆 | 当前对话上下文 |
| **Long-term Memory** | 长期记忆 | 持久化存储的信息 |

## C.5 模型训练与微调

| 英文术语 | 中文术语 | 说明 |
|----------|----------|------|
| **Fine-tuning** | 模型微调 | 在预训练基础上继续训练 |
| **Full Fine-tuning** | 全参数微调 | 更新全部模型参数 |
| **PEFT (Parameter-Efficient Fine-Tuning)** | 高效参数微调 | 只更新部分参数的微调方法 |
| **LoRA (Low-Rank Adaptation)** | LoRA | 一种高效的微调技术 |
| **QLoRA** | QLoRA | 量化的 LoRA，减少显存占用 |
| **Adapter** | 适配器 | 添加的可训练小型模块 |
| **Instruction Tuning** | 指令微调 | 提升指令遵循能力 |
| **RLHF (Reinforcement Learning from Human Feedback)** | 人类反馈强化学习 | 优化模型对齐的技术 |
| **Reward Model** | 奖励模型 | 评估输出质量的模型 |
| **PEFT** | 提示微调 | 仅调整少量提示参数 |

## C.6 阿里云产品术语

| 英文术语 | 中文术语 | 说明 |
|----------|----------|------|
| **DashScope** | 灵积 | 阿里云大模型服务平台 |
| **PAI** | 机器学习平台 | 阿里云机器学习服务 |
| **DSW** | 交互式建模 | PAI 的 Jupyter 环境 |
| **EAS** | 弹性算法服务 | PAI 的模型部署服务 |
| **FC / Function Compute** | 函数计算 | Serverless 计算服务 |
| **ACK** | 容器服务 | 阿里云 Kubernetes 服务 |
| **ASK** | 容器服务 Serverless | 无服务器 Kubernetes |
| **OSS** | 对象存储 | 云存储服务 |
| **RDS** | 云数据库 | 关系型数据库服务 |
| **SLS** | 日志服务 | 日志采集与分析 |
| **ARMS** | 实时监控 | 应用性能监控服务 |

## C.7 DevOps 与云原生

| 英文术语 | 中文术语 | 说明 |
|----------|----------|------|
| **Docker** | 容器 | 应用打包和隔离技术 |
| **Container** | 容器 | 轻量级虚拟化 |
| **Image** | 镜像 | 容器的模板 |
| **Dockerfile** | Docker 配方 | 定义镜像构建步骤 |
| **Kubernetes / K8s** | 容器编排 | 容器自动化管理平台 |
| **Pod** | Pod | Kubernetes 最小调度单位 |
| **Deployment** | 部署 | 应用部署配置 |
| **Service** | 服务 | 网络暴露方式 |
| **Ingress** | 入口 | HTTP/HTTPS 路由 |
| **ConfigMap** | 配置映射 | 非敏感配置存储 |
| **Secret** | 密钥 | 敏感信息存储 |
| **HPA (Horizontal Pod Autoscaler)** | 水平 Pod 自动扩缩容 | 根据负载自动调整副本数 |
| **Helm** | Helm | Kubernetes 包管理器 |
| **CI/CD** | 持续集成/持续部署 | 自动化构建和发布 |
| **Auto Scaling** | 自动扩缩容 | 根据需求自动调整资源 |
| **Serverless** | 无服务器 | 不需管理服务器的模式 |

## C.8 安全与合规

| 英文术语 | 中文术语 | 说明 |
|----------|----------|------|
| **API Key** | API 密钥 | 访问 API 的凭证 |
| **IAM (Identity and Access Management)** | 身份与访问管理 | 权限控制 |
| **RBAC (Role-Based Access Control)** | 基于角色的访问控制 | 角色化权限管理 |
| **VPC (Virtual Private Cloud)** | 虚拟私有云 | 隔离的网络环境 |
| **TLS / SSL** | 传输层安全 | 加密传输协议 |
| **WAF (Web Application Firewall)** | Web 应用防火墙 | 应用层安全防护 |
| **Rate Limiting** | 限流 | 控制请求频率 |
| **Input Validation** | 输入验证 | 校验用户输入 |
| **Prompt Injection** | 提示注入 | 针对 LLM 的攻击 |
| **Content Filtering** | 内容过滤 | 过滤不当内容 |

## C.9 性能与监控

| 英文术语 | 中文术语 | 说明 |
|----------|----------|------|
| **Latency** | 延迟 | 请求响应时间 |
| **Throughput** | 吞吐量 | 单位时间处理量 |
| **TTFT (Time to First Token)** | 首个 Token 时间 | 开始返回的时间 |
| **TPOT (Time Per Output Token)** | 每 Token 时间 | 输出每个 Token 的时间 |
| **RPS (Requests Per Second)** | 每秒请求数 | QPS，查询每秒 |
| **GPU Memory** | 显存 | GPU 内存 |
| **Throughput** | 吞吐量 | 单位时间处理的 token 数 |
| **Prometheus** | Prometheus | 监控系统 |
| **Grafana** | Grafana | 可视化仪表盘 |
| **Logging** | 日志 | 系统运行记录 |
| **Tracing** | 链路追踪 | 请求追踪 |
| **Metrics** | 指标 | 可测量的数据 |

## C.10 其他常见术语

| 英文术语 | 中文术语 | 说明 |
|----------|----------|------|
| **API (Application Programming Interface)** | 应用程序接口 | 交互协议 |
| **SDK (Software Development Kit)** | 软件开发包 | 开发工具集 |
| **REST / RESTful** | REST | 一种 API 设计风格 |
| **JSON** | JSON | 数据格式 |
| **gRPC** | gRPC | 高性能 RPC 框架 |
| **Webhook** | Webhook | 事件回调通知 |
| **CRUD** | 增删改查 | 基本数据操作 |
| **CRON** | 定时任务 | 周期性执行 |
| **Webhook** | 网络钩子 | 事件触发通知 |
| **Middleware** | 中间件 | 请求处理中间层 |
| **Streaming** | 流式输出 | 边生成边返回 |
| **Batch Processing** | 批处理 | 批量处理任务 |
