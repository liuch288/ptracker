"""P&L calculator service."""

import re
from typing import Dict, Any

# US Option pattern: AAPL250117C00150000
US_OPTION_PATTERN = re.compile(r'^[A-Z]{1,4}\d{6}[CP]\d{8}$')

# Option contract multiplier
OPTION_CONTRACT_MULTIPLIER = 100


def is_option(asset: str) -> bool:
    """Check if asset is a US option based on Yahoo Finance format."""
    return bool(US_OPTION_PATTERN.match(asset))


def get_multiplier(asset: str, quantity: float) -> float:
    """Get multiplier for asset. Returns 100 for options if quantity <= 10.
    
    Args:
        asset: Asset code
        quantity: Holding quantity
        
    Returns:
        100.0 for options (if quantity suggests not yet multiplied), 1.0 otherwise
    """
    if is_option(asset):
        # If quantity > 10, assume already multiplied in old data
        if quantity > 10:
            return 1.0
        return OPTION_CONTRACT_MULTIPLIER
    return 1.0


class PnLCalculator:
    """Calculate realized and unrealized profit/loss."""
    
    def __init__(self, price_service=None):
        """Initialize with price service dependency.
        
        Args:
            price_service: Optional PriceService instance
        """
        self.price_service = price_service
    
    def calculate_realized_pnl(
        self,
        total_invested: float,
        total_proceeds: float,
        total_fees: float,
        direction: str
    ) -> float:
        """Calculate realized P&L for closed position.
        
        Args:
            total_invested: Total capital invested
            total_proceeds: Total proceeds from closing
            total_fees: Total fees paid
            direction: Position direction ('long' or 'short')
            
        Returns:
            Realized P&L amount
        """
        if direction == "long":
            # Long: proceeds - invested - fees
            return total_proceeds - total_invested
        else:
            # Short: proceeds - cost - fees
            # (total_invested is actually proceeds for short)
            # (total_proceeds is actually cost for short)
            return total_invested - total_proceeds
    
    def calculate_unrealized_pnl(
        self,
        holding: Dict[str, Any],
        current_price: float
    ) -> float:
        """Calculate unrealized P&L for open position.
        
        Args:
            holding: Holding data dict
            current_price: Current market price
            
        Returns:
            Unrealized P&L amount
        """
        direction = holding['direction']
        quantity = holding['quantity']
        total_invested = holding['total_invested']
        asset = holding.get('asset', '')
        
        # Get multiplier for options (100x for option contracts)
        multiplier = get_multiplier(asset, quantity)
        
        # For options, total_invested is already stored with multiplier applied
        # (see position_calculator.py). Only current_value needs multiplier.
        if multiplier > 1.0:
            # This is an option - only apply multiplier to current value
            if direction == "long":
                current_value = current_price * quantity * multiplier
                return current_value - total_invested
            else:
                # Short
                current_cost = current_price * abs(quantity) * multiplier
                return total_invested - current_cost
        else:
            # Regular stock
            if direction == "long":
                current_value = current_price * quantity
                return current_value - total_invested
            else:
                current_cost = current_price * abs(quantity)
                return total_invested - current_cost
    
    def calculate_return_pct(
        self,
        pnl: float,
        total_invested: float
    ) -> float:
        """Calculate return percentage.
        
        Args:
            pnl: Profit/loss amount
            total_invested: Total capital invested
            
        Returns:
            Return percentage
        """
        if total_invested == 0:
            return 0.0
        
        return (pnl / total_invested) * 100.0
