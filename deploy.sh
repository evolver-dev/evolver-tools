#!/bin/bash
# deploy.sh — 一键部署 Evolver CLI Tools 到 GitHub Pages
# 
# 使用方法:
#   1. 先在 GitHub 创建一个 personal access token (classic, 勾选 repo 权限)
#   2. export GH_TOKEN="ghp_xxxxxxxxxxxx"
#   3. bash deploy.sh
#
# 或者:
#   1. gh auth login
#   2. bash deploy.sh

set -e

SITE_DIR="/root/evolver-site"
REPO="evolver-cli/evolver-tools"

echo "⚡ Evolver CLI Tools — Deploy to GitHub Pages"
echo ""

# Check auth
if ! gh auth status &>/dev/null; then
    if [ -z "$GH_TOKEN" ]; then
        echo "❌ 需要 GitHub 认证"
        echo ""
        echo "请选择一种方式:"
        echo "  1. export GH_TOKEN=\"ghp_xxxxxxxxxxxx\"   (用 Personal Access Token)"
        echo "  2. gh auth login                          (交互式登录)"
        echo ""
        echo "Token 需要 repo 权限。在 https://github.com/settings/tokens 创建"
        exit 1
    fi
    echo "$GH_TOKEN" | gh auth login --with-token
fi

echo "✅ GitHub 认证成功"
echo ""

# Create repo if not exists
cd "$SITE_DIR"

echo "📦 创建 GitHub 仓库: $REPO"
gh repo create "$REPO" --public --description "20 零依赖 Python CLI 工具 — pip install 即用" --source=. --remote=origin --push 2>&1 || {
    echo "⚠️  仓库可能已存在，尝试推送..."
    git remote add origin "https://github.com/$REPO.git" 2>/dev/null || true
    git push -u origin master 2>&1
}

echo ""
echo "✅ 代码已推送到 GitHub"
echo ""

# Enable GitHub Pages
echo "🌐 启用 GitHub Pages..."
gh api repos/$REPO/pages -X POST \
    -f source.branch=master \
    -f source.path=/ 2>/dev/null || {
    echo "⚠️  Pages 可能已启用，尝试更新..."
    gh api repos/$REPO/pages -X PUT \
        -f source.branch=master \
        -f source.path=/ 2>/dev/null || true
}

echo ""
echo "✅ 部署完成!"
echo "   🌍 https://cli.evolver.dev"
echo "   📦 https://github.com/$REPO"
echo ""
echo "⏱  DNS 和 Pages 构建可能需要 2-5 分钟生效"
