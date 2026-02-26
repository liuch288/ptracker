"""Transaction repository."""

from typing import Any, Dict, List
from tinydb import Query
from ptracker.repositories.base import BaseRepository


class TransactionRepository(BaseRepository):
    """Repository for transaction records."""
    
    def find_by_asset_account(
        self,
        asset: str,
        account: str,
        direction: str
    ) -> List[Dict[str, Any]]:
        """Find all transactions for specific asset/account/direction.
        
        Args:
            asset: Asset code
            account: Account name
            direction: Position direction ('long' or 'short')
            
        Returns:
            List of matching transactions
        """
        db, lock = self._read()
        try:
            Q = Query()
            return db.search(
                (Q.asset == asset) &
                (Q.account == account) &
                (Q.direction == direction)
            )
        finally:
            db.close()
            lock.release()
