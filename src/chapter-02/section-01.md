# 2.1 阿里云 GPU/NPU 计算资源

## 场景引入

某金融科技公司计划在阿里云上部署一个经过微调的风控大模型，用于实时交易风险评估。模型参数量约 7B（70 亿），需要在 50ms 内完成推理。技术团队面临的核心问题是：选择什么样的 GPU 实例？按量付费还是预留？如何确保推理服务的高可用？

这个问题背后，是每一个大模型应用开发者都会遇到的"基础设施选型"挑战。本章将系统地解答这些问题。

---

## 2.1.1 GPU 实例选型指南

### 理解 GPU 的关键参数

在选择 GPU 实例之前，技术决策者需要理解以下核心指标：

| 参数 | 含义 | 对大模型的意义 |
|-----|------|-------------|
| **显存 (VRAM)** | GPU 板载内存 | 决定能加载的模型大小，7B FP16 模型约需 14GB |
| **算力 (TFLOPS)** | 每秒浮点运算次数 | 影响推理速度，TF32 精度下 A100 约 312 TFLOPS |
| **显存带宽** | 数据传输速率 | 影响 Prefill 阶段的速度，A100 约 2TB/s |
| **互联带宽** | 多卡间通信速率 | 多卡并行训练/推理的关键，NVLink 可达 600GB/s |
| **功耗 (TDP)** | 最大功率消耗 | 影响散热和电力成本 |

### 阿里云 ECS GPU 实例族

阿里云提供多种 GPU 实例族，覆盖不同的大模型应用场景：

**1. GN 系列（NVIDIA A100/H800）—— 旗舰级**

| 实例规格 | GPU 型号 | GPU 数量 | 显存 | 适用场景 |
|---------|---------|---------|------|---------|
| ecs.gn7-c12g1.3xlarge | A100 40GB | 1 | 40GB | 小模型推理（≤7B） |
| ecs.gn7-c12g1.6xlarge | A100 40GB | 2 | 80GB | 中等模型推理/微调（7B-14B） |
| ecs.gn7-c12g1.12xlarge | A100 40GB | 4 | 160GB | 大模型训练/推理（14B-72B） |
| ecs.gn7e-c12g1.24xlarge | A100 80GB | 8 | 640GB | 超大模型训练（70B+） |

**2. GM 系列（NVIDIA H800/H20）—— 新一代**

H800 是 A100 的升级版，采用 Hopper 架构，在推理场景下性能提升 2-4 倍：

| 实例规格 | GPU 型号 | GPU 数量 | 显存 | 适用场景 |
|---------|---------|---------|------|---------|
| ecs.gm7-c12g1.3xlarge | H800 80GB | 1 | 80GB | 高性能推理 |
| ecs.gm7-c12g1.6xlarge | H800 80GB | 2 | 160GB | 模型微调 |
| ecs.gm7-c12g1.12xlarge | H800 80GB | 4 | 320GB | 大规模训练 |

**3. VGN 系列（NVIDIA L40s）—— 性价比之选**

L40s 是 Ada Lovelace 架构的推理优化卡，性价比极高：

| 实例规格 | GPU 型号 | GPU 数量 | 显存 | 适用场景 |
|---------|---------|---------|------|---------|
| ecs.vgn7i-vni4 | L40s 48GB | 1 | 48GB | 高性价比推理 |
| ecs.vgn7i-vni8 | L40s 48GB | 2 | 96GB | 多模型并发推理 |

### 选型决策矩阵

根据不同的应用场景，推荐以下选型方案：

```
应用场景                    推荐实例               月成本参考
─────────────────────────────────────────────────────────
≤7B 模型推理（低频）       vgn7i-vni4 (L40s)      ¥3,000-5,000
≤7B 模型推理（高频）       gn7-c12g1.3xlarge      ¥5,000-8,000
7B-14B 模型微调            gn7-c12g1.6xlarge      ¥15,000-25,000
14B-72B 模型推理           gn7-c12g1.12xlarge     ¥30,000-50,000
70B+ 模型训练              gm7-c12g1.12xlarge      ¥80,000-150,000
多模态模型（音视频）       gm7-c12g1.6xlarge       ¥40,000-70,000
```

**选型黄金法则：**

1. **推理优先选 L40s**：相同显存下，L40s 价格比 A100 低 40-60%，推理性能相当
2. **训练优先选 A100/H800**：NVLink 互联和多卡扩展性更好
3. **显存是硬约束**：模型大小决定了 GPU 显存下限，算力可以降低但显存不能少
4. **预留实例降成本**：长期稳定负载（>3 个月）用预留实例，可节省 30-50%

