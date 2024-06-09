from sqlalchemy import Column, Integer, String, DateTime, func, Numeric
from models import BaseModel


class User(BaseModel):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100))
    balance = Column(Numeric(precision=12, scale=2), default=0.0)
    created_at = Column(DateTime, default=func.now())
