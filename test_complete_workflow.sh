#!/bin/bash
# Complete workflow test for ptracker

set -e  # Exit on error

echo "🧪 Complete Workflow Test"
echo "=========================================="
echo ""

# Step 1: Add accounts
echo "📝 Step 1: Adding accounts"
echo "------------------------------------------"
ptracker account add us_broker --type brokerage --desc "US Market" --currency USD
ptracker account add hk_broker --type brokerage --desc "HK Market" --currency HKD
ptracker account add cn_broker --type brokerage --desc "CN Market" --currency CNY
echo ""

# Step 2: View accounts
echo "📋 Step 2: Viewing accounts"
echo "------------------------------------------"
ptracker account list
echo ""

# Step 3: Add US trades
echo "💰 Step 3: Adding US market trades"
echo "------------------------------------------"
ptracker trade add buy AAPL 100 150.0 --currency USD --account us_broker --action open --direction long --note "Apple"
ptracker trade add buy MSFT 50 300.0 --currency USD --account us_broker --action open --direction long --note "Microsoft"
echo ""

# Step 4: Add HK trades
echo "💰 Step 4: Adding HK market trades"
echo "------------------------------------------"
ptracker trade add buy 0700.HK 500 320.0 --currency HKD --account hk_broker --action open --direction long --note "Tencent"
ptracker trade add buy 9988.HK 200 80.0 --currency HKD --account hk_broker --action open --direction long --note "Alibaba"
echo ""

# Step 5: Add CN trades
echo "💰 Step 5: Adding CN market trades"
echo "------------------------------------------"
ptracker trade add buy 600000.SS 1000 10.0 --currency CNY --account cn_broker --action open --direction long --note "Pudong Bank"
echo ""

# Step 6: View all trades
echo "📊 Step 6: Viewing all trades"
echo "------------------------------------------"
ptracker trade list
echo ""

# Step 7: View holdings
echo "📈 Step 7: Viewing current holdings"
echo "------------------------------------------"
ptracker query holdings
echo ""

# Step 8: Close some positions
echo "💸 Step 8: Closing some positions"
echo "------------------------------------------"
echo "Closing 50 shares of AAPL..."
ptracker trade add sell AAPL 50 160.0 --currency USD --account us_broker --action close --direction long --note "Partial close"
echo ""
echo "Closing all Tencent..."
ptracker trade add sell 0700.HK 500 350.0 --currency HKD --account hk_broker --action close --direction long --note "Full close"
echo ""

# Step 9: View holdings after closing
echo "📈 Step 9: Viewing holdings after closing"
echo "------------------------------------------"
ptracker query holdings
echo ""

# Step 10: View realized positions
echo "💵 Step 10: Viewing realized positions"
echo "------------------------------------------"
ptracker query realized
echo ""

# Step 11: View holdings with closed positions
echo "📊 Step 11: Viewing holdings with closed positions"
echo "------------------------------------------"
ptracker query holdings --include-closed
echo ""

# Step 12: View portfolio value
echo "💎 Step 12: Viewing portfolio value"
echo "------------------------------------------"
ptracker query value
echo ""

# Step 13: View portfolio value in USD
echo "💎 Step 13: Viewing portfolio value in USD"
echo "------------------------------------------"
ptracker query value --currency USD
echo ""

# Step 14: View portfolio value by account
echo "💎 Step 14: Viewing portfolio value by account (USD)"
echo "------------------------------------------"
ptracker query value --currency USD --breakdown account
echo ""

echo "=========================================="
echo "✅ Complete workflow test finished!"
echo "=========================================="
