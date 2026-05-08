from uuid import UUID

import pytest
from pydantic import ValidationError

from utils.rejection_payloads import base_order_payload
from src.enums import OrderStatus
from src.nts.models import OrderConfirmed, OrderCreate, TradeExecuted
from src.nts.subjects import (
    ORDERS_CONFIRMED_SUBJECT,
    ORDERS_CREATE_SUBJECT,
    ORDERS_REJECTED_SUBJECT,
    TRADES_EXECUTED_SUBJECT,
)


def test_order_create_message_validates_against_model():
    """Verify that the helper base_order_payload produces a valid OrderCreate."""
    payload = base_order_payload()
    # noinspection PyArgumentList
    validated = OrderCreate(**payload)
    assert validated.quantity > 0
    assert validated.price > 0


@pytest.mark.asyncio
async def test_order_confirmed_message_contract(
    nats_client,
    message_collector,
) -> None:
    """The orders.confirmed payload must deserialise into OrderConfirmed."""
    payload = base_order_payload()
    await nats_client.publish_json(ORDERS_CREATE_SUBJECT, payload)

    # The Order Service should publish to orders.confirmed for a valid order
    confirmed_raw = await message_collector.wait_for(
        ORDERS_CONFIRMED_SUBJECT,
        timeout=5.0,
        predicate=lambda m: m.json_payload().get("order_id") == payload["order_id"],
    )
    confirmed_payload = confirmed_raw.json_payload()

    try:
        validated = OrderConfirmed.model_validate(confirmed_payload)
    except ValidationError as exc:
        pytest.fail(f"orders.confirmed payload does not match schema: {exc}")

    assert validated.status == OrderStatus.CONFIRMED
    assert validated.reason is None
    # Must be a valid UUID
    assert UUID(str(validated.order_id))


@pytest.mark.asyncio
async def test_rejected_message_contract(
    nats_client,
    message_collector,
) -> None:
    """The orders.rejected payload must deserialise into OrderConfirmed."""
    payload = base_order_payload()
    payload["quantity"] = 0  # trigger rejection

    await nats_client.publish_json(ORDERS_CREATE_SUBJECT, payload)

    rejected_raw = await message_collector.wait_for(
        ORDERS_REJECTED_SUBJECT,
        timeout=5.0,
        predicate=lambda m: m.json_payload().get("order_id") == payload["order_id"],
    )
    rejected_payload = rejected_raw.json_payload()

    try:
        validated = OrderConfirmed.model_validate(rejected_payload)
    except ValidationError as exc:
        pytest.fail(f"orders.rejected payload does not match schema: {exc}")

    assert validated.status == OrderStatus.REJECTED
    assert validated.reason is not None  # should explain *why*


@pytest.mark.asyncio
async def test_trade_executed_message_contract(
    nats_client,
    message_collector,
) -> None:
    """The trades.executed payload must deserialise into TradeExecuted."""
    payload = base_order_payload()

    await nats_client.publish_json(ORDERS_CREATE_SUBJECT, payload)

    await message_collector.wait_for(
        ORDERS_CONFIRMED_SUBJECT,
        timeout=5.0,
        predicate=lambda m: m.json_payload().get("order_id") == payload["order_id"],
    )

    trade_raw = await message_collector.wait_for(
        TRADES_EXECUTED_SUBJECT,
        timeout=5.0,
        predicate=lambda m: m.json_payload().get("order_id") == payload["order_id"],
    )
    trade_payload = trade_raw.json_payload()

    # Validate the model
    try:
        validated = TradeExecuted.model_validate(trade_payload)
    except ValidationError as exc:
        pytest.fail(f"trades.executed payload does not match schema: {exc}")

    assert validated.order_id == UUID(payload["order_id"])
    assert validated.symbol == payload["symbol"]
    assert validated.quantity == payload["quantity"]
