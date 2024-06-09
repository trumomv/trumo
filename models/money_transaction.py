import enum

from sqlalchemy import Column, Integer, Enum, ForeignKey, Numeric, DateTime, func
from models import BaseModel


class TransactionType(str, enum.Enum):
    TRANSFER = "transfer"
    WITHDRAWAL = "withdrawal"


class MoneyTransaction(BaseModel):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(Enum(TransactionType))
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    receiver_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    amount = Column(Numeric(precision=12, scale=2), default=0.0)
    created_at = Column(DateTime, default=func.now())
