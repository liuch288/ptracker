"""Tests for data models."""

from datetime import datetime
from ptracker.models import Transaction, Holding, Account, RealizedPosition, PriceQuote


def test_transaction_model():
    """Test Transaction model."""
    # Valid long buy transaction
    txn = Transaction(
        id="txn_123_ab",
        datetime=datetime.now(),
        type="buy",
        action="open",
        direction="long",
        asset="AAPL",
        quantity=100.0,  # Positive for buy+open+long
        price=150.0,
        currency="USD",
        fee=1.0,
        account="mybroker",
        note="Test transaction"
    )
    assert txn.quantity == 100.0
    print(f"✓ Valid long buy transaction: {txn.asset} x {txn.quantity}")
    
    # Valid short sell transaction
    txn2 = Transaction(
        id="txn_124_cd",
        datetime=datetime.now(),
        type="sell",
        action="open",
        direction="short",
        asset="TSLA",
        quantity=-50.0,  # Negative for sell+open+short
        price=200.0,
        currency="USD",
        account="mybroker"
    )
    assert txn2.quantity == -50.0
    print(f"✓ Valid short sell transaction: {txn2.asset} x {txn2.quantity}")
    
    # Test validation error
    try:
        invalid_txn = Transaction(
            id="txn_125_ef",
            datetime=datetime.now(),
            type="buy",
            action="open",
            direction="long",
            asset="AAPL",
            quantity=-100.0,  # Wrong sign!
            price=150.0,
            currency="USD",
            account="mybroker"
        )
        print("✗ Should have raised validation error")
    except ValueError as e:
        print(f"✓ Validation error caught: {str(e)[:50]}...")


def test_holding_model():
    """Test Holding model."""
    holding = Holding(
        asset="0700.HK",
        account="ibkr",
        direction="long",
        quantity=800.0,
        avg_cost=310.5,
        total_invested=248400.0,
        currency="HKD",
        first_open_date="2026-01-10",
        last_updated="2026-02-25",
        note="Test holding"
    )
    assert holding.status == "active"
    assert holding.quantity == 800.0
    print(f"✓ Holding created: {holding.asset} x {holding.quantity} @ {holding.avg_cost}")


def test_account_model():
    """Test Account model."""
    account = Account(
        id="acct_123_ab",
        name="mybroker",
        type="brokerage",
        description="My test account",
        currency="USD",
        created_at=datetime.now()
    )
    assert account.name == "mybroker"
    assert account.type == "brokerage"
    print(f"✓ Account created: {account.name} ({account.type})")


def test_realized_position_model():
    """Test RealizedPosition model."""
    realized = RealizedPosition(
        id="real_123_ab",
        asset="AAPL",
        account="mybroker",
        direction="long",
        first_open_date="2025-01-01",
        last_close_date="2026-01-01",
        holding_days=365,
        total_quantity=100.0,
        total_invested=10000.0,
        total_proceeds=12000.0,
        total_fees=20.0,
        realized_pnl=1980.0,
        return_pct=19.8,
        note="Test realized position"
    )
    assert realized.status == "closed"
    assert realized.realized_pnl == 1980.0
    print(f"✓ Realized position: {realized.asset} P&L={realized.realized_pnl} ({realized.return_pct}%)")


def test_price_quote_model():
    """Test PriceQuote model."""
    quote = PriceQuote(
        asset="AAPL",
        price=150.25,
        currency="USD",
        timestamp=datetime.now()
    )
    assert quote.price == 150.25
    print(f"✓ Price quote: {quote.asset} = {quote.price} {quote.currency}")


if __name__ == '__main__':
    test_transaction_model()
    test_holding_model()
    test_account_model()
    test_realized_position_model()
    test_price_quote_model()
    print("\n✅ All model tests passed!")
