#!/usr/bin/env python3
"""Test dividend functionality."""

import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from ptracker.models.transaction import Transaction
from ptracker.services.validation import ValidationService


def test_dividend_model():
    """Test dividend transaction model."""
    print("Testing dividend transaction model...")
    
    try:
        dividend = Transaction(
            id='test-div-001',
            datetime=datetime.now(),
            type='dividend',
            action='income',
            direction='long',
            asset='AAPL',
            quantity=0.0,
            price=100.0,
            currency='USD',
            fee=0.0,
            account='test',
            note='Q1 dividend'
        )
        
        assert dividend.type == 'dividend'
        assert dividend.action == 'income'
        assert dividend.quantity == 0.0
        assert dividend.price == 100.0
        
        print("✓ Dividend model validation passed")
        return True
        
    except Exception as e:
        print(f"✗ Dividend model validation failed: {e}")
        return False


def test_dividend_validation():
    """Test dividend validation."""
    print("\nTesting dividend validation...")
    
    try:
        validation_service = ValidationService()
        
        # Valid dividend transaction
        dividend_data = {
            'id': 'test-div-002',
            'datetime': datetime.now().isoformat(),
            'type': 'dividend',
            'action': 'income',
            'direction': 'long',
            'asset': 'AAPL',
            'quantity': 0.0,
            'price': 50.0,
            'currency': 'USD',
            'fee': 0.0,
            'account': 'test',
            'note': 'Test dividend'
        }
        
        errors = validation_service.validate_transaction(dividend_data)
        
        if errors:
            print(f"✗ Validation failed with errors: {errors}")
            return False
        
        print("✓ Dividend validation passed")
        return True
        
    except Exception as e:
        print(f"✗ Dividend validation failed: {e}")
        return False


def test_buy_sell_still_work():
    """Test that buy/sell transactions still work."""
    print("\nTesting buy/sell transactions...")
    
    try:
        # Test buy transaction
        buy_tx = Transaction(
            id='test-buy-001',
            datetime=datetime.now(),
            type='buy',
            action='open',
            direction='long',
            asset='AAPL',
            quantity=100.0,
            price=150.0,
            currency='USD',
            fee=1.0,
            account='test',
            note='Test buy'
        )
        
        assert buy_tx.type == 'buy'
        assert buy_tx.quantity == 100.0
        
        # Test sell transaction
        sell_tx = Transaction(
            id='test-sell-001',
            datetime=datetime.now(),
            type='sell',
            action='close',
            direction='long',
            asset='AAPL',
            quantity=-100.0,
            price=160.0,
            currency='USD',
            fee=1.0,
            account='test',
            note='Test sell'
        )
        
        assert sell_tx.type == 'sell'
        assert sell_tx.quantity == -100.0
        
        print("✓ Buy/sell transactions still work")
        return True
        
    except Exception as e:
        print(f"✗ Buy/sell test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("Testing Dividend Functionality")
    print("=" * 60)
    
    results = []
    
    results.append(test_dividend_model())
    results.append(test_dividend_validation())
    results.append(test_buy_sell_still_work())
    
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
