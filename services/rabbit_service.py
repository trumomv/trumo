import os

import pika
from pika.adapters.blocking_connection import BlockingConnection
from pydantic.v1 import BaseSettings


class RabbitMQConfig(BaseSettings):
    host: str = os.environ.get("RABBITMQ_HOST")
    port: int = int(os.environ.get("RABBITMQ_PORT"))
    username: str = os.environ.get("RABBITMQ_USERNAME")
    password: str = os.environ.get("RABBITMQ_PASSWORD")


rabbitmq_config = RabbitMQConfig()


class RabbitMQConnection:
    def __init__(self, config: RabbitMQConfig):
        credentials = pika.PlainCredentials(username=config.username, password=config.password)
        self.connection = BlockingConnection(
            pika.ConnectionParameters(host=config.host, port=config.port, credentials=credentials)
        )
        self.channel = self.connection.channel()

    def close(self):
        self.connection.close()


def get_rabbitmq_connection(config: RabbitMQConfig = rabbitmq_config) -> RabbitMQConnection:
    return RabbitMQConnection(config)
