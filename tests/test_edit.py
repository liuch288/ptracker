"""Tests for edit command functionality."""

import tempfile
from pathlib import Path
from unittest.mock import patch
from datetime import datetime

from ptracker.repositories import (
    TransactionRepository,
    HoldingRepository,
    AccountRepository,
    RealizedRepository,
)
from ptracker.cli.edit import parse_field_args, validate_and_convert_field


# ── parse_field_args ──────────────────────────────────────────────

def test_parse_field_args_basic():
    result = parse_field_args(["price=100.5", "fee=5.0"])
    assert result == {"price": "100.5", "fee": "5.0"}
    print("✓ parse_field_args: basic key=value")


def test_parse_field_args_value_with_equals():
    result = parse_field_args(["note=a=b"])
    assert result == {"note": "a=b"}
    print("✓ parse_field_args: value containing '='")


def test_parse_field_args_invalid_format():
    try:
        parse_field_args(["bad_input"])
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "Invalid field format" in str(e)
    print("✓ parse_field_args: rejects missing '='")


def test_parse_field_args_empty_field_name():
    try:
        parse_field_args(["=value"])
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "Field name cannot be empty" in str(e)
    print("✓ parse_field_args: rejects empty field name")


# ── validate_and_convert_field ────────────────────────────────────

def test_validate_trans_price():
    val, err = validate_and_convert_field("trans", "price", "150.5", {})
    assert val == 150.5 and err is None
    print("✓ validate: trans price converts to float")


def test_validate_trans_price_invalid():
    val, err = validate_and_convert_field("trans", "price", "abc", {})
    assert val is None and "Invalid price" in err
    print("✓ validate: trans price rejects non-number")


def test_validate_trans_fee():
    val, err = validate_and_convert_field("trans", "fee", "3.5", {})
    assert val == 3.5 and err is None
    print("✓ validate: trans fee converts to float")


def test_validate_trans_fee_invalid():
    val, err = validate_and_convert_field("trans", "fee", "xyz", {})
    assert val is None and "Invalid fee" in err
    print("✓ validate: trans fee rejects non-number")


def test_validate_trans_note():
    val, err = validate_and_convert_field("trans", "note", "hello", {})
    assert val == "hello" and err is None
    print("✓ validate: trans note passes through")


def test_validate_holding_status_valid():
    val, err = validate_and_convert_field("holding", "status", "active", {})
    assert val == "active" and err is None
    val2, err2 = validate_and_convert_field("holding", "status", "closed", {})
    assert val2 == "closed" and err2 is None
    print("✓ validate: holding status accepts active/closed")


def test_validate_holding_status_invalid():
    val, err = validate_and_convert_field("holding", "status", "pending", {})
    assert val is None and "Invalid status" in err
    print("✓ validate: holding status rejects invalid value")


def test_validate_unknown_field():
    val, err = validate_and_convert_field("trans", "unknown_field", "x", {})
    assert val is None and "Unknown field" in err
    print("✓ validate: rejects unknown field")


# ── validate account field (needs mock) ───────────────────────────

def test_validate_trans_account_exists():
    """Account validation when account exists."""
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir)
        acct_repo = AccountRepository(data_dir / "accounts.json")
        acct_repo.insert({
            "id": "acct_001",
            "name": "mybroker",
            "type": "brokerage",
            "currency": "USD",
            "created_at": datetime.now().isoformat(),
            "total_deposit": 0.0,
            "total_withdrawal": 0.0,
        })

        with patch("ptracker.cli.edit.get_data_dir", return_value=data_dir):
            val, err = validate_and_convert_field("trans", "account", "mybroker", {})
            assert val == "mybroker" and err is None
    print("✓ validate: trans account passes when account exists")


def test_validate_trans_account_not_exists():
    """Account validation when account does not exist."""
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir)
        # create empty accounts db
        AccountRepository(data_dir / "accounts.json")

        with patch("ptracker.cli.edit.get_data_dir", return_value=data_dir):
            val, err = validate_and_convert_field("trans", "account", "ghost", {})
            assert val is None and "does not exist" in err
    print("✓ validate: trans account fails when account missing")


# ── edit_transaction (integration) ────────────────────────────────

def test_edit_transaction_success():
    """Edit a transaction's price and fee."""
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir)
        tx_repo = TransactionRepository(data_dir / "transactions.json")
        tx_repo.insert({
            "id": "txn_001",
            "datetime": datetime.now().isoformat(),
            "type": "buy",
            "action": "open",
            "direction": "long",
            "asset": "AAPL",
            "quantity": 100.0,
            "price": 150.0,
            "currency": "USD",
            "fee": 1.0,
            "account": "mybroker",
            "note": "original",
        })

        from ptracker.cli.edit import edit_transaction
        with patch("ptracker.cli.edit.get_data_dir", return_value=data_dir):
            edit_transaction(data_dir, "txn_001", {"price": 160.0, "fee": 2.5})

        updated = tx_repo.find_by_id("txn_001")
        assert updated["price"] == 160.0
        assert updated["fee"] == 2.5
    print("✓ edit_transaction: updates price and fee")


