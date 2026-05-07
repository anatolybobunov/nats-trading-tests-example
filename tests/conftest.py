import logger
import os
from collections.abc import AsyncIterator

import pytest
import pytest_asyncio

from src.messaging.nats_client import NatsClient
from src.messaging.collector import MessageCollector
from src.messaging.subjects import (
    ORDERS_CONFIRMED_SUBJECT,
    ORDERS_REJECTED_SUBJECT,
    TRADES_EXECUTED_SUBJECT,
)
from src.database.pg_client import PostgresClient


def pytest_configure(config: pytest.Config) -> None:
    logger.configure_logging()


@pytest_asyncio.fixture
async def nats_client() -> AsyncIterator[NatsClient]:
    nats_url = os.getenv("NATS_URL", "nats://localhost:4222")
    client = await NatsClient.connect([nats_url])
    try:
        yield client
    finally:
        await client.close()


@pytest_asyncio.fixture
async def db_client() -> AsyncIterator[PostgresClient]:
    dsn = os.getenv(
        "POSTGRES_DSN",
        "postgresql://testuser:testpass@localhost:5432/trading",
    )
    client = await PostgresClient.connect(dsn)
    try:
        yield client
    finally:
        await client.close()


@pytest_asyncio.fixture
async def message_collector(nats_client: NatsClient) -> AsyncIterator[MessageCollector]:
    collector = MessageCollector(nats_client)
    await collector.start(
        [
            ORDERS_CONFIRMED_SUBJECT,
            ORDERS_REJECTED_SUBJECT,
            TRADES_EXECUTED_SUBJECT,
        ]
    )
    try:
        yield collector
    finally:
        await collector.stop()


@pytest_asyncio.fixture(autouse=True)
async def _cleanup_db(db_client: PostgresClient) -> AsyncIterator[None]:
    yield
    await db_client.execute("DELETE FROM orders")
    await db_client.execute("DELETE FROM positions")
