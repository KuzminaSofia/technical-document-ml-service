from __future__ import annotations

import ssl
from collections.abc import Iterator
from contextlib import contextmanager

import pika
from pika.adapters.blocking_connection import BlockingChannel, BlockingConnection

from technical_document_ml_service.core.config import app_settings
from technical_document_ml_service.messaging.contracts import PredictionTaskMessage


def build_connection_parameters() -> pika.ConnectionParameters:
    """собрать параметры подключения к RabbitMQ"""
    credentials = pika.PlainCredentials(
        username=app_settings.rabbitmq_user,
        password=app_settings.rabbitmq_password,
    )

    ssl_options = None
    if app_settings.rabbitmq_ssl_enabled:
        ssl_context = ssl.create_default_context()
        ssl_options = pika.SSLOptions(ssl_context)

    return pika.ConnectionParameters(
        host=app_settings.rabbitmq_host,
        port=app_settings.rabbitmq_port,
        virtual_host=app_settings.rabbitmq_virtual_host,
        credentials=credentials,
        heartbeat=app_settings.rabbitmq_heartbeat,
        blocked_connection_timeout=app_settings.rabbitmq_blocked_connection_timeout,
        ssl_options=ssl_options,
    )


@contextmanager
def open_rabbitmq_connection() -> Iterator[BlockingConnection]:
    """открыть соединение с RabbitMQ"""
    connection = pika.BlockingConnection(build_connection_parameters())
    try:
        yield connection
    finally:
        if connection.is_open:
            connection.close()


@contextmanager
def open_rabbitmq_channel() -> Iterator[BlockingChannel]:
    """открыть канал RabbitMQ поверх соединения"""
    with open_rabbitmq_connection() as connection:
        channel = connection.channel()
        try:
            yield channel
        finally:
            if channel.is_open:
                channel.close()


def declare_prediction_queue(
    channel: BlockingChannel,
    *,
    queue_name: str | None = None,
) -> str:
    """объявить очередь задач предсказания"""
    resolved_queue_name = queue_name or app_settings.rabbitmq_queue_name

    channel.queue_declare(
        queue=resolved_queue_name,
        durable=True,
    )

    return resolved_queue_name


def configure_consumer_qos(
    channel: BlockingChannel,
    *,
    prefetch_count: int | None = None,
) -> None:
    """настроить QoS для consumer-а"""
    channel.basic_qos(
        prefetch_count=prefetch_count or app_settings.rabbitmq_prefetch_count,
    )


def publish_prediction_task(
    message: PredictionTaskMessage,
    *,
    queue_name: str | None = None,
) -> None:
    """опубликовать задачу предсказания в RabbitMQ"""
    with open_rabbitmq_channel() as channel:
        resolved_queue_name = declare_prediction_queue(
            channel,
            queue_name=queue_name,
        )

        channel.basic_publish(
            exchange="",
            routing_key=resolved_queue_name,
            body=message.to_bytes(),
            properties=pika.BasicProperties(
                content_type="application/json",
                delivery_mode=2,
                timestamp=int(message.timestamp.timestamp()),
            ),
        )