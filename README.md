# 云上大模型应用开发实践

> 以阿里云为主要平台，带领零基础读者从入门到实战，系统掌握云上大模型应用开发技能。

## 📖 在线阅读

访问本书在线版本：https://your-username.github.io/cloud-llm-book/

## 📚 内容概览

本书分为 8 个部分，共 33 章：

| 部分 | 主题 | 章节 |
|------|------|------|
| 第一部分 | 基础入门 | 1-4 |
| 第二部分 | Prompt 工程 | 5-8 |
| 第三部分 | 应用开发实战 | 9-15 |
| 第四部分 | 高级应用架构 | 16-20 |
| 第五部分 | 模型微调与训练 | 21-24 |
| 第六部分 | 云原生部署与运维 | 25-29 |
| 第七部分 | 项目实战案例 | 30-32 |
| 第八部分 | 前沿与展望 | 33 |

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

# 构建 PDF（需要 pandoc 和 basictex）
pandoc -o book.pdf --pdf-engine=xelatex src/SUMMARY.md
```

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

[CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/)

---

*作者：方华 · 2026*