> **常见陷阱**：很多团队只关注 GPU 算力，忽略了显存带宽。对于大模型推理，显存带宽往往是瓶颈而非算力。A100 的 2TB/s 显存带宽是其推理性能优异的关键原因。

---

## 2.1.2 弹性容器实例 ECI 与大模型部署

### ECI 简介

弹性容器实例（Elastic Container Instance，ECI）是阿里云提供的 Serverless 容器服务。对于大模型应用，ECI 提供了以下优势：

- **无需管理节点**：无需购买和维护 ECS 实例
- **按秒计费**：精确到秒的计费粒度
- **自动弹性**：根据负载自动扩缩容
- **兼容 Kubernetes**：完全兼容 K8s API

### GPU 加速的 ECI

阿里云 ECI 支持指定 GPU 类型来创建容器组：

```python
# 使用 ECI SDK 创建 GPU 容器实例
from alibabacloud_eci20180808.client import Client
from alibabacloud_eci20180808.models import CreateContainerGroupRequest

client = Client(
    access_key_id=os.getenv('ALIBABA_CLOUD_ACCESS_KEY_ID'),
    access_key_secret=os.getenv('ALIBABA_CLOUD_ACCESS_KEY_SECRET'),
    endpoint='eci.cn-beijing.aliyuncs.com'
)

request = CreateContainerGroupRequest(
    region_id='cn-beijing',
    container_group_name='llm-inference',
    security_group_id='sg-xxxxxxxx',
    v_switch_id='vsw-xxxxxxxx',
    # 指定 GPU 规格
    instance_type='eci.gn7i-c12g1.3xlarge',
    containers=[
        {
            'name': 'llm-app',
            'image': 'registry.cn-beijing.aliyuncs.com/your-ns/llm-inference:v1',
            'cpu': 4,
            'memory': 16.0,
            'gpu': 1,  # 请求 1 块 GPU
            'ports': [{'port': 8000, 'protocol': 'TCP'}],
            'environment_vars': [
                {'key': 'MODEL_NAME', 'value': 'qwen-7b'},
                {'key': 'DASHSCOPE_API_KEY', 'value': os.getenv('DASHSCOPE_API_KEY')}
            ]
        }
    ]
)

response = client.create_container_group(request)
print(f"容器组 ID: {response.body.container_group_id}")
```

### ECI 适用场景

| 场景 | 推荐度 | 原因 |
|-----|-------|------|
| API 调用型推理（使用百炼/DashScope） | ★★★★★ | 无需 GPU，ECI 完美匹配 |
| 自部署轻量模型（≤7B） | ★★★★☆ | 灵活弹性，成本可控 |
| 大规模并发推理 | ★★★☆☆ | 单容器能力有限，需配合 K8s |
| 模型训练 | ★★☆☆☆ | 训练时间长，成本不如预留实例 |

---

## 2.1.3 PAI 平台：一站式模型训练与部署

### PAI 平台概述

阿里云 PAI（Platform of Artificial Intelligence）是面向企业的一站式机器学习平台，覆盖模型开发、训练、部署、管理的全生命周期。对于大模型场景，PAI 提供了以下核心能力：

```
┌──────────────────────────────────────────────┐
│                PAI 平台架构                   │
├──────────────────────────────────────────────┤
│  PAI-Studio     │  交互式开发环境（Notebook）  │
│  PAI-DSW        │  深度学习工作站（GPU 实例）  │
│  PAI-DLC        │  分布式训练（多机多卡）      │
│  PAI-EAS        │  模型在线服务（推理部署）     │
│  PAI-FeatureStore │  特征管理平台              │
└──────────────────────────────────────────────┘
```

### PAI-DSW：交互式模型开发

DSW（Deep Learning Workshop）提供预配置的 Jupyter Notebook 环境，支持一键启动 GPU 实例：

```python
# 在 PAI-DSW 中使用通义千问进行模型微调
from modelscope import AutoModel, AutoTokenizer
import torch

# 加载预训练模型
model_name = "qwen/Qwen2.5-7B-Instruct"
tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
model = AutoModel.from_pretrained(
    model_name,
    trust_remote_code=True,
    torch_dtype=torch.bfloat16,
    device_map="auto"
)

# 查看 GPU 使用情况
print(f"模型显存占用: {torch.cuda.memory_allocated() / 1024**3:.2f} GB")
print(f"GPU 型号: {torch.cuda.get_device_name(0)}")
```

### PAI-DLC：分布式模型训练

对于大规模模型训练（如全量微调 72B 模型），PAI-DLC 提供了多机多卡的分布式训练能力：

