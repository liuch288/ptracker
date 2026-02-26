"""Realized position repository."""

from typing import Any, Dict, List
from tinydb import Query
from ptracker.repositories.base import BaseRepository


class RealizedRepository(BaseRepository):
    """Repository for realized position records."""
    
    def find_by_date_range(self, start: str, end: str) -> List[Dict[str, Any]]:
        """Find realized positions within date range.
        
        Args:
            start: Start date (YYYY-MM-DD)
            end: End date (YYYY-MM-DD)
            
        Returns:
            List of realized positions closed within date range
        """
        db, lock = self._read()
        try:
            Q = Query()
            return db.search(
                (Q.last_close_date >= start) &
                (Q.last_close_date <= end)
            )
        finally:
            db.close()
            lock.release()
