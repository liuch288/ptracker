---
name: ptracker
description: 个人投资组合跟踪工具，用于管理多市场、多账户的投资组合，记录交易、查询持仓和盈亏。支持港股、美股、A股、加密货币等多种资产类型，支持做多做空。
---

# ptracker - 投资组合跟踪 CLI 工具

个人投资组合跟踪命令行工具，支持跨市场、跨账户的投资组合管理。

## 运行环境

- **Conda 环境**: `quantdev`
- **运行命令**: `conda run -n quantdev ptracker <command>`
- **项目路径**: `~/dev/ptracker`
- **Python 版本**: 3.10+
- **数据目录**: `~/.ptracker/`

## 核心功能

### 1. 多市场支持
- 港股（如 0700.HK）
- 美股（如 AAPL）
- A股（如 600519.SS）
- 加密货币（如 BTC-USD）
- 期货合约

### 📋 Yahoo Finance 代码格式规范（必读）

> ⚠️ **重要**: 录入交易时必须按照以下格式，否则系统会报错并拒绝录入。

| 市场 | 格式 | 示例 | 说明 |
|------|------|------|------|
| **美股** | 1-5个大写字母，无后缀 | `AAPL`, `MSFT`, `TSLA` | 苹果、微软、特斯拉 |
| **美股期权** | 标的+YYMMDD+C/P+行权价×1000 | `AAPL250117C00150000` | 苹果25年1月17日看涨期权，行权价$150 |
| **港股** | 4位数字 + .HK | `0700.HK`, `9988.HK`, `0388.HK` | 腾讯、阿里、港交所 |
| **沪股** | 6位数字(6开头) + .SS | `600519.SS`, `688001.SS` | 茅台、蚂蚁集团 |
| **深股** | 6位数字(0-3开头) + .SZ | `000001.SZ`, `300001.SZ` | 平安银行、创业板 |
| **日股** | 4位数字 + .T | `7203.T`, `9984.T` | 丰田、软银 |
| **英股** | 股票代码 + .L | `HSBA.L`, `BP.L` | 汇丰、英国石油 |
| **德股** | 股票代码 + .DE | `BMW.DE`, `SAP.DE` | 宝马、思爱普 |
| **澳股** | 股票代码 + .AX | `BHP.AX`, `CBA.AX` | 必和必拓、澳联邦银行 |
| **加股** | 股票代码 + .TO | `RY.TO`, `TD.TO` | 皇家银行、道明银行 |
| **印股** | 股票代码 + .NS | `RELIANCE.NS`, `TCS.NS` | 信实工业、塔塔咨询 |
| **指数** | ^ + 字母 | `^HSI`, `^SSEC`, `^N225` | 恒生指数、上证指数、日经225 |

#### 美股期权格式详解
```
标的代码 + 到期年(YY) + 到期月(mm) + 到期日(dd) + C/P + 行权价
```
- **标的代码**: 1-4位大写字母（如 AAPL, TSLA）
- **到期年份**: 后两位（如 25 = 2025年）
- **到期月份**: 两位（如 01 = 1月）
- **到期日期**: 两位（如 17 = 17日）
- **期权类型**: C = 看涨期权，P = 看跌期权
- **行权价**: 8位数字（行权价 × 1000，如 00150000 = $150.00）

**示例**: `AAPL250117C00150000`
- 标的: AAPL（苹果）
- 到期日: 2025年1月17日
- 类型: 看涨期权 (C)
- 行权价: $150.00

### 2. 多账户管理
- 支持多个券商账户（brokerage）
- 支持多个交易所账户（exchange）
- 每个账户独立跟踪持仓和盈亏
- 支持账户间资金转移

### 3. 交易类型
- **开仓交易**: 建立新仓位（做多或做空）
- **平仓交易**: 关闭现有仓位
- **加仓**: 增加现有仓位
- **减仓**: 部分平仓
- **分红**: 记录股息收入
- **做多**: 买入开仓，卖出平仓
- **做空**: 卖出开仓，买入平仓

