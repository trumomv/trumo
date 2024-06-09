import math
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator

from models.base_model import MAX_FLOAT


class UserCreate(BaseModel):
    name: str = Field(..., min_length=3, max_length=100)
    balance: Decimal = Field(0.0, ge=0, le=MAX_FLOAT, decimal_places=2)


class UserOut(BaseModel):
    id: int
    name: str
    balance: Decimal

    class Config:
        orm_mode = True
