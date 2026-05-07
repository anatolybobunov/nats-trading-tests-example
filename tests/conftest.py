import logger
import os
import structlog
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

log = structlog.get_logger(__name__)


def pytest_configure(config: pytest.Config) -> None:
    logger.configure_logging()


@pytest_asyncio.fixture
async def nats_client() -> AsyncIterator[NatsClient]:
    nats_url = os.getenv("NATS_URL", "nats://localhost:4222")
    log.info("creating NATS client", url=nats_url)
    client = await NatsClient.connect([nats_url])
    log.info("NATS client connected", url=nats_url)
    try:
        yield client
    finally:
        log.info("closing NATS client", url=nats_url)
        await client.close()


@pytest_asyncio.fixture
async def db_client() -> AsyncIterator[PostgresClient]:
    dsn = os.getenv(
        "POSTGRES_DSN",
        "postgresql://testuser:testpass@localhost:5432/trading",
    )
    log.info("connecting to PostgreSQL", dsn=dsn)
    client = await PostgresClient.connect(dsn)
    log.info("PostgreSQL client connected")
    try:
        yield client
    finally:
        log.info("closing PostgreSQL client")
        await client.close()


@pytest_asyncio.fixture
async def message_collector(nats_client: NatsClient) -> AsyncIterator[MessageCollector]:
    log.info("starting message collector")
    collector = MessageCollector(nats_client)
    await collector.start(
        [
            ORDERS_CONFIRMED_SUBJECT,
            ORDERS_REJECTED_SUBJECT,
            TRADES_EXECUTED_SUBJECT,
        ]
    )
    log.info("message collector started")
    try:
        yield collector
    finally:
        log.info("stopping message collector")
        await collector.stop()


@pytest_asyncio.fixture(autouse=True)
async def _cleanup_db(db_client: PostgresClient) -> AsyncIterator[None]:
    log.info("cleaning up database before test")
    yield
    log.info("cleaning up database after test")
    await db_client.execute("DELETE FROM orders")
    await db_client.execute("DELETE FROM positions")
