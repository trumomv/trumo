from datetime import datetime
from decimal import Decimal

from sqlalchemy.orm import declared_attr, declarative_base
MAX_FLOAT = 999999999999
Base = declarative_base()


class BaseModel(Base):
    __abstract__ = True

    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()

    def to_dict(self):
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if isinstance(value, datetime):
                value = value.isoformat()  # Convert datetime to ISO format string
            elif isinstance(value, Decimal):
                value = str(value)  # Convert Decimal to string
            result[column.name] = value
        return result