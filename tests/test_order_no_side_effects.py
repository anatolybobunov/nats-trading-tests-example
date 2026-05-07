import pytest

from helpers.rejection_payloads import base_order_payload
from helpers.side_effects import assert_no_trade_executed, assert_positions_unchanged
from src.messaging.subjects import ORDERS_CREATE_SUBJECT, ORDERS_REJECTED_SUBJECT


@pytest.mark.asyncio
async def test_rejected_order_does_not_create_trade(
    nats_client,
    db_client,
    message_collector,
) -> None:
    """After an order is rejected, no *trades.executed* message should appear."""
    payload = base_order_payload()
    payload["quantity"] = -1  # trigger a rejection

    await nats_client.publish_json(ORDERS_CREATE_SUBJECT, payload)

    # Wait for the rejection
    rejected = await message_collector.wait_for(
        ORDERS_REJECTED_SUBJECT,
        timeout=5.0,
        predicate=lambda m: m.json_payload().get("order_id") == payload["order_id"],
    )
    reported_order_id = rejected.json_payload().get("order_id", payload["order_id"])

    await assert_no_trade_executed(
        message_collector,
        order_id=reported_order_id if isinstance(reported_order_id, str) else payload["order_id"],
    )


@pytest.mark.asyncio
async def test_rejected_order_does_not_change_positions(
    nats_client,
    db_client,
    message_collector,
) -> None:
    """After an order is rejected, the positions table must be unchanged."""
    payload = base_order_payload()
    payload["quantity"] = -1  # trigger a rejection

    positions_before = await db_client.fetch_all_positions()

    await nats_client.publish_json(ORDERS_CREATE_SUBJECT, payload)

    await message_collector.wait_for(
        ORDERS_REJECTED_SUBJECT,
        timeout=5.0,
        predicate=lambda m: m.json_payload().get("order_id") == payload["order_id"],
    )

    await assert_positions_unchanged(
        db_client,
        expected=positions_before,
    )
