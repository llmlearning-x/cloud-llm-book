#!/bin/bash
# GitHub Pages 部署脚本
# 目标账号: llmlearning-x
# 目标仓库: cloud-llm-book

set -e

echo "🚀 开始部署书籍到 GitHub Pages..."

# 1. 确保在正确的分支上
git checkout gh-pages-deploy || {
    echo "❌ 找不到 gh-pages-deploy 分支，正在创建..."
    git subtree split --prefix book/html -b gh-pages-deploy
}

# 2. 推送到远程仓库的 gh-pages 分支
echo "📤 正在推送内容到 https://github.com/llmlearning-x/cloud-llm-book ..."
git push origin gh-pages-deploy:gh-pages --force

echo "✅ 部署成功！"
echo "请访问以下地址查看你的书籍（可能需要几分钟生效）："
echo "https://llmlearning-x.github.io/cloud-llm-book/"
