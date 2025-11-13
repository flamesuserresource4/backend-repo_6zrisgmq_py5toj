"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.
These schemas are used for data validation in your application.

Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name:
- User -> "user" collection
- Product -> "product" collection
- BlogPost -> "blogs" collection
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, Literal

class Bet(BaseModel):
    """
    Bets collection schema
    Collection name: "bet" (lowercase of class name)
    """
    period_id: str = Field(..., description="Game period identifier")
    bet_type: Literal['big_small', 'number', 'color'] = Field(..., description="Type of bet")
    selection: str = Field(..., description="Selected outcome, e.g., big/small, 0-9, red/green/violet")
    amount: float = Field(..., gt=0, description="Bet amount")
    source: Optional[str] = Field(None, description="Optional source or player identifier")

    @field_validator('selection')
    @classmethod
    def validate_selection(cls, v: str) -> str:
        v = v.lower().strip()
        return v

class User(BaseModel):
    name: str
    email: str
    address: str
    age: Optional[int] = None
    is_active: bool = True

class Product(BaseModel):
    title: str
    description: Optional[str] = None
    price: float
    category: str
    in_stock: bool = True
