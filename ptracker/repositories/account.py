"""Account repository."""

from typing import Any, Dict, Optional
from tinydb import Query
from ptracker.repositories.base import BaseRepository


class AccountRepository(BaseRepository):
    """Repository for account records."""
    
    def find_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Find account by name.
        
        Args:
            name: Account name
            
        Returns:
            Account data or None if not found
        """
        db, lock = self._read()
        try:
            Q = Query()
            result = db.search(Q.name == name)
            return result[0] if result else None
        finally:
            db.close()
            lock.release()
    
    def update_deposit(self, name: str, amount: float) -> None:
        """Add deposit amount to account.
        
        Args:
            name: Account name
            amount: Deposit amount
        """
        db, lock = self._write()
        try:
            Q = Query()
            account = db.search(Q.name == name)
            if account:
                current = account[0].get('total_deposit', 0.0)
                db.update({'total_deposit': current + amount}, Q.name == name)
        finally:
            db.close()
            lock.release()
    
    def update_withdrawal(self, name: str, amount: float) -> None:
        """Add withdrawal amount to account.
        
        Args:
            name: Account name
            amount: Withdrawal amount
        """
        db, lock = self._write()
        try:
            Q = Query()
            account = db.search(Q.name == name)
            if account:
                current = account[0].get('total_withdrawal', 0.0)
                db.update({'total_withdrawal': current + amount}, Q.name == name)
        finally:
            db.close()
            lock.release()
