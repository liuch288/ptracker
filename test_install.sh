#!/bin/bash
# 测试 ptracker 安装是否正常

set -e

echo "🧪 测试 ptracker 安装..."
echo ""

# 测试 1: 版本命令
echo "测试 1: 版本命令"
ptracker --version
ptracker -v
ptracker version
echo "✓ 版本命令正常"
echo ""

# 测试 2: 帮助命令
echo "测试 2: 帮助命令"
ptracker --help > /dev/null
ptracker account --help > /dev/null
ptracker trade --help > /dev/null
ptracker query --help > /dev/null
echo "✓ 帮助命令正常"
echo ""

# 测试 3: 检查 Python 包
echo "测试 3: Python 包"
python -c "import ptracker; print(f'ptracker {ptracker.__version__}')"
echo "✓ Python 包导入正常"
echo ""

# 测试 4: 运行单元测试
echo "测试 4: 单元测试"
python run_tests.py
echo ""

echo "✅ 所有测试通过！ptracker 安装正常"
