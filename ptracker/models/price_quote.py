"""Price quote data model."""

from datetime import datetime
from pydantic import BaseModel


class PriceQuote(BaseModel):
    """Current market price for an asset."""
    
    asset: str
    price: float
    currency: str
    timestamp: datetime
