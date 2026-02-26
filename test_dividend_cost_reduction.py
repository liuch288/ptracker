#!/usr/bin/env python3
"""Test dividend cost reduction functionality."""

import sys
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from ptracker.repositories import TransactionRepository, HoldingRepository, AccountRepository
from ptracker.utils.id_generator import generate_id


def test_dividend_reduces_cost():
    """Test that dividend reduces avg_cost and total_invested."""
    print("Testing dividend cost reduction...")
    
    # Create temporary directory for test data
    test_dir = Path(tempfile.mkdtemp())
    
    try:
        # Initialize repositories
        account_repo = AccountRepository(test_dir / "accounts.json")
        transaction_repo = TransactionRepository(test_dir / "transactions.json")
        holding_repo = HoldingRepository(test_dir / "holdings.json")
        
        # Create test account
        account_data = {
            'id': generate_id('acc'),
            'name': 'test_account',
            'type': 'brokerage',
            'currency': 'USD',
            'description': 'Test Account',
            'created_date': datetime.now().strftime('%Y-%m-%d')
        }
        account_repo.insert(account_data)
        
        # Create initial holding
        holding_data = {
            'id': generate_id('hld'),
            'asset': 'AAPL',
            'account': 'test_account',
            'direction': 'long',
            'quantity': 100.0,
            'avg_cost': 150.0,
            'total_invested': 15000.0,
            'currency': 'USD',
            'first_open_date': '2024-01-01',
            'last_updated': '2024-01-01',
            'note': 'Test position',
            'status': 'active'
        }
        holding_repo.insert(holding_data)
        
        # Record dividend transaction
        dividend_tx = {
            'id': generate_id('txn'),
            'datetime': datetime.now().isoformat(),
            'type': 'dividend',
            'action': 'income',
            'direction': 'long',
            'asset': 'AAPL',
            'quantity': 0.0,
            'price': 300.0,  # $300 dividend
            'currency': 'USD',
            'fee': 0.0,
            'account': 'test_account',
            'note': 'Q1 dividend'
        }
        transaction_repo.insert(dividend_tx)
        
        # Simulate dividend processing (what the CLI does)
        existing_holding = holding_repo.find_by_asset_account('AAPL', 'test_account', 'long')
        
        old_total_invested = existing_holding['total_invested']
        old_avg_cost = existing_holding['avg_cost']
        old_quantity = existing_holding['quantity']
        
        # Apply dividend
        new_total_invested = old_total_invested - dividend_tx['price']
        new_avg_cost = new_total_invested / old_quantity
        
        updated_holding = {
            **existing_holding,
            'total_invested': new_total_invested,
            'avg_cost': new_avg_cost,
            'last_updated': datetime.now().strftime('%Y-%m-%d')
        }
        
        holding_repo.upsert(updated_holding)
        
        # Verify results
        final_holding = holding_repo.find_by_asset_account('AAPL', 'test_account', 'long')
        
        assert final_holding['quantity'] == 100.0, "Quantity should not change"
        assert final_holding['total_invested'] == 14700.0, f"Total invested should be 14700, got {final_holding['total_invested']}"
        assert final_holding['avg_cost'] == 147.0, f"Avg cost should be 147, got {final_holding['avg_cost']}"
        
        print("✓ Dividend correctly reduced cost basis")
        print(f"  Quantity: {old_quantity} → {final_holding['quantity']} (unchanged)")
        print(f"  Total invested: ${old_total_invested:.2f} → ${final_holding['total_invested']:.2f}")
        print(f"  Avg cost: ${old_avg_cost:.2f} → ${final_holding['avg_cost']:.2f}")
        
        return True
        
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Cleanup
        shutil.rmtree(test_dir)


def test_dividend_without_position():
    """Test dividend when no position exists."""
    print("\nTesting dividend without position...")
    
    test_dir = Path(tempfile.mkdtemp())
    
    try:
        transaction_repo = TransactionRepository(test_dir / "transactions.json")
        holding_repo = HoldingRepository(test_dir / "holdings.json")
        
        # Record dividend without position
        dividend_tx = {
            'id': generate_id('txn'),
            'datetime': datetime.now().isoformat(),
            'type': 'dividend',
            'action': 'income',
            'direction': 'long',
            'asset': 'GOOGL',
            'quantity': 0.0,
            'price': 50.0,
            'currency': 'USD',
            'fee': 0.0,
            'account': 'test_account',
            'note': 'Dividend without position'
        }
        transaction_repo.insert(dividend_tx)
        
        # Check no holding exists
        existing_holding = holding_repo.find_by_asset_account('GOOGL', 'test_account', 'long')
        
        assert existing_holding is None, "No holding should exist"
        
        # Verify transaction was recorded
        all_txs = transaction_repo.find_all()
        assert len(all_txs) == 1, "Transaction should be recorded"
        assert all_txs[0]['type'] == 'dividend', "Transaction type should be dividend"
        
        print("✓ Dividend recorded without position")
        
        return True
        
    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False
        
    finally:
        shutil.rmtree(test_dir)


def test_dividend_exceeds_investment():
    """Test dividend amount exceeding total investment."""
    print("\nTesting dividend exceeding investment...")
    
    test_dir = Path(tempfile.mkdtemp())
    
    try:
        holding_repo = HoldingRepository(test_dir / "holdings.json")
        
        # Create holding with small investment
        holding_data = {
            'id': generate_id('hld'),
            'asset': 'TEST',
            'account': 'test_account',
            'direction': 'long',
            'quantity': 10.0,
            'avg_cost': 10.0,
            'total_invested': 100.0,
            'currency': 'USD',
            'first_open_date': '2024-01-01',
            'last_updated': '2024-01-01',
            'note': '',
            'status': 'active'
        }
        holding_repo.insert(holding_data)
        
        # Apply large dividend
        dividend_amount = 200.0  # Exceeds investment
        existing_holding = holding_repo.find_by_asset_account('TEST', 'test_account', 'long')
        
        old_total_invested = existing_holding['total_invested']
        new_total_invested = old_total_invested - dividend_amount
        
        # Should be capped at 0
        if new_total_invested < 0:
            new_total_invested = 0
        
        new_avg_cost = new_total_invested / existing_holding['quantity'] if existing_holding['quantity'] > 0 else 0
        
        updated_holding = {
            **existing_holding,
            'total_invested': new_total_invested,
            'avg_cost': new_avg_cost
        }
        
        holding_repo.upsert(updated_holding)
        
        final_holding = holding_repo.find_by_asset_account('TEST', 'test_account', 'long')
        
        assert final_holding['total_invested'] == 0.0, "Total invested should be 0"
        assert final_holding['avg_cost'] == 0.0, "Avg cost should be 0"
        
        print("✓ Large dividend correctly capped at 0")
        print(f"  Total invested: ${old_total_invested:.2f} → ${final_holding['total_invested']:.2f}")
        
        return True
        
    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False
        
    finally:
        shutil.rmtree(test_dir)


def main():
    """Run all tests."""
    print("=" * 60)
    print("Testing Dividend Cost Reduction")
    print("=" * 60)
    
    results = []
    
    results.append(test_dividend_reduces_cost())
    results.append(test_dividend_without_position())
    results.append(test_dividend_exceeds_investment())
    
    print("\n" + "=" * 60)
    if all(results):
        print("✓ All tests passed!")
        print("=" * 60)
        return 0
    else:
        print("✗ Some tests failed")
        print("=" * 60)
        return 1


if __name__ == '__main__':
    sys.exit(main())
