import json
import logging
import os
import random
import sys

from sqlalchemy.orm import Session

from db import SessionLocal
from errors.withdraw_error import WithdrawError
from pydantic_models.transaction import WithdrawCreate
from services.rabbit_service import RabbitMQConnection, get_rabbitmq_connection
from services.transaction_service import TransactionService


def process_withdrawal(db: Session, channel, method, body):

    try:
        # Introduce a 10% chance of failure
        if random.random() < 0.1:
            raise Exception("Simulated random failure")

        transaction_data = json.loads(body)  # Parse JSON message
        transaction = WithdrawCreate(**transaction_data)  # Convert to WithdrawCreate object

        TransactionService.withdraw_money(db, transaction)
        db.commit()
        channel.basic_ack(delivery_tag=method.delivery_tag)
    except json.JSONDecodeError as e:
        logging.error(f"Failed to decode JSON: {e}")
        channel.basic_ack(delivery_tag=method.delivery_tag)
    except TypeError:
        # incorrect messages we do not process
        channel.basic_ack(delivery_tag=method.delivery_tag)
    except WithdrawError as e:
        logging.error(f"Failed to transfer money: {e}")
        # incorrect messages we do not process
        channel.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as e:
        logging.exception(e)
        channel.basic_nack(delivery_tag=method.delivery_tag)


def callback(ch, method, properties, body):
    db: Session = SessionLocal()
    process_withdrawal(db, ch, method, body)
    db.close()


def main():
    queue_name = os.environ.get("RABBITMQ_QUEUE")
    if not queue_name:
        logging.error("Environment variable RABBITMQ_QUEUE not set")
        sys.exit(1)

    rabbitmq: RabbitMQConnection = get_rabbitmq_connection()
    rabbitmq.channel.exchange_declare(exchange=queue_name, exchange_type="direct", durable=True)
    result = rabbitmq.channel.queue_declare(queue=queue_name, durable=True)
    rabbitmq.channel.queue_bind(exchange=queue_name, queue=result.method.queue)

    rabbitmq.channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=False)

    print("Waiting for withdrawal messages...")
    try:
        rabbitmq.channel.start_consuming()
    except Exception as e:
        logging.exception(f"Error during consuming: {e}")
        rabbitmq.connection.close()


if __name__ == "__main__":
    main()
