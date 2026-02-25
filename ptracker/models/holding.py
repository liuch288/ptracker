"""Holding data model."""

from typing import Literal
from pydantic import BaseModel


class Holding(BaseModel):
    """Current active position with non-zero quantity."""
    
    asset: str
    account: str
    direction: Literal["long", "short"]
    quantity: float
    avg_cost: float
    total_invested: float
    currency: str
    first_open_date: str  # YYYY-MM-DD
    last_updated: str  # YYYY-MM-DD
    note: str = ""
    status: Literal["active"] = "active"
