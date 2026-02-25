# ptracker 快速开始指南

## 安装

### 1. 确保环境准备好

```bash
# 激活 conda 环境
conda activate quantdev

# 检查 Python 版本（需要 3.10+）
python --version
```

### 2. 安装 ptracker

```bash
# 开发模式（推荐，代码修改立即生效）
pip install -e .

# 或使用安装脚本
./install.sh
```

### 3. 验证安装

```bash
# 检查版本（三种方式）
ptracker --version
ptracker -v
ptracker version

# 查看帮助
ptracker --help

# 运行完整测试
./test_install.sh
```

## 初始化

```bash
# 使用默认颜色方案（绿色代表盈利/上涨）
ptracker init

# 指定颜色方案为西方风格（绿涨红跌）
ptracker init --color-scheme green_up

# 指定颜色方案为中国风格（红涨绿跌）
ptracker init --color-scheme red_up
ptracker init -c red_up
```

颜色方案说明：
- `green_up`（默认）: 绿色代表盈利/上涨，红色代表亏损/下跌（西方风格）
- `red_up`: 红色代表盈利/上涨，绿色代表亏损/下跌（中国风格）

这会在 `~/.ptracker/` 创建以下文件：
- `transactions.json` - 交易记录
- `holdings.json` - 持仓信息
- `realized.json` - 已平仓记录
- `accounts.json` - 账户信息
- `config.toml` - 配置文件

## 基本使用流程

### 1. 添加账户

```bash
# 添加美股账户
ptracker account add ibkr --type brokerage --desc "Interactive Brokers" --currency USD

# 添加港股账户
ptracker account add futu --type brokerage --desc "富途证券" --currency HKD

# 查看所有账户
ptracker account list
```

### 2. 记录交易

#### 买入开仓（做多）

```bash
# 买入美股
ptracker trade add buy AAPL 100 150.0 \
  --currency USD \
  --action open \
  --direction long \
  --account ibkr \
  --note "建仓苹果"

# 买入港股
ptracker trade add buy 0700.HK 500 320.5 \
  --currency HKD \
  --action open \
  --direction long \
  --account futu \
  --note "建仓腾讯"
```

#### 卖出开仓（做空）

```bash
# 卖空美股
ptracker trade add sell TSLA 50 200.0 \
  --currency USD \
  --action open \
  --direction short \
  --account ibkr \
  --note "做空特斯拉"
```

#### 平仓

```bash
# 卖出平仓（平多头）
ptracker trade add sell AAPL 100 160.0 \
  --currency USD \
  --action close \
  --direction long \
  --account ibkr \
  --note "止盈平仓"

# 买入平仓（平空头）
ptracker trade add buy TSLA 50 180.0 \
  --currency USD \
  --action close \
  --direction short \
  --account ibkr \
  --note "止盈平空"
```

#### 加仓/减仓

```bash
# 加仓（继续买入）
ptracker trade add buy 0700.HK 300 310.0 \
  --currency HKD \
  --action open \
  --direction long \
  --account futu \
  --note "回调加仓"

# 减仓（部分平仓）
ptracker trade add sell 0700.HK 200 330.0 \
  --currency HKD \
  --action close \
  --direction long \
  --account futu \
  --note "部分止盈"
```

### 3. 查看交易记录

```bash
# 查看所有交易
ptracker trade list

# 按资产筛选
ptracker trade list --asset AAPL

# 按账户筛选
ptracker trade list --account ibkr

# 按日期范围筛选
ptracker trade list --from 2026-01-01 --to 2026-12-31

# 按交易类型筛选
ptracker trade list --type buy
ptracker trade list --action open
ptracker trade list --direction long
```

### 4. 查看持仓

```bash
# 查看所有活跃持仓
ptracker query holdings

# 查看特定账户
ptracker query holdings --account ibkr

# 查看特定资产
ptracker query holdings --asset AAPL

# 包含已平仓记录
ptracker query holdings --include-closed

# 排序
ptracker query holdings --sort total_invested

# 货币转换
ptracker query holdings --currency USD
```

### 5. 查看投资组合价值

