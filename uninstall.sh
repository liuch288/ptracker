#!/bin/bash
# ptracker 卸载脚本

set -e

echo "🗑️  开始卸载 ptracker..."

# 检查是否已安装
if ! pip show ptracker > /dev/null 2>&1; then
    echo "❌ ptracker 未安装"
    exit 1
fi

echo ""
echo "⚠️  警告: 这将卸载 ptracker 程序"
echo "   数据文件 (~/.ptracker/) 不会被删除"
echo ""
read -p "是否继续? (y/N) " -n 1 -r
echo

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ 卸载已取消"
    exit 1
fi

# 卸载
pip uninstall -y ptracker

echo ""
echo "✅ ptracker 已卸载"
echo ""
echo "如需删除数据文件，请手动执行:"
echo "  rm -rf ~/.ptracker"
