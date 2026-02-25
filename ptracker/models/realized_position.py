"""Realized position data model."""

from typing import Literal
from pydantic import BaseModel


class RealizedPosition(BaseModel):
    """Historical closed position summary with calculated P&L."""
    
    id: str
    asset: str
    account: str
    direction: Literal["long", "short"]
    first_open_date: str  # YYYY-MM-DD
    last_close_date: str  # YYYY-MM-DD
    holding_days: int
    total_quantity: float
    total_invested: float
    total_proceeds: float
    total_fees: float
    realized_pnl: float
    return_pct: float
    note: str = ""
    status: Literal["closed"] = "closed"
