"""Cash flow data model."""

from datetime import datetime
from typing import Literal
from pydantic import BaseModel


class CashFlow(BaseModel):
    """Cash flow record for deposits and withdrawals."""
    
    id: str
    datetime: datetime
    type: Literal["deposit", "withdrawal"]
    account: str
    amount: float
    currency: str
    note: str = ""
