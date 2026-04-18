# 云上智能：大模型应用开发实战

> 以阿里云为主要平台，带领零基础读者从入门到实战，系统掌握云上大模型应用开发技能。

## 📖 在线阅读

访问本书在线版本：https://llmlearning-x.github.io/cloud-llm-book/

## 📚 内容概览

本书分为 **6 个部分，共 18 章**，涵盖云计算基础、大模型理论、Prompt 工程、应用开发、高级架构和模型微调：

| 部分 | 主题 | 章节 | 内容 |
|------|------|------|------|
| 第一部分 | 云计算基础 | 1-3 | IaaS/PaaS/SaaS、阿里云核心产品（OSS/FC/ACK/RDS/SLS） |
| 第二部分 | 大模型基础 | 4-6 | Transformer 架构、通义千问/DashScope API 快速入门 |
| 第三部分 | Prompt 工程 | 7-8 | 核心要素、Zero/Few-shot、CoT、ReAct、System Prompt |
| 第四部分 | 应用开发实战 | 9-13 | Gradio/FastAPI、RAG 知识库、智能客服、内容生成、垂直领域 |
| 第五部分 | 高级应用架构 | 14-16 | Advanced RAG、Agent 智能体、向量数据库（Milvus） |
| 第六部分 | 模型微调与部署 | 17-18 | PAI LoRA 微调、Docker/FC/ACK 部署、监控与安全 |

附录 A-D：阿里云产品速查表、常用工具资源、术语表、错误码 FAQ

**全书约 23 万字，包含完整代码示例。**

## 🚀 快速开始

### 本地预览

```bash
# 安装 mdBook
cargo install mdbook

# 或使用 Homebrew
brew install mdbook

# 启动本地服务器
mdbook serve

# 或打开浏览器
mdbook serve --open
```

### Docker 方式

```bash
docker run -p 3000:3000 -v $(pwd):/book ghcr.io/h extrah/mdbook-serve:latest
```

## 📦 构建

```bash
# 构建 HTML
mdbook build

# 构建 PDF（需要 pandoc 和 xelatex）
pandoc -o book.pdf --pdf-engine=xelatex src/SUMMARY.md
```

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

[CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/)

---

*作者：方华 · 2026*
