"""Holding repository."""

from typing import Any, Dict, Optional
from tinydb import Query
from ptracker.repositories.base import BaseRepository
from ptracker.utils.id_generator import generate_id


class HoldingRepository(BaseRepository):
    """Repository for holding records."""
    
    def find_by_id(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Find holding by ID.
        
        Args:
            doc_id: Holding ID
            
        Returns:
            Holding data or None if not found
        """
        db, lock = self._read()
        try:
            Q = Query()
            result = db.search(Q.id == doc_id)
            return result[0] if result else None
        finally:
            db.close()
            lock.release()
    
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
                # Update existing (preserve id)
                holding['id'] = existing[0]['id']
                db.update(
                    holding,
                    (Q.asset == holding['asset']) &
                    (Q.account == holding['account']) &
                    (Q.direction == holding['direction'])
                )
            else:
                # Insert new with generated id
                if 'id' not in holding:
                    holding['id'] = generate_id('hold')
                db.insert(holding)
        finally:
            db.close()
            lock.release()
    
    def update_by_id(self, doc_id: str, updates: Dict[str, Any]) -> bool:
        """Update holding by ID.
        
        Args:
            doc_id: Holding ID
            updates: Dictionary of fields to update
            
        Returns:
            True if updated successfully, False if not found
        """
        db, lock = self._write()
        try:
            Q = Query()
            existing = db.search(Q.id == doc_id)
            if not existing:
                return False
            
            # Preserve the id and immutable fields
            updated_holding = {**existing[0], **updates}
            updated_holding['id'] = existing[0]['id']
            
            db.update(
                updated_holding,
                Q.id == doc_id
            )
            return True
        finally:
            db.close()
            lock.release()
