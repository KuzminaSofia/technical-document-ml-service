from __future__ import annotations

import logging
import ssl
import threading
from collections.abc import Iterator
from contextlib import contextmanager

import pika
from pika.adapters.blocking_connection import BlockingChannel, BlockingConnection

from technical_document_ml_service.core.config import app_settings
from technical_document_ml_service.messaging.contracts import PredictionTaskMessage

LOGGER = logging.getLogger("technical_document_ml_service.messaging.rabbitmq")


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
    """открыть одноразовое соединение с RabbitMQ (для consumer-а / воркера)"""
    connection = pika.BlockingConnection(build_connection_parameters())
    try:
        yield connection
    finally:
        if connection.is_open:
            connection.close()


@contextmanager
def open_rabbitmq_channel() -> Iterator[BlockingChannel]:
    """открыть одноразовый канал RabbitMQ поверх соединения (для consumer-а / воркера)"""
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
    """объявить очередь задач предсказания (идемпотентно)"""
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


class _PersistentPublisher:
    """переиспользуемый publisher с thread-local соединением

    pika.BlockingConnection не является потокобезопасным, поэтому каждый поток
    получает свое собственное долгоживущее соединение + канал
    при разрыве соединения выполняется один reconnect и повтор публикации
    """

    def __init__(self) -> None:
        self._local = threading.local()

    def _get_channel(self) -> BlockingChannel:
        connection: BlockingConnection | None = getattr(self._local, "connection", None)
        channel: BlockingChannel | None = getattr(self._local, "channel", None)

        if connection is None or not connection.is_open:
            LOGGER.debug("RabbitMQ publisher: открываем новое соединение (поток %s)", threading.current_thread().name)
            connection = pika.BlockingConnection(build_connection_parameters())
            self._local.connection = connection
            channel = None

        if channel is None or not channel.is_open:
            channel = connection.channel()
            # объявляем очередь при создании канала — гарантируем её существование
            declare_prediction_queue(channel)
            self._local.channel = channel

        return channel

    def _reset(self) -> None:
        """сбросить соединение и канал текущего потока"""
        try:
            conn: BlockingConnection | None = getattr(self._local, "connection", None)
            if conn is not None and conn.is_open:
                conn.close()
        except Exception:
            pass
        self._local.connection = None
        self._local.channel = None

    def publish(
        self,
        message: PredictionTaskMessage,
        *,
        queue_name: str | None = None,
    ) -> None:
        resolved_queue = queue_name or app_settings.rabbitmq_queue_name
        body = message.to_bytes()
        properties = pika.BasicProperties(
            content_type="application/json",
            delivery_mode=2,
            timestamp=int(message.timestamp.timestamp()),
        )

        try:
            channel = self._get_channel()
            channel.basic_publish(
                exchange="",
                routing_key=resolved_queue,
                body=body,
                properties=properties,
            )
        except Exception:
            # соединение разорвано — сбросить состояние и сделать одну попытку переподключения
            LOGGER.warning(
                "RabbitMQ publisher: соединение разорвано, переподключаемся (поток %s)",
                threading.current_thread().name,
            )
            self._reset()
            channel = self._get_channel()
            channel.basic_publish(
                exchange="",
                routing_key=resolved_queue,
                body=body,
                properties=properties,
            )


_publisher = _PersistentPublisher()


def publish_prediction_task(
    message: PredictionTaskMessage,
    *,
    queue_name: str | None = None,
) -> None:
    """опубликовать задачу предсказания через persistent publisher"""
    _publisher.publish(message, queue_name=queue_name)