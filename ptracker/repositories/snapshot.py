"""Snapshot repository for persisting portfolio snapshots."""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from ptracker.repositories.base import BaseRepository


class SnapshotRepository(BaseRepository):
    """Repository for portfolio snapshot records.
    
    Stores snapshots in a single JSON file using TinyDB.
    Each snapshot is identified by its snapshot_time.
    """
    
    def find_latest(self) -> Optional[Dict[str, Any]]:
        """Find the most recent snapshot.
        
        Returns:
            Latest snapshot data or None if no snapshots exist
        """
        snapshots = self.find_all()
        if not snapshots:
            return None
        
        # Sort by snapshot_time descending
        snapshots.sort(
            key=lambda s: s.get('snapshot_time', ''),
            reverse=True
        )
        return snapshots[0]
    
    def find_by_date(self, date: str) -> Optional[Dict[str, Any]]:
        """Find snapshot by date (YYYY-MM-DD).
        
        Args:
            date: Date string in YYYY-MM-DD format
            
        Returns:
            Snapshot data or None if not found
        """
        snapshots = self.find_all()
        for s in snapshots:
            snapshot_date = s.get('snapshot_time', '')[:10]
            if snapshot_date == date:
                return s
        return None
    
    def find_recent(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Find recent snapshots.
        
        Args:
            limit: Maximum number of snapshots to return
            
        Returns:
            List of recent snapshots, sorted by time descending
        """
        snapshots = self.find_all()
        snapshots.sort(
            key=lambda s: s.get('snapshot_time', ''),
            reverse=True
        )
        return snapshots[:limit]
    
    def save_snapshot(self, snapshot: Dict[str, Any]) -> str:
        """Save a new snapshot.
        
        Args:
            snapshot: Snapshot data dict
            
        Returns:
            Snapshot ID (snapshot_time)
        """
        # Ensure snapshot_time is set
        if 'snapshot_time' not in snapshot:
            snapshot['snapshot_time'] = datetime.now().isoformat()
        
        # Use snapshot_time as ID
        snapshot_id = snapshot['snapshot_time']
        snapshot['id'] = snapshot_id
        
        # Always insert a new snapshot (use snapshot_time as unique ID)
        self.insert(snapshot)
        
        return snapshot_id
    
    def delete_old_snapshots(self, keep_count: int = 30) -> int:
        """Delete old snapshots, keeping the most recent ones.
        
        Args:
            keep_count: Number of recent snapshots to keep
            
        Returns:
            Number of snapshots deleted
        """
        snapshots = self.find_recent(1000)  # Get all
        if len(snapshots) <= keep_count:
            return 0
        
        # Get IDs to delete (older ones)
        to_delete = snapshots[keep_count:]
        deleted = 0
        
        for s in to_delete:
            if self.delete(s.get('id', '')):
                deleted += 1
        
        return deleted
