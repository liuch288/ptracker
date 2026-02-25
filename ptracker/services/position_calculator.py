"""Position calculator service."""

from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime, date
from ptracker.repositories import TransactionRepository, HoldingRepository, RealizedRepository
from ptracker.models import Transaction, Holding


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
    
    def calculate_average_cost(
        self,
        transactions: List[Dict[str, Any]],
        direction: str
    ) -> tuple[float, float]:
        """Calculate weighted average cost for position.
        
        Args:
            transactions: List of transaction dicts
            direction: Position direction ('long' or 'short')
            
        Returns:
            Tuple of (avg_cost, total_invested/total_proceeds)
        """
        if direction == "long":
            # For long positions: avg_cost = total_invested / total_quantity
            total_invested = 0.0
            total_quantity = 0.0
            
            for txn in transactions:
                if txn['action'] == 'open' and txn['direction'] == 'long':
                    cost = (abs(txn['quantity']) * txn['price']) + txn['fee']
                    total_invested += cost
                    total_quantity += abs(txn['quantity'])
            
            if total_quantity == 0:
                return 0.0, 0.0
            
            avg_cost = total_invested / total_quantity
            return avg_cost, total_invested
        
        else:  # short
            # For short positions: avg_cost = total_proceeds / total_quantity
            total_proceeds = 0.0
            total_quantity = 0.0
            
            for txn in transactions:
                if txn['action'] == 'open' and txn['direction'] == 'short':
                    proceeds = (abs(txn['quantity']) * txn['price']) - txn['fee']
                    total_proceeds += proceeds
                    total_quantity += abs(txn['quantity'])
            
            if total_quantity == 0:
                return 0.0, 0.0
            
            avg_cost = total_proceeds / total_quantity
            return avg_cost, total_proceeds
    
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
    
    def recalculate_position(
        self,
        asset: str,
        account: str,
        direction: str
    ) -> Optional[PositionUpdate]:
        """Recalculate position after transaction added/modified.
        
        Args:
            asset: Asset code
            account: Account name
            direction: Position direction
            
        Returns:
            PositionUpdate with holding changes and optional realized position
        """
        # Get all transactions for this position
        transactions = self.transaction_repo.find_by_asset_account(asset, account, direction)
        
        if not transactions:
            return None
        
        # Sort by datetime
        transactions.sort(key=lambda t: t['datetime'])
        
        # Calculate net quantity
        net_quantity = sum(t['quantity'] for t in transactions)
        
        # Get existing holding
        existing_holding = self.holding_repo.find_by_asset_account(asset, account, direction)
        old_quantity = existing_holding['quantity'] if existing_holding else 0.0
        
        # Detect closure
        closure_type = self.detect_closure(old_quantity, net_quantity)
        
        # Calculate average cost and total invested
        avg_cost, total_invested = self.calculate_average_cost(transactions, direction)
        
        # Get dates
        first_open_date = transactions[0]['datetime'][:10] if transactions else date.today().isoformat()
        last_updated = transactions[-1]['datetime'][:10] if transactions else date.today().isoformat()
        
        # Concatenate notes
        notes = [t['note'] for t in transactions if t.get('note')]
        note = '|'.join(notes) if notes else ''
        
        # Get currency from first transaction
        currency = transactions[0]['currency'] if transactions else 'USD'
        
        # Create/update holding
        holding_data = {
            'asset': asset,
            'account': account,
            'direction': direction,
            'quantity': net_quantity,
            'avg_cost': avg_cost,
            'total_invested': total_invested,
            'currency': currency,
            'first_open_date': first_open_date,
            'last_updated': last_updated,
            'note': note,
            'status': 'active'
        }
        
        realized_data = None
        
        # Handle closures
        if closure_type in [ClosureType.FULL, ClosureType.REVERSED]:
            # Create realized position
            realized_data = self.create_realized_position(
                transactions,
                existing_holding or holding_data,
                closure_type
            )
        
        return PositionUpdate(
            holding=holding_data if net_quantity != 0 else None,
            realized=realized_data,
            closure_type=closure_type
        )
    
    def create_realized_position(
        self,
        transactions: List[Dict[str, Any]],
        holding: Dict[str, Any],
        closure_type: ClosureType
    ) -> Dict[str, Any]:
        """Create realized position record from closed position.
        
        Args:
            transactions: All transactions for this position
            holding: Holding data
            closure_type: Type of closure
            
        Returns:
            Realized position data dict
        """
        from ptracker.utils.id_generator import generate_id
        
        # Separate opening and closing transactions
        opening_txns = [t for t in transactions if t['action'] == 'open']
        closing_txns = [t for t in transactions if t['action'] == 'close']
        
        # Calculate totals
        total_quantity = sum(abs(t['quantity']) for t in opening_txns)
        total_fees = sum(t['fee'] for t in transactions)
        
        # Calculate invested and proceeds
        if holding['direction'] == 'long':
            total_invested = sum(
                (abs(t['quantity']) * t['price']) + t['fee']
                for t in opening_txns
            )
            total_proceeds = sum(
                (abs(t['quantity']) * t['price']) - t['fee']
                for t in closing_txns
            )
            realized_pnl = total_proceeds - total_invested
        else:  # short
            total_proceeds = sum(
                (abs(t['quantity']) * t['price']) - t['fee']
                for t in opening_txns
            )
            total_cost = sum(
                (abs(t['quantity']) * t['price']) + t['fee']
                for t in closing_txns
            )
            total_invested = total_proceeds  # For return calculation
            realized_pnl = total_proceeds - total_cost
        
        # Calculate return percentage
        return_pct = (realized_pnl / total_invested * 100) if total_invested > 0 else 0.0
        
        # Calculate holding days
        first_date = datetime.fromisoformat(transactions[0]['datetime'].replace('Z', '+00:00'))
        last_date = datetime.fromisoformat(transactions[-1]['datetime'].replace('Z', '+00:00'))
        holding_days = (last_date.date() - first_date.date()).days
        
        # Concatenate notes
        notes = [t['note'] for t in transactions if t.get('note')]
        note = '|'.join(notes) if notes else ''
        
        return {
            'id': generate_id('real'),
            'asset': holding['asset'],
            'account': holding['account'],
            'direction': holding['direction'],
            'first_open_date': transactions[0]['datetime'][:10],
            'last_close_date': transactions[-1]['datetime'][:10],
            'holding_days': holding_days,
            'total_quantity': total_quantity,
            'total_invested': total_invested,
            'total_proceeds': total_proceeds,
            'total_fees': total_fees,
            'realized_pnl': realized_pnl,
            'return_pct': return_pct,
            'note': note,
            'status': 'closed'
        }
