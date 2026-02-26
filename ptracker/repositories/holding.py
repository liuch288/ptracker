"""Holding repository."""

from typing import Any, Dict, Optional
from tinydb import Query
from ptracker.repositories.base import BaseRepository


class HoldingRepository(BaseRepository):
    """Repository for holding records."""
    
    def find_by_asset_account(
        self,
        asset: str,
        account: str,
        direction: str
    ) -> Optional[Dict[str, Any]]:
        """Find holding for specific asset/account/direction.
        
        Args:
            asset: Asset code
            account: Account name
            direction: Position direction ('long' or 'short')
            
        Returns:
            Holding data or None if not found
        """
        db, lock = self._read()
        try:
            Q = Query()
            result = db.search(
                (Q.asset == asset) &
                (Q.account == account) &
                (Q.direction == direction)
            )
            return result[0] if result else None
        finally:
            db.close()
            lock.release()
    
    def upsert(self, holding: Dict[str, Any]) -> None:
        """Insert or update holding.
        
        Args:
            holding: Holding data with asset, account, direction fields
        """
        db, lock = self._write()
        try:
            Q = Query()
            existing = db.search(
                (Q.asset == holding['asset']) &
                (Q.account == holding['account']) &
                (Q.direction == holding['direction'])
            )
            
            if existing:
                # Update existing
                db.update(
                    holding,
                    (Q.asset == holding['asset']) &
                    (Q.account == holding['account']) &
                    (Q.direction == holding['direction'])
                )
            else:
                # Insert new
                db.insert(holding)
        finally:
            db.close()
            lock.release()
