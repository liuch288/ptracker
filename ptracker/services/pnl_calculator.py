"""P&L calculator service."""

from typing import Dict, Any


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
        
        if direction == "long":
            # Long: (current_price * quantity) - total_invested
            current_value = current_price * quantity
            return current_value - total_invested
        else:
            # Short: total_proceeds - (current_price * abs(quantity))
            # For short, total_invested is actually the proceeds
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
