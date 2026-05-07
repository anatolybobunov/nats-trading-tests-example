import pytest

from helpers.rejection_payloads import base_order_payload
from helpers.side_effects import assert_no_trade_executed, assert_positions_unchanged
from src.enums import OrderStatus
from src.messaging.subjects import ORDERS_CREATE_SUBJECT, ORDERS_REJECTED_SUBJECT


@pytest.mark.asyncio
async def test_order_rejected_when_order_id_is_invalid_uuid(
    nats_client,
    db_client,
    message_collector,
) -> None:
    payload = base_order_payload()
    payload["order_id"] = "not-a-uuid"

    positions_before = await db_client.fetch_all_positions()

    await nats_client.publish_json(ORDERS_CREATE_SUBJECT, payload)

    # Wait for *any* rejection message — we cannot match by order_id
    # because the system may or may not echo the invalid value back.
    rejected = await message_collector.wait_for(
        ORDERS_REJECTED_SUBJECT,
        timeout=5.0,
        predicate=None,
    )
    rejected_payload = rejected.json_payload()

    assert rejected_payload["status"] == OrderStatus.REJECTED
    assert rejected_payload.get("reason"), "Expected a rejection reason when order_id is not a valid UUID"

    # --- side-effect checks ---

    # Use the order_id the system returned (if any) for the trade check.
    reported_order_id = rejected_payload.get("order_id", payload["order_id"])
    await assert_no_trade_executed(
        message_collector,
        order_id=reported_order_id if isinstance(reported_order_id, str) else payload["order_id"],
    )

    await assert_positions_unchanged(
        db_client,
        expected=positions_before,
    )
