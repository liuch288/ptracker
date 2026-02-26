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
