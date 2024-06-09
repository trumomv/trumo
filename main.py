import logging
import os
import time
from typing import List

from fastapi import FastAPI, Depends, HTTPException
from pika import exceptions
from pika.spec import BasicProperties
from sqlalchemy.orm import Session

from db import get_db
from models import TransactionType
from pydantic_models.transaction import TransactionOut, TransactionCreate, WithdrawCreate
from services.rabbit_service import RabbitMQConnection, get_rabbitmq_connection
from services.redis_service import RedisService, get_redis_service
from services.transaction_service import TransactionService
from services.user_service import UserService
from pydantic_models.user import UserOut, UserCreate

app = FastAPI()


def setup_rabbitmq_with_retry(retries=5, delay=5):
    rabbitmq = None
    queue_name = os.environ.get("RABBITMQ_QUEUE")
    for _ in range(retries):
        try:
            rabbitmq = get_rabbitmq_connection()
            rabbitmq.channel.exchange_declare(exchange=queue_name, exchange_type="direct", durable=True)
            rabbitmq.channel.queue_declare(queue=queue_name, durable=True)
            rabbitmq.channel.queue_bind(exchange=queue_name, queue=queue_name, routing_key="")
            break
        except exceptions.AMQPConnectionError as e:
            logging.warning(f"RabbitMQ connection failed: {e}. Retrying in {delay} seconds...")
            time.sleep(delay)
    if not rabbitmq:
        logging.error("Failed to connect to RabbitMQ after several attempts.")
        raise ConnectionError("RabbitMQ setup failed")
    return rabbitmq


@app.on_event("startup")
def setup_rabbitmq():
    setup_rabbitmq_with_retry()


@app.post("/users/", response_model=UserOut)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    try:
        db_user = UserService.create_user(db, user)
        db.commit()
    except Exception as e:
        logging.exception(e)
        raise HTTPException(status_code=400, detail="Unable to create user, please try again later")

    return db_user


@app.get("/users/", response_model=List[UserOut])
def get_users(db: Session = Depends(get_db)):
    # if there are a lot of users then paging is needed
    return UserService.get_users(db)


@app.post("/transactions/transfer", response_model=TransactionOut)
def transfer_money(transaction: TransactionCreate, db: Session = Depends(get_db)):
    sender = UserService.fetch(db, transaction.sender_id)
    receiver = UserService.fetch(db, transaction.receiver_id)
    if not sender or not receiver:
        raise HTTPException(status_code=404, detail="User not found")

    if sender.balance < transaction.amount:
        raise HTTPException(status_code=404, detail="Insufficient balance")

    try:
        db_transaction = TransactionService.transfer_money(db, sender, receiver, transaction.amount, TransactionType.TRANSFER)
        db.commit()
    except Exception as e:
        logging.exception(e)
        raise HTTPException(status_code=400, detail="Unable to transfer money, please try again later")

    return db_transaction


@app.post("/transactions/withdraw")
def withdraw_money(transaction: WithdrawCreate, rabbitmq: RabbitMQConnection = Depends(get_rabbitmq_connection)):
    message = transaction.json()
    queue_name = os.environ.get("RABBITMQ_QUEUE")

    try:
        rabbitmq.channel.basic_publish(
            exchange=queue_name,
            routing_key="",
            body=message,
            properties=BasicProperties(
                delivery_mode=2
            )
        )
    except exceptions.AMQPError as e:
        logging.error(f"Failed to publish message: {e}")
        raise HTTPException(status_code=500, detail="Failed to publish message")

    return {"message": "Withdrawal request submitted"}


@app.get("/transactions/", response_model=List[TransactionOut])
async def get_all_transactions(db: Session = Depends(get_db), redis_service: RedisService = Depends(get_redis_service)):
    return await TransactionService.get_all_transactions(db, redis_service)


@app.get("/transactions/{user_id}", response_model=List[TransactionOut])
async def get_transactions_for_user(user_id: int, db: Session = Depends(get_db), redis_service: RedisService = Depends(get_redis_service)):
    return await TransactionService.get_user_transactions(db, redis_service, user_id)


@app.get("/transactions/{user_id}/{transaction_type}", response_model=List[TransactionOut])
async def get_transactions_for_user(user_id: int, transaction_type: TransactionType, db: Session = Depends(get_db), redis_service: RedisService = Depends(get_redis_service)):
    return await TransactionService.get_user_transactions(db, redis_service, user_id, transaction_type)


@app.get("/transactions/history/{user1_id}/{user2_id}", response_model=List[TransactionOut])
async def get_transaction_history(user1_id: int, user2_id: int, db: Session = Depends(get_db), redis_service: RedisService = Depends(get_redis_service)):
    return await TransactionService.get_transactions_between_users(db, redis_service, user1_id, user2_id)
