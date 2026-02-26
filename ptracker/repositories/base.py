"""Base repository with file locking."""

from pathlib import Path
from typing import Any, Dict, List, Optional
from tinydb import TinyDB, Query
from filelock import FileLock


class BaseRepository:
    """Base repository providing abstraction over TinyDB with filelock protection."""
    
    def __init__(self, db_path: Path):
        """Initialize repository with database path.
        
        Args:
            db_path: Path to TinyDB JSON file
        """
        self.db_path = db_path
        self.lock_path = db_path.with_suffix('.lock')
    
    def _read(self) -> tuple[TinyDB, FileLock]:
        """Open database for reading (with shared lock).
        
        Returns:
            Tuple of (TinyDB instance, FileLock instance)
        """
        lock = FileLock(self.lock_path, timeout=10)
        lock.acquire()
        db = TinyDB(self.db_path)
        return db, lock
    
    def _write(self) -> tuple[TinyDB, FileLock]:
        """Open database for writing (with exclusive lock).
        
        Returns:
            Tuple of (TinyDB instance, FileLock instance)
        """
        lock = FileLock(self.lock_path, timeout=10)
        lock.acquire()
        db = TinyDB(self.db_path)
        return db, lock
    
    def insert(self, data: Dict[str, Any]) -> str:
        """Insert document and return ID.
        
        Args:
            data: Document data with 'id' field
            
        Returns:
            Document ID
        """
        db, lock = self._write()
        try:
            db.insert(data)
            return data['id']
        finally:
            db.close()
            lock.release()
    
    def update(self, doc_id: str, data: Dict[str, Any]) -> bool:
        """Update document by ID.
        
        Args:
            doc_id: Document ID
            data: Fields to update
            
        Returns:
            True if document was updated, False otherwise
        """
        db, lock = self._write()
        try:
            Q = Query()
            result = db.update(data, Q.id == doc_id)
            return len(result) > 0
        finally:
            db.close()
            lock.release()
    
    def delete(self, doc_id: str) -> bool:
        """Delete document by ID.
        
        Args:
            doc_id: Document ID
            
        Returns:
            True if document was deleted, False otherwise
        """
        db, lock = self._write()
        try:
            Q = Query()
            result = db.remove(Q.id == doc_id)
            return len(result) > 0
        finally:
            db.close()
            lock.release()
    
    def find_all(self) -> List[Dict[str, Any]]:
        """Find all documents.
        
        Returns:
            List of all documents
        """
        db, lock = self._read()
        try:
            return db.all()
        finally:
            db.close()
            lock.release()
    
    def find_by_id(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Find document by ID.
        
        Args:
            doc_id: Document ID
            
        Returns:
            Document data or None if not found
        """
        db, lock = self._read()
        try:
            Q = Query()
            result = db.search(Q.id == doc_id)
            return result[0] if result else None
        finally:
            db.close()
            lock.release()
