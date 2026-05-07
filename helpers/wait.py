from typing import TypeVar
from uuid import UUID

from pydantic import BaseModel

from src.messaging.collector import MessageCollector
from src.messaging.models import OrderConfirmed, TradeExecuted
from src.messaging.subjects import ORDERS_CONFIRMED_SUBJECT, TRADES_EXECUTED_SUBJECT

ModelT = TypeVar("ModelT", bound=BaseModel)


async def _wait_for_typed_message(
    collector: MessageCollector,
    *,
    subject: str,
    order_id: UUID,
    model_type: type[ModelT],
    timeout: float = 5.0,
) -> ModelT:
    message = await collector.wait_for(
        subject,
        timeout=timeout,
        predicate=lambda item: item.json_payload().get("order_id") == str(order_id),
    )
    payload = message.json_payload()
    return model_type.model_validate(payload)


async def wait_for_order_confirmed(
    collector: MessageCollector,
    *,
    order_id: UUID,
    timeout: float = 5.0,
) -> OrderConfirmed:
    return await _wait_for_typed_message(
        collector,
        subject=ORDERS_CONFIRMED_SUBJECT,
        order_id=order_id,
        model_type=OrderConfirmed,
        timeout=timeout,
    )


async def wait_for_trade_executed(
    collector: MessageCollector,
    *,
    order_id: UUID,
    timeout: float = 5.0,
) -> TradeExecuted:
    return await _wait_for_typed_message(
        collector,
        subject=TRADES_EXECUTED_SUBJECT,
        order_id=order_id,
        model_type=TradeExecuted,
        timeout=timeout,
    )
