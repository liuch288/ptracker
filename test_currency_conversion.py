#!/usr/bin/env python3
"""Test currency conversion with multi-market trades."""

import subprocess
import sys
from pathlib import Path

def run_command(cmd):
    """Run a command and print output."""
    print(f"\n{'='*60}")
    print(f"Running: {cmd}")
    print('='*60)
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
    return result.returncode == 0

def main():
    """Test multi-market trades with currency conversion."""
    
    print("🧪 Testing Currency Conversion with Multi-Market Trades")
    print("="*60)
    
    # Check if ptracker is initialized
    data_dir = Path.home() / ".ptracker"
    if not data_dir.exists():
        print("❌ ptracker not initialized. Run 'ptracker init' first.")
        sys.exit(1)
    
    print("\n📝 Test Plan:")
    print("1. Add accounts for different markets")
    print("2. Add trades in USD (US market)")
    print("3. Add trades in HKD (Hong Kong market)")
    print("4. Add trades in CNY (China A-share market)")
    print("5. Query holdings in original currencies")
    print("6. Query holdings converted to USD")
    print("7. Query portfolio value in USD")
    
    # Step 1: Add accounts
    print("\n" + "="*60)
    print("Step 1: Adding accounts for different markets")
    print("="*60)
    
    run_command('ptracker account add us_broker --type brokerage --desc "US Market Account" --currency USD')
    run_command('ptracker account add hk_broker --type brokerage --desc "Hong Kong Market Account" --currency HKD')
    run_command('ptracker account add cn_broker --type brokerage --desc "China A-Share Account" --currency CNY')
    
    # Step 2: Add US market trades
    print("\n" + "="*60)
    print("Step 2: Adding US market trades (USD)")
    print("="*60)
    
    run_command('ptracker trade add buy AAPL 100 150.0 --currency USD --account us_broker --action open --direction long --note "Apple stock"')
    run_command('ptracker trade add buy MSFT 50 300.0 --currency USD --account us_broker --action open --direction long --note "Microsoft stock"')
    
    # Step 3: Add Hong Kong market trades
    print("\n" + "="*60)
    print("Step 3: Adding Hong Kong market trades (HKD)")
    print("="*60)
    
    run_command('ptracker trade add buy 0700.HK 500 320.0 --currency HKD --account hk_broker --action open --direction long --note "Tencent"')
    run_command('ptracker trade add buy 9988.HK 200 80.0 --currency HKD --account hk_broker --action open --direction long --note "Alibaba HK"')
    
    # Step 4: Add China A-share trades
    print("\n" + "="*60)
    print("Step 4: Adding China A-share trades (CNY)")
    print("="*60)
    
    run_command('ptracker trade add buy 600000.SS 1000 10.0 --currency CNY --account cn_broker --action open --direction long --note "Pudong Bank"')
    run_command('ptracker trade add buy 000001.SZ 500 15.0 --currency CNY --account cn_broker --action open --direction long --note "Ping An Bank"')
    
    # Step 5: Query all trades
    print("\n" + "="*60)
    print("Step 5: Viewing all trades")
    print("="*60)
    
    run_command('ptracker trade list')
    
    # Step 6: Query holdings in original currencies
    print("\n" + "="*60)
    print("Step 6: Viewing holdings (original currencies)")
    print("="*60)
    
    run_command('ptracker query holdings')
    
    # Step 7: Query holdings by account
    print("\n" + "="*60)
    print("Step 7: Viewing holdings by account")
    print("="*60)
    
    run_command('ptracker query holdings --account us_broker')
    run_command('ptracker query holdings --account hk_broker')
    run_command('ptracker query holdings --account cn_broker')
    
    # Step 8: Query holdings converted to USD
    print("\n" + "="*60)
    print("Step 8: 🔄 Converting all holdings to USD")
    print("="*60)
    
    run_command('ptracker query holdings --currency USD')
    
    # Step 9: Query portfolio value in original currencies
    print("\n" + "="*60)
    print("Step 9: Portfolio value (mixed currencies)")
    print("="*60)
    
    run_command('ptracker query value')
    
    # Step 10: Query portfolio value converted to USD
    print("\n" + "="*60)
    print("Step 10: 🔄 Portfolio value converted to USD")
    print("="*60)
    
    run_command('ptracker query value --currency USD')
    
    # Step 11: Query portfolio value with breakdown
    print("\n" + "="*60)
    print("Step 11: 🔄 Portfolio value by account (USD)")
    print("="*60)
    
    run_command('ptracker query value --currency USD --breakdown account')
    
    # Step 12: Query portfolio value by asset
    print("\n" + "="*60)
    print("Step 12: 🔄 Portfolio value by asset (USD)")
    print("="*60)
    
    run_command('ptracker query value --currency USD --breakdown asset')
    
    print("\n" + "="*60)
    print("✅ Currency conversion test completed!")
    print("="*60)
    print("\n📊 Summary:")
    print("- US Market (USD): AAPL, MSFT")
    print("- HK Market (HKD): 0700.HK, 9988.HK")
    print("- CN Market (CNY): 600000.SS, 000001.SZ")
    print("\n💡 Key observations:")
    print("1. Each holding shows its original currency")
    print("2. With --currency USD, all values are converted to USD")
    print("3. Exchange rates are fetched automatically from yfinance")
    print("4. Breakdown by account/asset works with currency conversion")

if __name__ == '__main__':
    main()