### 4. 持仓计算
- 自动计算平均成本（Average Cost Basis）
- 支持 FIFO 成本计算方法
- 自动跟踪已实现盈亏
- 实时计算未实现盈亏（需联网获取价格）
- 计算持仓天数和回报率

### 5. 数据存储
- 基于 TinyDB 的本地 JSON 存储
- 交易记录不可变日志（transactions.json）
- 当前持仓快照（holdings.json）
- 已平仓记录（realized.json）
- 账户信息（accounts.json）
- 资金流水记录（cash_flows.json）
- 投资组合快照（snapshots.json）
- 配置文件（config.toml）

### 6. 投资组合快照
- 捕获当前投资组合完整状态
- 包含实时市场价格、未实现盈亏、回报率
- 按账户和持仓分层记录
- 支持历史快照查询和对比
- 自动记录汇率和价格来源
- 支持快照清理（保留最近 N 条）

### 7. 资金流水管理
- 记录账户入金（deposit）和出金（withdrawal）
- 每笔流水独立记录，含时间、金额、货币、备注
- 自动更新账户累计入金/出金总额
- 支持按账户查询流水历史

### 8. 美股期权支持
- 自动识别美股期权代码格式（如 AAPL250117C00150000）
- 期权合约自动应用 100 倍乘数
- 持仓计算和盈亏计算均考虑乘数
- 显示时自动转换为每股价格

## 命令详解

### 初始化系统

```bash
# 使用默认颜色方案（绿涨红跌，西方风格）
ptracker init

# 使用中国风格（红涨绿跌）
ptracker init --color-scheme red_up
ptracker init -c red_up

# 使用西方风格（绿涨红跌）
ptracker init --color-scheme green_up
```

**说明**:
- 首次使用必须运行此命令
- 创建 `~/.ptracker/` 目录和所有必需文件
- 颜色方案可后续通过 `ptracker config color` 修改

### 账户管理

```bash
# 添加账户
ptracker account add <账户名> \
  --type <brokerage|exchange> \
  --desc "账户描述" \
  --currency <USD|HKD|CNY>

# 示例：添加美股账户
ptracker account add ibkr \
  --type brokerage \
  --desc "Interactive Brokers" \
  --currency USD

# 示例：添加港股账户
ptracker account add futu \
  --type brokerage \
  --desc "富途证券" \
  --currency HKD

# 列出所有账户
ptracker account list

# 查询特定账户详情
ptracker account query <账户名>

# 删除账户（需确认，且账户无持仓）
ptracker account delete <账户名>

# 入金（记录存款）
ptracker account deposit <账户名> <金额> --currency <货币>

# 出金（记录取款）
ptracker account withdraw <账户名> <金额> --currency <货币>

# 入金带备注
ptracker account deposit ibkr 10000 --currency USD --note "从银行转账"

# 出金带备注
ptracker account withdraw ibkr 5000 --currency USD --note "转出到银行"


**参数说明**:
- `type`: 账户类型
  - `brokerage`: 券商账户（股票、期货）
  - `exchange`: 交易所账户（加密货币）
- `currency`: 账户基准货币（USD、HKD、CNY 等）

### 交易记录

> ⚠️ **格式要求**: 资产代码必须符合 Yahoo Finance 格式规范（见上方「📋 Yahoo Finance 代码格式规范」章节）。系统会自动验证格式，格式错误会被拒绝录入。

#### 买入开仓（做多）

```bash
ptracker trade add buy <资产代码> <数量> <价格> \
  --currency <货币> \
  --action open \
  --direction long \
  --account <账户名> \
  --fee <手续费> \
  --note "备注"

# 示例：买入美股
ptracker trade add buy AAPL 100 150.0 \
  --currency USD \
  --action open \
  --direction long \
  --account ibkr \
  --fee 1.0 \
  --note "建仓苹果"

# 示例：买入港股
ptracker trade add buy 0700.HK 500 320.5 \
  --currency HKD \
  --action open \
  --direction long \
  --account futu
```

#### 卖出开仓（做空）

```bash
ptracker trade add sell <资产代码> <数量> <价格> \
  --currency <货币> \
  --action open \
  --direction short \
  --account <账户名>

