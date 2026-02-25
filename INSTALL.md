# ptracker 安装指南

## 系统要求

- Python 3.10 或更高版本
- conda 或其他 Python 环境管理工具（推荐）
- 网络连接（用于安装依赖和查询价格）

## 安装步骤

### 方式 1: 使用安装脚本（推荐）

```bash
# 1. 激活 conda 环境
conda activate quantdev

# 2. 运行安装脚本
./install.sh

# 3. 按提示选择安装模式
#    - 选项 1: 开发模式（代码修改立即生效）
#    - 选项 2: 正式安装
```

### 方式 2: 手动安装

#### 开发模式（推荐用于开发）

```bash
# 激活环境
conda activate quantdev

# 安装（可编辑模式）
pip install -e .
```

这种方式安装后，你修改代码不需要重新安装，`ptracker` 命令会自动使用最新代码。

#### 正式安装

```bash
# 激活环境
conda activate quantdev

# 安装
pip install .
```

#### 使用 pipx（全局安装）

```bash
# 安装 pipx（如果还没有）
python -m pip install --user pipx
python -m pipx ensurepath

# 使用 pipx 安装 ptracker
pipx install .
```

#### 使用 uv

```bash
# 安装 uv（如果还没有）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 使用 uv 安装
uv pip install .
```

## 验证安装

### 基本验证

```bash
# 检查版本（三种方式都可以）
ptracker --version
ptracker -v
ptracker version

# 查看帮助
ptracker --help

# 查看子命令帮助
ptracker account --help
ptracker trade --help
ptracker query --help
```

### 完整测试

```bash
# 运行安装测试脚本
./test_install.sh

# 或手动运行单元测试
python run_tests.py
```

### 检查 Python 包

```bash
# 查看包信息
pip show ptracker

# 在 Python 中导入
python -c "import ptracker; print(ptracker.__version__)"
```

## 依赖包

安装时会自动安装以下依赖：

- **typer** - CLI 框架
- **rich** - 终端美化输出
- **tinydb** - 轻量级 JSON 数据库
- **filelock** - 文件锁（并发保护）
- **pydantic** - 数据验证
- **yfinance** - Yahoo Finance 价格查询
- **akshare** - A股、港股、期货价格查询
- **python-dateutil** - 日期处理
- **toml** - 配置文件解析

## 初始化

安装完成后，需要初始化数据目录：

```bash
ptracker init
```

这会在 `~/.ptracker/` 创建以下文件：

```
~/.ptracker/
├── transactions.json  # 交易记录
├── holdings.json      # 当前持仓
├── realized.json      # 已平仓记录
├── accounts.json      # 账户信息
└── config.toml        # 配置文件
```

## 常见问题

### 问题 1: 命令找不到

```bash
# 检查是否安装
pip show ptracker

# 检查命令路径
which ptracker

# 如果找不到，可能需要重新加载 shell
source ~/.zshrc  # 或 source ~/.bashrc
```

### 问题 2: 权限错误

```bash
# 使用 --user 选项
pip install --user -e .

# 或使用虚拟环境
conda activate quantdev
pip install -e .
```

### 问题 3: 依赖安装失败

```bash
# 更新 pip
pip install --upgrade pip

# 清理缓存后重试
pip cache purge
pip install -e .

# 或使用国内镜像
pip install -e . -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 问题 4: Python 版本不兼容

```bash
# 检查 Python 版本（需要 3.10+）
python --version

# 如果版本太低，创建新环境
conda create -n quantdev python=3.10
conda activate quantdev
pip install -e .
```

## 卸载

### 卸载程序（保留数据）

```bash
# 使用卸载脚本
./uninstall.sh

# 或手动卸载
pip uninstall ptracker
```

### 删除数据（可选）

```bash
# 备份数据（推荐）
cp -r ~/.ptracker ~/.ptracker.backup

# 删除数据
rm -rf ~/.ptracker
```

## 升级

### 开发模式

如果使用开发模式安装（`pip install -e .`），直接 `git pull` 更新代码即可，不需要重新安装。

### 正式安装

```bash
# 拉取最新代码
git pull

# 重新安装
pip install --upgrade .
```

## 多环境管理

### 在不同 conda 环境中安装

```bash
# 环境 1: 开发环境
conda activate quantdev
pip install -e .

# 环境 2: 生产环境
conda activate prod
pip install .
```

### 使用不同数据目录

```bash
# 默认数据目录: ~/.ptracker/
# 可以通过环境变量修改（未来功能）
export PTRACKER_DATA_DIR=~/my-portfolio
ptracker init
```

## 开发者安装

如果你要参与开发：

```bash
# 1. 克隆仓库
git clone <repository-url>
cd ptracker

# 2. 创建开发环境
conda create -n ptracker-dev python=3.10
conda activate ptracker-dev

# 3. 安装开发模式
pip install -e .

# 4. 安装开发工具（可选）
pip install pytest pytest-cov black flake8 mypy

# 5. 运行测试
python run_tests.py

# 6. 代码格式化
black ptracker tests

# 7. 类型检查
mypy ptracker
```

## 下一步

- 阅读快速开始指南：[QUICKSTART.md](QUICKSTART.md)
- 查看完整文档：[README.md](README.md)
- 查看开发进度：[PROGRESS.md](PROGRESS.md)

## 获取帮助

如果遇到问题：

1. 查看帮助文档：`ptracker --help`
2. 运行测试脚本：`./test_install.sh`
3. 查看日志和错误信息
4. 提交 issue 或联系开发者
