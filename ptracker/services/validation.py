"""Validation service for business rules."""

from typing import List, Dict, Any
import re


class ValidationService:
    """Validate business rules and data consistency."""
    
    def __init__(self, transaction_repo=None):
        """Initialize with optional transaction repository.
        
        Args:
            transaction_repo: TransactionRepository instance
        """
        self.transaction_repo = transaction_repo
    
    def validate_transaction(self, transaction: Dict[str, Any]) -> List[str]:
        """Validate transaction data and business rules.
        
        Args:
            transaction: Transaction data dict
            
        Returns:
            List of error messages (empty if valid)
        """
        errors = []
        
        # Validate required fields
        required_fields = ['type', 'action', 'direction', 'asset', 'quantity', 'price', 'currency', 'account']
        for field in required_fields:
            if field not in transaction or transaction[field] is None:
                errors.append(f"Missing required field: {field}")
        
        if errors:
            return errors
        
        # Validate quantity sign
        if not self.validate_quantity_sign(
            transaction['quantity'],
            transaction['type'],
            transaction['action'],
            transaction['direction']
        ):
            errors.append(
                f"Invalid quantity sign for {transaction['type']}/{transaction['action']}/{transaction['direction']}"
            )
        
        # Validate asset code format
        if not self.validate_asset_code(transaction['asset']):
            errors.append(f"Invalid asset code format: {transaction['asset']}")
        
        # Validate price is positive
        if transaction['price'] <= 0:
            errors.append("Price must be positive")
        
        # Validate currency code (basic check)
        if len(transaction['currency']) != 3:
            errors.append("Currency code must be 3 characters")
        
        return errors
    
    def validate_account_deletion(self, account_name: str) -> bool:
        """Check if account can be deleted (no transactions).
        
        Args:
            account_name: Account name to check
            
        Returns:
            True if account can be deleted, False otherwise
        """
        if not self.transaction_repo:
            return True
        
        # Check if any transactions exist for this account
        all_transactions = self.transaction_repo.find_all()
        has_transactions = any(t['account'] == account_name for t in all_transactions)
        
        return not has_transactions
    
    def validate_asset_code(self, asset: str) -> bool:
        """Validate asset code format (Yahoo Finance style).
        
        Args:
            asset: Asset code to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not asset or len(asset) < 1:
            return False
        
        # Basic validation: alphanumeric, dots, hyphens, equals
        # Examples: AAPL, 0700.HK, BTC-USD, 600000.SS, HKDUSD=X
        pattern = r'^[A-Z0-9][A-Z0-9\.\-=]*$'
        return bool(re.match(pattern, asset, re.IGNORECASE))
    
    def validate_quantity_sign(
        self,
        quantity: float,
        tx_type: str,
        action: str,
        direction: str
    ) -> bool:
        """Validate quantity sign matches transaction type.

        Args:
            quantity: Transaction quantity
            tx_type: Transaction type ('buy', 'sell', or 'dividend')
            action: Transaction action ('open', 'close', or 'income')
            direction: Position direction ('long' or 'short')

        Returns:
            True if valid, False otherwise
        """
        # Dividends don't use quantity validation
        if tx_type == "dividend" and action == "income":
            return True

        # Determine expected sign
        if tx_type == "buy" and action == "open" and direction == "long":
            expected_positive = True
        elif tx_type == "buy" and action == "close" and direction == "short":
            expected_positive = True
        elif tx_type == "sell" and action == "close" and direction == "long":
            expected_positive = False
        elif tx_type == "sell" and action == "open" and direction == "short":
            expected_positive = False
        else:
            # Invalid combination
            return False

        # Check if sign matches expectation
        if expected_positive:
            return quantity > 0
        else:
            return quantity < 0

