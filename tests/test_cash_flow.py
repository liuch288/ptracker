"""Test cash flow functionality."""

import tempfile
from pathlib import Path
from datetime import datetime
from ptracker.repositories import CashFlowRepository
from ptracker.models.cash_flow import CashFlow


def test_cash_flow_model():
    """Test CashFlow model."""
    cash_flow = CashFlow(
        id="cf_123_ab",
        datetime=datetime.now(),
        type="deposit",
        account="mybroker",
        amount=1000.0,
        currency="USD",
        note="Initial deposit"
    )
    assert cash_flow.type == "deposit"
    assert cash_flow.amount == 1000.0
    assert cash_flow.note == "Initial deposit"
    print(f"✓ CashFlow created: {cash_flow.type} {cash_flow.amount}")


def test_cash_flow_repository():
    """Test CashFlowRepository."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "cash_flows.json"
        repo = CashFlowRepository(db_path)
        
        # Insert deposit
        deposit_data = {
            'id': 'cf_123_ab',
            'datetime': datetime.now().isoformat(),
            'type': 'deposit',
            'account': 'mybroker',
            'amount': 1000.0,
            'currency': 'USD',
            'note': 'Initial deposit'
        }
        repo.insert(deposit_data)
        print(f"✓ Inserted deposit")
        
        # Insert withdrawal
        withdrawal_data = {
            'id': 'cf_456_cd',
            'datetime': datetime.now().isoformat(),
            'type': 'withdrawal',
            'account': 'mybroker',
            'amount': 500.0,
            'currency': 'USD',
            'note': 'Partial withdrawal'
        }
        repo.insert(withdrawal_data)
        print(f"✓ Inserted withdrawal")
        
        # Find by account
        flows = repo.find_by_account('mybroker')
        assert len(flows) == 2
        assert flows[0]['type'] in ['deposit', 'withdrawal']
        print(f"✓ Found {len(flows)} cash flows for account")


if __name__ == "__main__":
    test_cash_flow_model()
    test_cash_flow_repository()
    print("\n✓ All cash flow tests passed!")
