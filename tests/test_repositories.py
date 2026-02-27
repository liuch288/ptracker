"""Tests for repositories."""

import tempfile
from pathlib import Path
from datetime import datetime
from ptracker.repositories import (
    TransactionRepository,
    HoldingRepository,
    AccountRepository,
    RealizedRepository
)


def test_transaction_repository():
    """Test TransactionRepository."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "transactions.json"
        repo = TransactionRepository(db_path)
        
        # Insert transaction
        txn_data = {
            'id': 'txn_123_ab',
            'datetime': datetime.now().isoformat(),
            'type': 'buy',
            'action': 'open',
            'direction': 'long',
            'asset': 'AAPL',
            'quantity': 100.0,
            'price': 150.0,
            'currency': 'USD',
            'fee': 1.0,
            'account': 'mybroker',
            'note': 'Test'
        }
        txn_id = repo.insert(txn_data)
        assert txn_id == 'txn_123_ab'
        print(f"✓ Inserted transaction: {txn_id}")
        
        # Find by ID
        found = repo.find_by_id('txn_123_ab')
        assert found is not None
        assert found['asset'] == 'AAPL'
        print(f"✓ Found transaction by ID: {found['asset']}")
        
        # Find all
        all_txns = repo.find_all()
        assert len(all_txns) == 1
        print(f"✓ Found all transactions: {len(all_txns)}")
        
        # Find by asset/account/direction
        filtered = repo.find_by_asset_account('AAPL', 'mybroker', 'long')
        assert len(filtered) == 1
        print(f"✓ Found by asset/account/direction: {len(filtered)}")
        
        # Update
        success = repo.update('txn_123_ab', {'note': 'Updated'})
        assert success
        updated = repo.find_by_id('txn_123_ab')
        assert updated['note'] == 'Updated'
        print("✓ Updated transaction")
        
        # Delete
        success = repo.delete('txn_123_ab')
        assert success
        deleted = repo.find_by_id('txn_123_ab')
        assert deleted is None
        print("✓ Deleted transaction")


def test_holding_repository():
    """Test HoldingRepository."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "holdings.json"
        repo = HoldingRepository(db_path)
        
        # Upsert (insert)
        holding_data = {
            'asset': 'AAPL',
            'account': 'mybroker',
            'direction': 'long',
            'quantity': 100.0,
            'avg_cost': 150.0,
            'total_invested': 15000.0,
            'currency': 'USD',
            'first_open_date': '2026-01-01',
            'last_updated': '2026-01-01',
            'note': 'Test',
            'status': 'active'
        }
        repo.upsert(holding_data)
        print("✓ Upserted holding (insert)")
        
        # Find by asset/account/direction
        found = repo.find_by_asset_account('AAPL', 'mybroker', 'long')
        assert found is not None
        assert found['quantity'] == 100.0
        print(f"✓ Found holding: {found['asset']} x {found['quantity']}")
        
        # Upsert (update)
        holding_data['quantity'] = 200.0
        holding_data['last_updated'] = '2026-01-02'
        repo.upsert(holding_data)
        
        updated = repo.find_by_asset_account('AAPL', 'mybroker', 'long')
        assert updated['quantity'] == 200.0
        print(f"✓ Upserted holding (update): quantity = {updated['quantity']}")


def test_account_repository():
    """Test AccountRepository."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "accounts.json"
        repo = AccountRepository(db_path)
        
        # Insert account
        account_data = {
            'id': 'acct_123_ab',
            'name': 'mybroker',
            'type': 'brokerage',
            'description': 'Test account',
            'currency': 'USD',
            'created_at': datetime.now().isoformat(),
            'total_deposit': 0.0,
            'total_withdrawal': 0.0
        }
        acct_id = repo.insert(account_data)
        print(f"✓ Inserted account: {acct_id}")
        
        # Find by name
        found = repo.find_by_name('mybroker')
        assert found is not None
        assert found['type'] == 'brokerage'
        print(f"✓ Found account by name: {found['name']}")
        
        # Test deposit
        repo.update_deposit('mybroker', 1000.0)
        found = repo.find_by_name('mybroker')
        assert found['total_deposit'] == 1000.0
        print(f"✓ Updated deposit: {found['total_deposit']}")
        
        # Test withdrawal
        repo.update_withdrawal('mybroker', 500.0)
        found = repo.find_by_name('mybroker')
        assert found['total_withdrawal'] == 500.0
        print(f"✓ Updated withdrawal: {found['total_withdrawal']}")


def test_realized_repository():
    """Test RealizedRepository."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "realized.json"
        repo = RealizedRepository(db_path)
        
        # Insert realized position
        realized_data = {
            'id': 'real_123_ab',
            'asset': 'AAPL',
            'account': 'mybroker',
            'direction': 'long',
            'first_open_date': '2025-01-01',
            'last_close_date': '2026-01-01',
            'holding_days': 365,
            'total_quantity': 100.0,
            'total_invested': 10000.0,
            'total_proceeds': 12000.0,
            'total_fees': 20.0,
            'realized_pnl': 1980.0,
            'return_pct': 19.8,
            'note': 'Test',
            'status': 'closed'
        }
        real_id = repo.insert(realized_data)
        print(f"✓ Inserted realized position: {real_id}")
        
        # Find by date range
        found = repo.find_by_date_range('2025-01-01', '2026-12-31')
        assert len(found) == 1
        print(f"✓ Found by date range: {len(found)}")


if __name__ == '__main__':
    test_transaction_repository()
    print()
    test_holding_repository()
    print()
    test_account_repository()
    print()
    test_realized_repository()
    print("\n✅ All repository tests passed!")