# 示例：做空美股
ptracker trade add sell TSLA 50 200.0 \
  --currency USD \
  --action open \
  --direction short \
  --account ibkr \
  --note "做空特斯拉"
```

#### 卖出平仓（平多头）

```bash
ptracker trade add sell <资产代码> <数量> <价格> \
  --currency <货币> \
  --action close \
  --direction long \
  --account <账户名>

# 示例：卖出平仓
ptracker trade add sell AAPL 100 160.0 \
  --currency USD \
  --action close \
  --direction long \
  --account ibkr \
  --note "止盈平仓"
```

#### 买入平仓（平空头）

```bash
ptracker trade add buy <资产代码> <数量> <价格> \
  --currency <货币> \
  --action close \
  --direction short \
  --account <账户名>

# 示例：买入平空
ptracker trade add buy TSLA 50 180.0 \
  --currency USD \
  --action close \
  --direction short \
  --account ibkr \
  --note "止盈平空"
```

#### 记录分红

```bash
ptracker trade add dividend <资产代码> <分红金额> \
  --currency <货币> \
  --account <账户名> \
  --note "分红说明"

# 示例：记录美股分红
ptracker trade add dividend AAPL 50.0 \
  --currency USD \
  --account ibkr \
  --note "Q1 2026 dividend"
```

**重要说明**:
- 分红命令只需要两个位置参数：资产代码和分红金额
- 不需要输入数量参数（内部自动设为 0）
- 不需要输入价格参数（分红金额会存储在价格字段）
- 分红会自动降低持仓成本

#### 查看交易记录

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
ptracker trade list --type sell
ptracker trade list --type dividend

# 按动作筛选
ptracker trade list --action open
ptracker trade list --action close

# 按方向筛选
ptracker trade list --direction long
ptracker trade list --direction short
```

### 查询持仓

```bash
# 查看所有活跃持仓
ptracker query holdings

# 查看特定账户的持仓
ptracker query holdings --account ibkr

# 查看特定资产的持仓
ptracker query holdings --asset AAPL

# 按投资金额排序
ptracker query holdings --sort total_invested

# 按数量排序
ptracker query holdings --sort quantity

# 转换为特定货币显示（明细和汇总都转换）
ptracker query holdings --currency USD

# 分别控制明细和汇总的货币
ptracker query holdings --detail-currency USD --total-currency CNY

# 明细保持原始货币，汇总转换为 USD
ptracker query holdings --detail-currency mix --total-currency USD
```

**输出字段说明**:
- `Asset`: 资产代码
- `Account`: 账户名称
- `Direction`: 方向（Long/Short）
- `Quantity`: 持仓数量
- `Avg Cost`: 平均成本
- `Total Invested`: 总投资金额
- `Currency`: 货币
- `First Open`: 首次开仓日期
- `Status`: 状态（active/closed）

### 查询投资组合价值

```bash
# 查看总价值（需联网获取实时价格）
ptracker query value

# 按资产分类查看
ptracker query value --breakdown asset

# 按账户分类查看
ptracker query value --breakdown account

# 按货币分类查看
ptracker query value --breakdown currency

# 转换为特定货币显示
ptracker query value --currency USD
```

**说明**:
- 需要网络连接获取实时价格
- 使用 yfinance（美股、港股）和 akshare（A股）
- 自动计算未实现盈亏

### 查询已平仓记录

```bash
# 查看所有已平仓记录
ptracker query realized

# 按账户筛选
ptracker query realized --account ibkr

# 按资产筛选
ptracker query realized --asset AAPL

# 按排序方式
ptracker query realized --sort pnl      # 按盈亏排序
ptracker query realized --sort return   # 按回报率排序
ptracker query realized --sort days     # 按持仓天数排序
ptracker query realized --sort date     # 按日期排序（默认）

# 限制显示数量
ptracker query realized --limit 10

# 货币转换（同 holdings 的三级货币控制）
ptracker query realized --currency USD
ptracker query realized --detail-currency mix --total-currency USD
```

