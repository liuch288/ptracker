#!/bin/bash
# ptracker 安装脚本

set -e

echo "🚀 开始安装 ptracker..."

# 检查 Python 版本
python_version=$(python --version 2>&1 | awk '{print $2}')
echo "✓ 检测到 Python 版本: $python_version"

# 检查是否在虚拟环境中
if [[ -z "$VIRTUAL_ENV" ]] && [[ -z "$CONDA_DEFAULT_ENV" ]]; then
    echo "⚠️  警告: 未检测到虚拟环境"
    echo "   建议先激活 conda 环境: conda activate quantdev"
    read -p "   是否继续安装? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ 安装已取消"
        exit 1
    fi
fi

# 选择安装模式
echo ""
echo "请选择安装模式:"
echo "  1) 开发模式 (可编辑，修改代码立即生效)"
echo "  2) 正式安装 (不可编辑)"
read -p "请输入选项 (1/2): " choice

case $choice in
    1)
        echo "📦 使用开发模式安装..."
        pip install -e .
        ;;
    2)
        echo "📦 使用正式模式安装..."
        pip install .
        ;;
    *)
        echo "❌ 无效选项"
        exit 1
        ;;
esac

echo ""
echo "✅ 安装完成!"
echo ""
echo "验证安装:"
ptracker --version
echo ""
echo "下一步:"
echo "  1. 初始化: ptracker init"
echo "  2. 查看帮助: ptracker --help"
