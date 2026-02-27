"""Cash flow repository."""

from typing import Any, Dict, List
from tinydb import Query
from ptracker.repositories.base import BaseRepository


class CashFlowRepository(BaseRepository):
    """Repository for cash flow records."""
    
    def find_by_account(self, account: str) -> List[Dict[str, Any]]:
        """Find all cash flows for an account.
        
        Args:
            account: Account name
            
        Returns:
            List of cash flow records
        """
        db, lock = self._read()
        try:
            Q = Query()
            return db.search(Q.account == account)
        finally:
            db.close()
            lock.release()