**输出字段说明**:
- `Asset`: 资产代码
- `Account`: 账户名称
- `Direction`: 方向（Long/Short）
- `Total Quantity`: 总交易数量
- `Total Invested`: 总投资金额
- `Total Proceeds`: 总收益金额
- `Realized P&L`: 已实现盈亏
- `Return %`: 回报率
- `Holding Days`: 持仓天数
- `First Open`: 首次开仓日期
- `Last Close`: 最后平仓日期

### 查询盈亏汇总

```bash
# 查看总盈亏（已实现 + 未实现）
ptracker query pnl

# 查看详细分解（按资产）
ptracker query pnl --detail

# 只看已实现盈亏
ptracker query pnl --realized-only

# 只看未实现盈亏
ptracker query pnl --unrealized-only

# 按账户筛选
ptracker query pnl --account ibkr

# 转换为特定货币
ptracker query pnl --currency USD

# 分别控制明细和汇总货币
ptracker query pnl --detail-currency mix --total-currency USD
```

### 配置管理

```bash
# 查看当前配置
ptracker config show

# 修改配置项
ptracker config set <配置路径> <值>

# 示例：修改颜色方案
ptracker config set display.color_scheme red_up

# 示例：修改默认货币
ptracker config set general.default_currency CNY

# 示例：修改成本计算方法
ptracker config set general.cost_basis_method fifo

# 交互式修改颜色方案
ptracker config color
```

### 投资组合快照

```bash
# 捕获当前投资组合快照（自动保存并显示）
ptracker snapshot take

# 捕获但不保存（仅显示）
ptracker snapshot take --no-save

# 捕获但不显示
ptracker snapshot take --no-show

# 查看最近的快照列表
ptracker snapshot list
ptracker snapshot list --limit 20

# 查看最新快照详情
ptracker snapshot show

# 查看指定日期的快照
ptracker snapshot show --date 2026-03-01

# 清理旧快照（保留最近 30 条）
ptracker snapshot prune
ptracker snapshot prune --keep 50
```

**快照包含的信息**:
- 投资组合总市值、总成本、未实现/已实现盈亏
- 总回报率
- 各账户详情（入金、出金、净入金、市值、盈亏）
- 各持仓详情（当前价格、市值、未实现盈亏、回报率）
- 货币分布
- 汇率快照
- 价格来源和时间戳

**配置文件结构** (`~/.ptracker/config.toml`):
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

## 典型工作流程

### 工作流 1: 美股长期投资

```bash
# 1. 添加账户
ptracker account add ibkr --type brokerage --currency USD --desc "盈透证券"

# 2. 首次建仓
ptracker trade add buy AAPL 100 150.0 \
  --currency USD --action open --direction long --account ibkr

# 3. 回调加仓
ptracker trade add buy AAPL 50 145.0 \
  --currency USD --action open --direction long --account ibkr --note "回调加仓"

# 4. 查看持仓（自动计算平均成本）
ptracker query holdings --asset AAPL

# 5. 部分止盈
ptracker trade add sell AAPL 50 170.0 \
  --currency USD --action close --direction long --account ibkr --note "部分止盈"

# 6. 查看已实现盈亏
ptracker query realized --asset AAPL

# 7. 查看剩余持仓
ptracker query holdings --asset AAPL
```

### 工作流 2: 港股短线交易

```bash
# 1. 添加账户
ptracker account add futu --type brokerage --currency HKD --desc "富途证券"

# 2. 建仓
ptracker trade add buy 0700.HK 1000 320.0 \
  --currency HKD --action open --direction long --account futu --note "突破买入"

# 3. 止盈平仓
ptracker trade add sell 0700.HK 1000 335.0 \
  --currency HKD --action close --direction long --account futu --note "达到目标价"

# 4. 查看已平仓记录
ptracker query realized --asset 0700.HK
```

### 工作流 3: 做空交易

```bash
# 1. 卖空开仓
ptracker trade add sell TSLA 100 250.0 \
  --currency USD --action open --direction short --account ibkr --note "高位做空"

# 2. 查看空头持仓
ptracker query holdings --asset TSLA

# 3. 买入平空
ptracker trade add buy TSLA 100 220.0 \
  --currency USD --action close --direction short --account ibkr --note "止盈平空"

# 4. 查看已实现盈亏
ptracker query realized --asset TSLA
```