```yaml
# PAI-DLC 训练任务配置
apiVersion: "pai.alibabacloud.com/v1alpha1"
kind: "PyTorchJob"
metadata:
  name: "qwen-finetune"
spec:
  pytorchReplicaSpecs:
    Worker:
      replicas: 4  # 4 个训练节点
      template:
        spec:
          containers:
          - name: pytorch
            image: registry.cn-beijing.aliyuncs.com/pai/llm-train:latest
            resources:
              limits:
                nvidia.com/gpu: 8  # 每节点 8 卡
            command:
            - python
            - -m
            - torch.distributed.launch
            - --nproc_per_node=8
            - --nnodes=4
            - finetune.py
            - --model_name=qwen/Qwen2.5-7B
            - --data_path=oss://my-bucket/training-data/
            - --output_path=oss://my-bucket/output/
```

### PAI-EAS：模型在线部署

将训练好的模型部署为在线推理服务：

```python
# PAI-EAS 部署大模型推理服务
from alibabacloud_pai_eas20230131.client import Client
from alibabacloud_pai_eas20230131.models import CreateServiceRequest

client = Client(access_key_id='xxx', access_key_secret='xxx')

# 创建推理服务
request = CreateServiceRequest(
    service_name='qwen-7b-finetuned',
    service_config='''
    {
        "metadata": {
            "instance": 2,
            "resource": "ecs.gn7i-c12g1.3xlarge"
        },
        "containers": [{
            "image": "registry.cn-beijing.aliyuncs.com/pai/llm-inference:vllm",
            "port": 8000,
            "env": [{
                "name": "MODEL_PATH",
                "value": "oss://my-bucket/models/qwen-7b-finetuned"
            }]
        }]
    }
    '''
)

response = client.create_service(request)
print(f"推理服务地址: {response.body.service_url}")
```

> **最佳实践**：对于大多数企业，建议使用 PAI-EAS 部署自训练模型，而不是直接在 ECS 上搭建推理服务。PAI-EAS 内置了模型优化、自动扩缩容、灰度发布等企业级功能，可以大幅降低运维复杂度。

---

## 2.1.4 GPU 池化与百炼平台调度

### 传统 GPU 调度的痛点

在传统模式下，GPU 资源以整卡为单位分配给特定模型，存在严重浪费：

```
场景：3 个模型部署在 3 张 A100 上

模型 A（Qwen-7B 推理）  → 占用 GPU #1，利用率 25%
模型 B（Embedding）      → 占用 GPU #2，利用率 15%
模型 C（图像理解）        → 占用 GPU #3，利用率 35%

总体 GPU 利用率：25% → 巨大的资源浪费！
```

### 百炼平台的 GPU 池化技术

阿里云百炼平台通过 GPU 池化技术解决了这个问题。其核心技术论文《Aegaeon: Token-Level GPU Scheduling for Multi-Model Inference》发表于 SOSP 2025，代表了大模型基础设施领域的前沿水平。

**工作原理：**

```
传统模式（独占）：
  GPU #1 → 模型 A（独占）
  GPU #2 → 模型 B（独占）
  GPU #3 → 模型 C（独占）

GPU 池化模式（共享）：
  GPU Pool = [GPU #1, GPU #2, GPU #3]
       ↓
  Token 级调度器
       ↓
  请求 A 的 token → GPU #1
  请求 B 的 token → GPU #2
  请求 A 的 token → GPU #3  （同一请求的不同 token 可分布在不同 GPU）
```

**性能提升：**

| 指标 | 传统独占模式 | GPU 池化模式 | 提升 |
|-----|------------|------------|------|
| GPU 平均利用率 | 30% | 75%+ | 2.5x |
| 单卡并发请求数 | 5-10 | 20-50 | 5x |
| 推理延迟 P99 | 500ms | <200ms | 2.5x |
| 单位 token 成本 | 基准 | -60% | 显著降低 |

### 对技术决策者的启示

GPU 池化技术的意义在于：

1. **降低推理成本**：相同硬件资源可服务更多用户
2. **提升用户体验**：更低的延迟和更高的可用性
3. **简化运维**：无需手动分配和调优 GPU 资源

> **决策建议**：如果你的企业需要同时运行多个大模型（对话、Embedding、图像理解等），强烈建议使用百炼平台的 API 服务，而不是自建 GPU 集群。GPU 池化带来的成本优势在规模化场景下非常显著。

---

## 2.1.5 预留实例与 Spot 实例策略

### 三种计费模式对比

| 计费模式 | 价格 | 适用场景 | 灵活性 |
|---------|------|---------|-------|
| **按量付费** | 原价 | 开发测试、突发流量 | 最高 |
| **预留实例** | 原价的 50-70% | 长期稳定负载（>3月） | 中等 |
| **Spot 实例** | 原价的 10-30% | 可中断的离线任务 | 最低 |

### 预留实例策略

预留实例（Reserved Instance）适合 7×24 小时运行的推理服务：

