# ptracker

Personal investment portfolio tracking CLI tool for managing diverse portfolios across multiple markets.

## Features

- Multi-account support (brokerage, exchange)
- Multi-market support (Hong Kong stocks, US stocks, A-shares, cryptocurrencies, futures)
- Long and short position tracking
- Automatic position calculation and P&L tracking
- Local JSON-based storage with TinyDB
- Price queries with yfinance and akshare fallback
- Rich terminal output with tables and colors
- Customizable color scheme (green-up or red-up)

## Installation

详细安装说明请查看 [INSTALL.md](INSTALL.md)

### 快速安装

**方式 1: 使用安装脚本（推荐）**
```bash
conda activate quantdev
./install.sh
```

**方式 2: 开发模式（推荐用于开发）**

如果你想修改代码并立即生效，使用开发模式：

```bash
# 激活 conda 环境
conda activate quantdev

# 在项目根目录下安装（可编辑模式）
pip install -e .
```

这样安装后，你修改代码不需要重新安装，`ptracker` 命令会自动使用最新代码。

### 方式 2: 正式安装

如果只是使用，不需要修改代码：

```bash
# 使用 pip
pip install .

# 或使用 pipx（全局安装，推荐）
pipx install .

# 或使用 uv
uv pip install .
```

### 方式 3: 使用 poetry

```bash
poetry install
```

### 验证安装

```bash
# 检查版本（三种方式都可以）
ptracker --version
ptracker -v
ptracker version

# 查看帮助
ptracker --help

# 运行测试
./test_install.sh
```

## Requirements

- Python 3.10 or higher
- 依赖包（自动安装）：
  - typer - CLI 框架
  - rich - 终端美化
  - tinydb - JSON 数据库
  - filelock - 文件锁
  - pydantic - 数据验证
  - yfinance - 价格查询（美股、港股）
  - akshare - 价格查询（A股、期货）
  - python-dateutil - 日期处理
  - toml - 配置文件

## 数据存储

所有数据存储在 `~/.ptracker/` 目录：

```
~/.ptracker/
├── transactions.json  # 交易记录（不可变日志）
├── holdings.json      # 当前持仓
├── realized.json      # 已平仓记录
├── accounts.json      # 账户信息
└── config.toml        # 配置文件
```

## Quick Start

1. 初始化系统：
```bash
# 使用默认颜色方案（绿涨红跌）
ptracker init

# 或指定颜色方案
ptracker init --color-scheme green_up  # 绿涨红跌（西方风格）
ptracker init --color-scheme red_up    # 红涨绿跌（中国风格）
```

2. 添加账户：
```bash
ptracker account add ibkr --type brokerage --desc "Interactive Brokers" --currency USD
ptracker account add futu --type brokerage --desc "富途证券" --currency HKD
```

3. 记录交易：
```bash
# 买入美股
ptracker trade add buy AAPL 100 150.0 --currency USD --action open --direction long --account ibkr

# 买入港股
ptracker trade add buy 0700.HK 500 320.5 --currency HKD --action open --direction long --account futu --note "建仓腾讯"
```

4. 查看持仓：
```bash
# 查看所有持仓
ptracker query holdings

# 查看特定账户
ptracker query holdings --account ibkr

# 包含已平仓记录
ptracker query holdings --include-closed
```

5. 查看投资组合价值：
```bash
# 查看总价值
ptracker query value

# 按资产分类
ptracker query value --breakdown asset

# 转换为特定货币
ptracker query value --currency USD
```

6. 平仓交易：
```bash
# 卖出平仓
ptracker trade add sell AAPL 100 160.0 --currency USD --action close --direction long --account ibkr --note "止盈"
```

## 命令概览

```bash
ptracker init                    # 初始化数据目录（可选 --color-scheme）
ptracker config show/set/color   # 配置管理
ptracker account add/list/query  # 账户管理
ptracker trade add/list          # 交易记录
ptracker query holdings/value    # 查询持仓和价值
```

## License

MIT
