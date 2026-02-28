---
name: ptracker
description: Use when the user wants to track investment portfolio, manage brokerage accounts, record trades/dividends, or query holdings/P&L. Works with ptracker CLI (conda environment: quantdev).
---

# ptracker - Portfolio Tracking CLI

Personal investment portfolio tracking tool for managing diverse portfolios across multiple markets.

## Environment

- **Conda env**: `quantdev`
- **Run command**: `conda run -n quantdev ptracker <command>`
- **Project path**: `~/dev/ptracker`

## Commands

### Account Management
```bash
ptracker account list                      # List all accounts
ptracker account add --name <name> --broker <broker>  # Add new account
ptracker account query <account-id>        # Query account details
ptracker account deposit <account-id> --amount <amount> --currency <HKD|USD|CNY>
ptracker account withdraw <account-id> --amount <amount>
```

### Trade Management
```bash
ptracker trade add --account <account-id> --symbol <symbol> --quantity <qty> --price <price> --type <buy|sell> --date <YYYY-MM-DD>
ptracker trade add --account <account-id> --symbol <symbol> --dividend --amount <amount> --date <YYYY-MM-DD>  # Dividend
ptracker trade list --account <account-id>
```

### Query
```bash
ptracker query holdings                    # Current holdings
ptracker query holdings --account <account-id>
ptracker query value                      # Total portfolio value
ptracker query realized                   # Closed positions
ptracker query pnl                        # Realized + unrealized P&L
```

## Workflows

### Adding a New Trade
1. List accounts to find the account ID: `ptracker account list`
2. Add trade: `ptracker trade add --account <id> --symbol 00700 --quantity 100 --price 350 --type buy --date 2026-02-28`

### Checking Portfolio
1. Query holdings: `ptracker query holdings`
2. Query value: `ptracker query value`
3. Query P&L: `ptracker query pnl`

### Recording Dividend
1. Find account ID: `ptracker account list`
2. Add dividend: `ptracker trade add --account <id> --symbol 00700 --dividend --amount 500 --date 2026-02-28`

## Notes

- Symbol format: HK stocks (00700), US stocks (AAPL), A-shares (600519), crypto (BTC)
- Currency: HKD (default for HK), USD (default for US), CNY (for A-shares)
- Dates: YYYY-MM-DD format
