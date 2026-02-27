"""Account data model."""

from datetime import datetime
from pydantic import BaseModel


class Account(BaseModel):
    """Brokerage or exchange account container for transactions."""
    
    id: str
    name: str
    type: str = "brokerage"
    description: str = ""
    currency: str = "USD"
    created_at: datetime
    total_deposit: float = 0.0
    total_withdrawal: float = 0.0
