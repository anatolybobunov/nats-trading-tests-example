"""
Temporary debug helpers for investigating automated test behavior.
This file contains utility code that is used only for debugging and troubleshooting test runs.
It helps inspect NATS messages and pg state while tests are running.
The code here is not part of the main application logic and may be removed or changed later.
"""

from dataclasses import dataclass

import structlog

from src.pg.models import OrderRow, PositionRow
from src.pg.pg_client import PostgresClient
from src.nts.collector import MessageCollector
from src.nts.models import NatsMessage

logger = structlog.get_logger(__name__)


@dataclass(frozen=True)
class DebugDbState:
    orders: list[OrderRow]
    positions: list[PositionRow]


async def dump_any_nats_messages(message_collector: MessageCollector) -> dict[str, list[NatsMessage]]:
    logger.info("dumping any NATS messages for debugging")
    messages_by_subject = await message_collector.drain_all()
    for subject, messages in messages_by_subject.items():
        logger.info("NATS subject messages", subject=subject, messages=[message.model_dump() for message in messages])
    logger.info(
        "dumped NATS messages for debugging",
        subjects=list(messages_by_subject.keys()),
        total_count=sum(len(messages) for messages in messages_by_subject.values()),
    )
    return messages_by_subject


async def dump_any_db_state(db_client: PostgresClient) -> DebugDbState:
    logger.info("dumping any DB state for debugging")
    orders = await db_client.fetch_all_orders()
    positions = await db_client.fetch_all_positions()
    logger.info("DB orders snapshot", orders=[order.model_dump() for order in orders])
    logger.info("DB positions snapshot", positions=[position.model_dump() for position in positions])
    logger.info(
        "dumped DB state for debugging",
        orders_count=len(orders),
        positions_count=len(positions),
    )
    return DebugDbState(orders=orders, positions=positions)
