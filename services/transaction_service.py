from decimal import Decimal
from typing import List

from sqlalchemy.orm import Session

from errors.withdraw_error import WithdrawError
from models import MoneyTransaction, TransactionType, User
from pydantic_models.transaction import WithdrawCreate
from services.redis_service import RedisService
from services.user_service import UserService


class TransactionService:
    @classmethod
    def transfer_money(cls, db: Session, sender: User, receiver: User, amount: Decimal, transfer_type: TransactionType) -> MoneyTransaction:
        sender.balance -= amount
        receiver.balance += amount

        db_transaction = MoneyTransaction(
            sender_id=sender.id,
            receiver_id=receiver.id,
            amount=amount,
            type=transfer_type
        )

        db.add(db_transaction)

        return db_transaction

    @classmethod
    def withdraw_money(cls, db: Session, transaction: WithdrawCreate):
        user = UserService.fetch(db, transaction.sender_id)

        if not user:
            raise WithdrawError("User not found")
        if user.balance < transaction.amount:
            raise WithdrawError("Insufficient balance")

        user.balance -= Decimal(transaction.amount)

        db_transaction = MoneyTransaction(
            sender_id=transaction.sender_id,
            amount=transaction.amount,
            type=TransactionType.WITHDRAWAL
        )

        db.add(db_transaction)

        return db_transaction

    @classmethod
    async def get_all_transactions(cls, db: Session, redis_service: RedisService) -> List[dict]:
        await redis_service.delete("all_transactions")
        transactions_cache = await redis_service.get("all_transactions")
        if transactions_cache:
            return transactions_cache

        transactions = db.query(MoneyTransaction).all()
        transactions_dicts = [transaction.to_dict() for transaction in transactions]
        await redis_service.set("all_transactions", transactions_dicts)
        return transactions_dicts

    @classmethod
    async def get_user_transactions(cls, db: Session, redis_service: RedisService, user_id: int, transaction_type: TransactionType = None):
        transactions = await cls.get_all_transactions(db, redis_service)
        if not transactions:
            return []

        filtered_transactions = [t for t in transactions if t['sender_id'] == user_id or t['receiver_id'] == user_id]
        if transaction_type:
            filtered_transactions = [t for t in filtered_transactions if t['type'] == transaction_type.value]
        return filtered_transactions

    @classmethod
    async def get_transactions_between_users(cls, db: Session, redis_service: RedisService, user1_id: int, user2_id: int):
        transactions = await cls.get_all_transactions(db, redis_service)
        if not transactions:
            return []

        filtered_transactions = [
            t for t in transactions
            if (
                       (t['sender_id'] == user1_id and t['receiver_id'] == user2_id) or
                       (t['sender_id'] == user2_id and t['receiver_id'] == user1_id)
               ) and t['type'] == TransactionType.TRANSFER
        ]
        return filtered_transactions