### 工作流 4: 分红处理

```bash
# 1. 记录分红收入
ptracker trade add dividend AAPL 50.0 \
  --currency USD --account ibkr --note "Q1 2026 dividend"

# 2. 查看持仓（分红会降低平均成本）
ptracker query holdings --asset AAPL

# 3. 查看所有分红记录
ptracker trade list --type dividend
```

### 工作流 5: 多账户管理

```bash
# 1. 查看所有账户
ptracker account list

# 2. 查看各账户持仓
ptracker query holdings --account ibkr
ptracker query holdings --account futu

# 3. 查看总投资组合价值
ptracker query value

# 4. 按账户分类查看价值
ptracker query value --breakdown account

# 5. 查看总盈亏（详细分解）
ptracker query pnl --detail
```

## 资产代码格式

### 港股
- 格式: `<股票代码>.HK`
- 示例: `0700.HK` (腾讯), `9988.HK` (阿里巴巴)

### 美股
- 格式: `<股票代码>`
- 示例: `AAPL` (苹果), `TSLA` (特斯拉), `MSFT` (微软)

### A股
- 格式: `<股票代码>.SS` (上交所) 或 `<股票代码>.SZ` (深交所)
- 示例: `600519.SS` (茅台), `000001.SZ` (平安银行)

### 加密货币
- 格式: `<币种>-USD`
- 示例: `BTC-USD` (比特币), `ETH-USD` (以太坊)

## 数据模型

### Transaction（交易记录）
```python
{
    "id": "tx_xxx",
    "datetime": "2026-03-04T10:00:00",
    "type": "buy|sell|dividend",
    "action": "open|close|income",
    "direction": "long|short",
    "asset": "AAPL",
    "quantity": 100.0,
    "price": 150.0,
    "currency": "USD",
    "fee": 1.0,
    "account": "ibkr",
    "note": "建仓"
}
```

### Holding（持仓）
```python
{
    "asset": "AAPL",
    "account": "ibkr",
    "direction": "long",
    "quantity": 100.0,
    "avg_cost": 150.5,
    "total_invested": 15050.0,
    "currency": "USD",
    "first_open_date": "2026-03-04",
    "last_updated": "2026-03-04",
    "note": "建仓",
    "status": "active"
}
```

### RealizedPosition（已平仓）
```python
{
    "id": "real_xxx",
    "asset": "AAPL",
    "account": "ibkr",
    "direction": "long",
    "first_open_date": "2026-01-01",
    "last_close_date": "2026-03-04",
    "holding_days": 63,
    "total_quantity": 100.0,
    "total_invested": 15000.0,
    "total_proceeds": 16000.0,
    "total_fees": 2.0,
    "realized_pnl": 1000.0,
    "return_pct": 6.67,
    "currency": "USD",
    "note": "止盈",
    "status": "closed"
}
```

## 核心业务逻辑

### 1. 持仓计算（Position Calculator）
- **开仓**: 创建新持仓或增加现有持仓
- **平仓**: 减少或关闭持仓，生成已实现盈亏记录
- **平均成本**: 加权平均成本计算
- **部分平仓**: 按比例减少持仓，保持平均成本不变
- **全部平仓**: 关闭持仓，记录到 realized.json

### 2. 盈亏计算（P&L Calculator）
- **已实现盈亏**: 平仓时的实际盈亏
  - 做多: `(卖出价格 - 平均成本) × 数量 - 手续费`
  - 做空: `(平均成本 - 买入价格) × 数量 - 手续费`
- **未实现盈亏**: 当前持仓的浮动盈亏
  - 做多: `(当前价格 - 平均成本) × 数量`
  - 做空: `(平均成本 - 当前价格) × 数量`
- **回报率**: `盈亏 / 总投资 × 100%`

### 3. 价格服务（Price Service）
- **yfinance**: 美股、港股、加密货币
- **akshare**: A股、期货
- **缓存机制**: 60秒缓存，减少 API 调用
- **自动重试**: 失败时自动切换数据源

