"""Transaction data model."""

from datetime import datetime as dt
from typing import Literal
from pydantic import BaseModel, field_validator


class Transaction(BaseModel):
    """Transaction record for buy/sell trades."""
    
    id: str
    datetime: dt
    type: Literal["buy", "sell"]
    action: Literal["open", "close"]
    direction: Literal["long", "short"]
    asset: str
    quantity: float
    price: float
    currency: str
    fee: float = 0.0
    account: str
    note: str = ""
    
    @field_validator("quantity")
    @classmethod
    def validate_quantity_sign(cls, v: float, info) -> float:
        """Ensure quantity sign matches type, action, and direction.
        
        Rules:
        - buy + open + long → positive
        - buy + close + short → positive
        - sell + close + long → negative
        - sell + open + short → negative
        """
        values = info.data
        if not values:
            return v
            
        tx_type = values.get("type")
        action = values.get("action")
        direction = values.get("direction")
        
        # Determine expected sign
        if tx_type == "buy" and action == "open" and direction == "long":
            expected_positive = True
        elif tx_type == "buy" and action == "close" and direction == "short":
            expected_positive = True
        elif tx_type == "sell" and action == "close" and direction == "long":
            expected_positive = False
        elif tx_type == "sell" and action == "open" and direction == "short":
            expected_positive = False
        else:
            # Invalid combination, let it pass for now
            return v
        
        # Check if sign matches expectation
        if expected_positive and v < 0:
            raise ValueError(
                f"Quantity must be positive for {tx_type}/{action}/{direction}"
            )
        elif not expected_positive and v > 0:
            raise ValueError(
                f"Quantity must be negative for {tx_type}/{action}/{direction}"
            )
        
        return v
