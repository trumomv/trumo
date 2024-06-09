from decimal import Decimal

from pydantic import BaseModel, field_validator, Field
from typing import Optional

from models import TransactionType
from models.base_model import MAX_FLOAT


class TransactionBase(BaseModel):
    amount: Decimal = Field(..., ge=0.01, le=MAX_FLOAT, decimal_places=2)
    sender_id: int = Field(..., ge=1)


class TransactionCreate(TransactionBase):
    receiver_id: int = Field(..., ge=1)


class WithdrawCreate(TransactionBase):
    pass


class TransactionOut(BaseModel):
    id: int
    sender_id: Optional[int]
    receiver_id: Optional[int]
    type: TransactionType
    amount: Decimal

    class Config:
        orm_mode = True