```python
# 使用阿里云 SDK 查询预留实例价格
from alibabacloud_ecs20140526.client import Client
from alibabacloud_ecs20140526.models import DescribeReservedInstancesRequest

client = Client(access_key_id='xxx', access_key_secret='xxx')

# 查询 A100 预留实例价格
response = client.describe_reserved_instances(
    DescribeReservedInstancesRequest(
        region_id='cn-beijing',
        instance_type='ecs.gn7-c12g1.3xlarge',
        scope='Region',
        offering_type='All Upfront',  # 全预付（最便宜）
        reserved_instance_offering_type='No Upfront'  # 无预付
    )
)

# 成本对比计算
hourly_ondemand = 28.5  # 按量 ¥28.5/小时
hourly_reserved = 14.0  # 预留 ¥14.0/小时
monthly_savings = (hourly_ondemand - hourly_reserved) * 24 * 30
print(f"预留实例月节省：¥{monthly_savings:,.0f}")
```

### Spot 实例策略

Spot 实例价格极低，但可能被系统随时回收。适合以下场景：

**适合 Spot 的场景：**
- 模型训练（可设置 Checkpoint，中断后恢复）
- 离线批量推理（文档 Embedding、数据标注）
- 开发环境（Jupyter Notebook）

**不适合 Spot 的场景：**
- 在线推理服务（不能中断）
- 实时风控（延迟敏感）

```python
# Spot 实例训练脚本（带 Checkpoint）
import torch
import os
from datetime import datetime

class SpotAwareTrainer:
    """支持 Spot 实例中断恢复的训练器"""

    def __init__(self, model, optimizer, checkpoint_dir='checkpoints'):
        self.model = model
        self.optimizer = optimizer
        self.checkpoint_dir = checkpoint_dir
        os.makedirs(checkpoint_dir, exist_ok=True)

    def save_checkpoint(self, step):
        """保存 Checkpoint"""
        checkpoint = {
            'step': step,
            'model_state_dict': self.model.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'timestamp': datetime.now().isoformat()
        }
        path = f"{self.checkpoint_dir}/step_{step}.pt"
        torch.save(checkpoint, path)
        print(f"Checkpoint 已保存: {path}")

    def load_latest_checkpoint(self):
        """加载最新 Checkpoint"""
        if not os.path.exists(self.checkpoint_dir):
            return 0

        checkpoints = [f for f in os.listdir(self.checkpoint_dir) if f.endswith('.pt')]
        if not checkpoints:
            return 0

        latest = max(checkpoints, key=lambda x: int(x.split('_')[1].split('.')[0]))
        checkpoint = torch.load(f"{self.checkpoint_dir}/{latest}")
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        print(f"从 {latest} 恢复训练 (保存于 {checkpoint['timestamp']})")
        return checkpoint['step']

    def train_with_spot_handling(self, train_fn, max_steps=10000, save_interval=500):
        """带 Spot 中断处理的训练"""
        try:
            start_step = self.load_latest_checkpoint()

            for step in range(start_step, max_steps):
                train_fn(step)

                # 定期保存 Checkpoint
                if (step + 1) % save_interval == 0:
                    self.save_checkpoint(step + 1)

        except Exception as e:
            # Spot 实例被回收时，触发中断信号
            print(f"训练中断: {e}")
            self.save_checkpoint(step)  # 紧急保存
            raise

# 使用示例
trainer = SpotAwareTrainer(model, optimizer)
trainer.train_with_spot_handling(
    train_fn=lambda step: train_step(model, optimizer, dataloader),
    max_steps=50000,
    save_interval=1000
)
```

### 混合策略推荐

对于大多数大模型应用团队，推荐以下混合策略：

```
生产推理服务（7×24）  → 预留实例（70% 基础负载）+ 按量付费（30% 弹性）
模型微调训练          → Spot 实例（成本最低，可中断恢复）
开发测试环境          → Spot 实例 或 PAI-DSW（按量计费）
数据处理/Embedding    → Spot 实例（离线批处理，不要求实时）
```

---

## 本节小结

本节系统介绍了阿里云的 GPU/NPU 计算资源体系：

1. **实例选型**：根据模型大小和应用场景，在 A100、H800、L40s 之间做出最优选择
2. **ECI 部署**：Serverless 容器化方案，适合 API 调用型推理和轻量模型部署
3. **PAI 平台**：一站式模型开发、训练、部署平台，降低运维复杂度
4. **GPU 池化**：百炼平台的 Token 级调度技术，大幅提升资源利用率
5. **成本策略**：预留实例 + Spot 实例 + 按量付费的混合策略，在稳定性和成本之间取得平衡

技术决策者在选择计算资源时，应遵循"先评估、再预留、Spot 补充"的原则，避免过度采购或资源不足。
