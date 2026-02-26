"""Position calculator service."""

from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime, date
from ptracker.repositories import TransactionRepository, HoldingRepository, RealizedRepository
from ptracker.models import Transaction, Holding
from ptracker.utils.id_generator import generate_id


class ClosureType(Enum):
    """Position closure type."""
    NONE = "none"
    PARTIAL = "partial"
    FULL = "full"
    REVERSED = "reversed"


class PositionUpdate:
    """Result of position recalculation."""
    
    def __init__(
        self,
        holding: Optional[Dict[str, Any]] = None,
        realized: Optional[Dict[str, Any]] = None,
        closure_type: ClosureType = ClosureType.NONE
    ):
        self.holding = holding
        self.realized = realized
        self.closure_type = closure_type


class PositionCalculator:
    """Calculate holdings and detect position closures from transaction history."""
    
    def __init__(
        self,
        transaction_repo: TransactionRepository,
        holding_repo: HoldingRepository,
        realized_repo: RealizedRepository
    ):
        """Initialize with repository dependencies."""
        self.transaction_repo = transaction_repo
        self.holding_repo = holding_repo
        self.realized_repo = realized_repo
    
    def update_position_incremental(
        self,
        transaction: Dict[str, Any],
        existing_holding: Optional[Dict[str, Any]]
    ) -> PositionUpdate:
        """Update position incrementally based on new transaction.
        
        Args:
            transaction: New transaction data
            existing_holding: Current holding or None
            
        Returns:
            PositionUpdate with changes
        """
        asset = transaction['asset']
        account = transaction['account']
        direction = transaction['direction']
        action = transaction['action']
        quantity = transaction['quantity']
        price = transaction['price']
        fee = transaction['fee']
        currency = transaction['currency']
        tx_date = transaction['datetime'][:10]
        note = transaction['note']
        
        # No existing holding - create new one
        if not existing_holding or existing_holding['quantity'] == 0:
            if action == 'open':
                # New position
                qty = abs(quantity)
                if direction == 'long':
                    total_invested = (qty * price) + fee
                    avg_cost = total_invested / qty
                else:  # short
                    total_invested = (qty * price) - fee
                    avg_cost = total_invested / qty
                
                holding_data = {
                    'asset': asset,
                    'account': account,
                    'direction': direction,
                    'quantity': qty,
                    'avg_cost': avg_cost,
                    'total_invested': total_invested,
                    'currency': currency,
                    'first_open_date': tx_date,
                    'last_updated': tx_date,
                    'note': note,
                    'status': 'active'
                }
                
                return PositionUpdate(holding=holding_data, closure_type=ClosureType.NONE)
            else:
                # Close without open - error case, but return None
                return PositionUpdate(closure_type=ClosureType.NONE)
        
        # Has existing holding
        old_quantity = existing_holding['quantity']
        old_avg_cost = existing_holding['avg_cost']
        old_total_invested = existing_holding['total_invested']
        
        if action == 'open':
            # Add to position
            add_qty = abs(quantity)
            if direction == 'long':
                add_cost = (add_qty * price) + fee
            else:  # short
                add_cost = (add_qty * price) - fee
            
            new_quantity = old_quantity + add_qty
            new_total_invested = old_total_invested + add_cost
            new_avg_cost = new_total_invested / new_quantity
            
            holding_data = {
                **existing_holding,
                'quantity': new_quantity,
                'avg_cost': new_avg_cost,
                'total_invested': new_total_invested,
                'last_updated': tx_date,
                'note': f"{existing_holding['note']}|{note}" if existing_holding['note'] and note else (existing_holding['note'] or note)
            }
            
            return PositionUpdate(holding=holding_data, closure_type=ClosureType.NONE)
        
        else:  # action == 'close'
            # Reduce position
            close_qty = abs(quantity)
            new_quantity = old_quantity - close_qty
            
            # Detect closure type
            closure_type = self.detect_closure(old_quantity, new_quantity)
            
            # Calculate proceeds from closing
            if direction == 'long':
                close_proceeds = (close_qty * price) - fee
                close_cost = close_qty * old_avg_cost
                realized_pnl = close_proceeds - close_cost
            else:  # short
                close_cost = (close_qty * price) + fee
                close_proceeds = close_qty * old_avg_cost
                realized_pnl = close_proceeds - close_cost
            
            realized_data = None
            holding_data = None
            
            if closure_type == ClosureType.FULL:
                # Full closure
                return_pct = (realized_pnl / old_total_invested * 100) if old_total_invested > 0 else 0.0
                
                first_date = datetime.fromisoformat(existing_holding['first_open_date'])
                last_date = datetime.fromisoformat(tx_date)
                holding_days = (last_date.date() - first_date.date()).days
                
                realized_data = {
                    'id': generate_id('real'),
                    'asset': asset,
                    'account': account,
                    'direction': direction,
                    'first_open_date': existing_holding['first_open_date'],
                    'last_close_date': tx_date,
                    'holding_days': holding_days,
                    'total_quantity': old_quantity,
                    'total_invested': old_total_invested,
                    'total_proceeds': close_proceeds if direction == 'long' else old_total_invested - realized_pnl,
                    'total_fees': fee,
                    'realized_pnl': realized_pnl,
                    'return_pct': return_pct,
                    'currency': currency,
                    'note': f"{existing_holding['note']}|{note}" if existing_holding['note'] and note else (existing_holding['note'] or note),
                    'status': 'closed'
                }
                
            elif closure_type == ClosureType.PARTIAL:
                # Partial closure - net investment reduces by proceeds received
                if direction == 'long':
                    # For long: reduce investment by proceeds from sale
                    new_total_invested = old_total_invested - close_proceeds
                else:  # short
                    # For short: reduce investment by cost to cover
                    new_total_invested = old_total_invested - close_cost
                
                # Recalculate avg_cost based on new net investment
                new_avg_cost = new_total_invested / new_quantity if new_quantity > 0 else 0.0
                
                holding_data = {
                    **existing_holding,
                    'quantity': new_quantity,
                    'avg_cost': new_avg_cost,
                    'total_invested': new_total_invested,
                    'last_updated': tx_date,
                    'note': f"{existing_holding['note']}|{note}" if existing_holding['note'] and note else (existing_holding['note'] or note)
                }
            
            return PositionUpdate(
                holding=holding_data,
                realized=realized_data,
                closure_type=closure_type
            )
    
    def detect_closure(
        self,
        old_quantity: float,
        new_quantity: float
    ) -> ClosureType:
        """Detect if position closed, partially closed, or reversed.
        
        Args:
            old_quantity: Previous position quantity
            new_quantity: New position quantity
            
        Returns:
            ClosureType enum value
        """
        # Full closure (long position)
        if old_quantity > 0 and new_quantity == 0:
            return ClosureType.FULL
        
        # Full closure (short position)
        if old_quantity < 0 and new_quantity == 0:
            return ClosureType.FULL
        
        # Reversed (long to short)
        if old_quantity > 0 and new_quantity < 0:
            return ClosureType.REVERSED
        
        # Reversed (short to long)
        if old_quantity < 0 and new_quantity > 0:
            return ClosureType.REVERSED
        
        # Partial closure
        if old_quantity != 0 and new_quantity != 0:
            if abs(new_quantity) < abs(old_quantity):
                # Same sign but smaller magnitude
                if (old_quantity > 0 and new_quantity > 0) or (old_quantity < 0 and new_quantity < 0):
                    return ClosureType.PARTIAL
        
        # No closure (position increased or stayed same)
        return ClosureType.NONE
    
    