### 4. 数据验证（Validation Service）
- 交易数量符号验证
- 账户存在性验证
- 资产代码格式验证
- 账户删除前检查持仓

## 技术栈

- **CLI 框架**: Typer
- **终端美化**: Rich
- **数据库**: TinyDB (JSON)
- **数据验证**: Pydantic
- **价格数据**: yfinance, akshare
- **日期处理**: python-dateutil
- **配置文件**: TOML
- **并发控制**: filelock

## 常见问题

### Q1: 如何修改颜色方案？
```bash
# 方式 1: 交互式修改
ptracker config color

# 方式 2: 直接设置
ptracker config set display.color_scheme red_up
```

### Q2: 如何备份数据？
```bash
# 备份整个数据目录
cp -r ~/.ptracker ~/.ptracker.backup.$(date +%Y%m%d)

# 或只备份交易记录
cp ~/.ptracker/transactions.json ~/backup/
```

### Q3: 如何查看特定时间段的交易？
```bash
ptracker trade list --from 2026-01-01 --to 2026-03-31
```

### Q4: 如何删除错误的交易记录？
目前不支持删除交易记录（不可变日志设计）。如需修正，可以：
1. 添加反向交易来抵消
2. 或直接编辑 `~/.ptracker/transactions.json`（需谨慎）

### Q5: 价格查询失败怎么办？
```bash
# 检查网络连接
ping finance.yahoo.com

# 手动测试价格查询
ptracker price AAPL

# 查看详细错误信息
ptracker query value --verbose
```

### Q6: 如何处理货币转换？
系统会自动使用实时汇率进行货币转换（通过 yfinance）。可以使用 `--currency` 参数指定显示货币：
```bash
ptracker query holdings --currency USD
ptracker query value --currency CNY
```

## 开发相关

### 项目结构
```
ptracker/
├── cli/              # CLI 命令
│   ├── main.py       # 主入口
│   ├── account.py    # 账户管理
│   ├── trade.py      # 交易记录
│   ├── query.py      # 查询命令
│   ├── config.py     # 配置管理
│   └── init.py       # 初始化
├── models/           # 数据模型
│   ├── transaction.py
│   ├── holding.py
│   ├── realized_position.py
│   └── account.py
├── repositories/     # 数据访问层
│   ├── base.py
│   ├── transaction.py
│   ├── holding.py
│   └── realized.py
├── services/         # 业务逻辑
│   ├── position_calculator.py
│   ├── pnl_calculator.py
│   ├── price_service.py
│   └── validation.py
└── utils/            # 工具函数
    ├── color_helper.py
    └── id_generator.py
```

### 运行测试
```bash
# 运行所有测试
python run_tests.py

# 运行特定测试
python -m pytest tests/test_repositories.py

# 运行安装测试
./test_install.sh
```

### 开发模式安装
```bash
# 激活环境
conda activate quantdev

# 可编辑模式安装
pip install -e .

# 修改代码后无需重新安装
```

## 版本信息

- **当前版本**: 0.1.4
- **Python 要求**: 3.10+
- **许可证**: MIT

## 使用建议

1. **首次使用**: 先运行 `ptracker init` 初始化系统
2. **添加账户**: 为每个券商/交易所创建独立账户
3. **记录交易**: 及时记录每笔交易，保持数据准确
4. **定期查询**: 定期查看持仓和盈亏情况
5. **数据备份**: 定期备份 `~/.ptracker/` 目录
6. **颜色方案**: 根据个人习惯选择合适的颜色方案
7. **货币管理**: 为每个账户设置正确的基准货币
8. **备注信息**: 为重要交易添加备注，便于后续查询

## 注意事项

1. 交易记录是不可变日志，删除需谨慎
2. 价格查询需要网络连接
3. 分红会自动降低持仓成本
4. 做空交易的盈亏计算与做多相反
5. 部分平仓会按比例减少持仓
6. 账户删除前必须清空所有持仓
7. 数据文件使用 JSON 格式，可手动编辑（需谨慎）
8. 建议定期备份数据文件