def test_edit_transaction_not_found():
    """Edit a non-existent transaction should raise Exit."""
    from click.exceptions import Exit
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir)
        TransactionRepository(data_dir / "transactions.json")

        from ptracker.cli.edit import edit_transaction
        try:
            edit_transaction(data_dir, "txn_ghost", {"note": "x"})
            assert False, "Should have raised Exit"
        except (SystemExit, Exit):
            pass
    print("✓ edit_transaction: raises exit for missing transaction")


# ── edit_holding (integration) ────────────────────────────────────

def test_edit_holding_by_id():
    """Edit a holding by ID."""
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir)
        hold_repo = HoldingRepository(data_dir / "holdings.json")
        hold_repo.upsert({
            "asset": "AAPL",
            "account": "mybroker",
            "direction": "long",
            "quantity": 100.0,
            "avg_cost": 150.0,
            "total_invested": 15000.0,
            "currency": "USD",
            "first_open_date": "2026-01-01",
            "last_updated": "2026-01-01",
            "note": "old note",
            "status": "active",
        })
        holding = hold_repo.find_by_asset_account("AAPL", "mybroker", "long")
        hold_id = holding["id"]

        from ptracker.cli.edit import edit_holding
        edit_holding(data_dir, hold_id, None, None, None, {"note": "new note"})

        updated = hold_repo.find_by_id(hold_id)
        assert updated["note"] == "new note"
    print("✓ edit_holding: updates by ID")


def test_edit_holding_by_asset_account():
    """Edit a holding by asset/account/direction."""
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir)
        hold_repo = HoldingRepository(data_dir / "holdings.json")
        hold_repo.upsert({
            "asset": "700.HK",
            "account": "longbridge",
            "direction": "long",
            "quantity": 200.0,
            "avg_cost": 300.0,
            "total_invested": 60000.0,
            "currency": "HKD",
            "first_open_date": "2026-01-01",
            "last_updated": "2026-01-01",
            "note": "",
            "status": "active",
        })

        from ptracker.cli.edit import edit_holding
        edit_holding(data_dir, None, "700.HK", "longbridge", "long", {"status": "closed"})

        updated = hold_repo.find_by_asset_account("700.HK", "longbridge", "long")
        assert updated["status"] == "closed"
    print("✓ edit_holding: updates by asset/account/direction")


def test_edit_holding_not_found():
    """Edit a non-existent holding should raise Exit."""
    from click.exceptions import Exit
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir)
        HoldingRepository(data_dir / "holdings.json")

        from ptracker.cli.edit import edit_holding
        try:
            edit_holding(data_dir, "hold_ghost", None, None, None, {"note": "x"})
            assert False, "Should have raised Exit"
        except (SystemExit, Exit):
            pass
    print("✓ edit_holding: raises exit for missing holding")


# ── edit_realized (integration) ───────────────────────────────────

def test_edit_realized_success():
    """Edit a realized position's note."""
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir)
        real_repo = RealizedRepository(data_dir / "realized.json")
        real_repo.insert({
            "id": "real_001",
            "asset": "AAPL",
            "account": "mybroker",
            "direction": "long",
            "first_open_date": "2025-01-01",
            "last_close_date": "2026-01-01",
            "holding_days": 365,
            "total_quantity": 100.0,
            "total_invested": 10000.0,
            "total_proceeds": 12000.0,
            "total_fees": 20.0,
            "realized_pnl": 1980.0,
            "return_pct": 19.8,
            "note": "old",
            "status": "closed",
        })

        from ptracker.cli.edit import edit_realized
        edit_realized(data_dir, "real_001", {"note": "updated note"})

        updated = real_repo.find_by_id("real_001")
        assert updated["note"] == "updated note"
    print("✓ edit_realized: updates note")


def test_edit_realized_not_found():
    """Edit a non-existent realized position should raise Exit."""
    from click.exceptions import Exit
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir)
        RealizedRepository(data_dir / "realized.json")

        from ptracker.cli.edit import edit_realized
        try:
            edit_realized(data_dir, "real_ghost", {"note": "x"})
            assert False, "Should have raised Exit"
        except (SystemExit, Exit):
            pass
    print("✓ edit_realized: raises exit for missing realized")


# ── main ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    # parse_field_args
    test_parse_field_args_basic()
    test_parse_field_args_value_with_equals()
    test_parse_field_args_invalid_format()
    test_parse_field_args_empty_field_name()

    # validate_and_convert_field
    test_validate_trans_price()
    test_validate_trans_price_invalid()
    test_validate_trans_fee()
    test_validate_trans_fee_invalid()
    test_validate_trans_note()
    test_validate_holding_status_valid()
    test_validate_holding_status_invalid()
    test_validate_unknown_field()
    test_validate_trans_account_exists()
    test_validate_trans_account_not_exists()

    # integration: edit_transaction
    test_edit_transaction_success()
    test_edit_transaction_not_found()

    # integration: edit_holding
    test_edit_holding_by_id()
    test_edit_holding_by_asset_account()
    test_edit_holding_not_found()

    # integration: edit_realized
    test_edit_realized_success()
    test_edit_realized_not_found()

    print("\n✅ All edit tests passed!")