```bash
# 查看总价值（需要联网获取实时价格）
ptracker query value

# 按资产分类
ptracker query value --breakdown asset

# 按账户分类
ptracker query value --breakdown account

# 按货币分类
ptracker query value --breakdown currency

# 转换为特定货币
ptracker query value --currency USD
```

### 6. 查看单个资产价格

```bash
# 查询美股价格
ptracker price AAPL

# 查询港股价格
ptracker price 0700.HK

# 查询加密货币价格
ptracker price BTC-USD
```

## 常见场景示例

### 场景 1: 美股长期投资

```bash
# 1. 添加账户
ptracker account add ibkr --type brokerage --currency USD

# 2. 建仓
ptracker trade add buy AAPL 100 150.0 --currency USD --action open --direction long --account ibkr

# 3. 加仓
ptracker trade add buy AAPL 50 145.0 --currency USD --action open --direction long --account ibkr --note "回调加仓"

# 4. 查看持仓（平均成本会自动计算）
ptracker query holdings --asset AAPL

# 5. 部分止盈
ptracker trade add sell AAPL 50 170.0 --currency USD --action close --direction long --account ibkr --note "部分止盈"

# 6. 查看已实现盈亏
ptracker query holdings --include-closed
```

### 场景 2: 港股短线交易

```bash
# 1. 添加账户
ptracker account add futu --type brokerage --currency HKD

# 2. 建仓
ptracker trade add buy 0700.HK 1000 320.0 --currency HKD --action open --direction long --account futu --note "突破买入"

# 3. 止盈平仓
ptracker trade add sell 0700.HK 1000 335.0 --currency HKD --action close --direction long --account futu --note "达到目标价"

# 4. 查看已平仓记录
ptracker query holdings --include-closed --asset 0700.HK
```

### 场景 3: 做空交易

```bash
# 1. 卖空开仓
ptracker trade add sell TSLA 100 250.0 --currency USD --action open --direction short --account ibkr --note "高位做空"

# 2. 买入平仓
ptracker trade add buy TSLA 100 220.0 --currency USD --action close --direction short --account ibkr --note "止盈平空"
```

### 场景 4: 多账户管理

```bash
# 查看所有账户的持仓
ptracker query holdings

# 查看特定账户
ptracker query holdings --account ibkr
ptracker query holdings --account futu

# 查看总价值（所有账户）
ptracker query value

# 按账户分类查看
ptracker query value --breakdown account
```

## 配置文件

配置文件位于 `~/.ptracker/config.toml`：

```toml
[general]
default_currency = "USD"
default_account = ""
cost_basis_method = "average"  # average 或 fifo

[display]
date_format = "%Y-%m-%d"
decimal_places = 2
color_scheme = "green_up"  # green_up 或 red_up

[api]
# 未来可添加 API keys
```

### 配置管理命令

```bash
# 查看当前配置
ptracker config show

# 修改配置项
ptracker config set display.color_scheme red_up
ptracker config set general.default_currency CNY

# 交互式修改颜色方案
ptracker config color
```

## 数据备份

```bash
# 备份所有数据
cp -r ~/.ptracker ~/.ptracker.backup

# 或只备份特定文件
cp ~/.ptracker/transactions.json ~/backup/transactions_$(date +%Y%m%d).json
```

## 故障排除

### 问题 1: 命令找不到

```bash
# 检查是否安装
pip show ptracker

# 重新安装
pip install -e .
```

### 问题 2: 价格查询失败

```bash
# 检查网络连接
ping finance.yahoo.com

# 手动测试价格查询
ptracker price AAPL
```

### 问题 3: 数据文件损坏

```bash
# 检查 JSON 文件格式
python -m json.tool ~/.ptracker/transactions.json

# 从备份恢复
cp ~/.ptracker.backup/transactions.json ~/.ptracker/
```

## 卸载

```bash
# 卸载程序（保留数据）
pip uninstall ptracker

# 或使用卸载脚本
./uninstall.sh

# 删除数据（可选）
rm -rf ~/.ptracker
```

## 下一步

- 查看完整文档：`README.md`
- 查看开发进度：`PROGRESS.md`
- 运行测试：`python run_tests.py`
