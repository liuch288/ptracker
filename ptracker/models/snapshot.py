"""Snapshot data model for portfolio state capture."""

from datetime import datetime
from typing import Dict, Any, List, Optional
from pydantic import BaseModel


class HoldingSnapshot(BaseModel):
    """Holding-level snapshot data.
    
    Extends existing Holding with current market data.
    """
    # Original Holding fields
    asset: str
    account: str
    direction: str
    quantity: float
    avg_cost: float
    total_invested: float
    currency: str
    first_open_date: str
    last_updated: str
    note: str = ""
    status: str = "active"
    
    # Current market data
    current_price: float
    market_value: float
    unrealized_pnl: float
    return_pct: float


class AccountSnapshot(BaseModel):
    """Account-level snapshot data."""
    name: str
    currency: str
    type: str
    description: str
    
    # Flow totals
    total_deposit: float
    total_withdrawal: float
    net_deposit: float
    
    # Position totals
    total_market_value: float
    total_cost: float
    total_unrealized_pnl: float
    
    # Holdings in this account
    holdings: List[HoldingSnapshot]


class PortfolioSnapshot(BaseModel):
    """Portfolio-level snapshot data."""
    version: str = "1.0"
    snapshot_time: str  # ISO format datetime
    
    # Flow totals
    total_deposit: float
    total_withdrawal: float
    net_deposit: float
    
    # Position totals
    total_market_value: float
    total_cost: float
    total_unrealized_pnl: float
    total_realized_pnl: float
    total_return_pct: float
    
    # Counts
    account_count: int
    holding_count: int
    
    # Currency breakdown
    currency_breakdown: Dict[str, float]  # currency -> market_value
    
    # Per-account snapshots
    accounts: List[AccountSnapshot]
    
    # Metadata
    price_source: str = "yfinance"
    price_timestamp: Optional[str] = None
    currency_rates: Dict[str, float] = {}  # currency -> rate to base currency
    
    class Config:
        json_schema_extra = {
            "example": {
                "version": "1.0",
                "snapshot_time": "2024-01-15T10:30:00",
                "total_deposit": 100000.0,
                "total_withdrawal": 0.0,
                "net_deposit": 100000.0,
                "total_market_value": 105000.0,
                "total_cost": 100000.0,
                "total_unrealized_pnl": 5000.0,
                "total_realized_pnl": 0.0,
                "total_return_pct": 5.0,
                "account_count": 2,
                "holding_count": 5,
                "currency_breakdown": {"USD": 80000.0, "HKD": 20000.0},
                "accounts": [],
                "price_source": "yfinance",
                "price_timestamp": "2024-01-15T10:30:00",
                "currency_rates": {"USD": 1.0, "HKD": 0.128}
            }
        }
