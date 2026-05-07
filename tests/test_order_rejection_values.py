import pytest

from helpers.rejection_payloads import base_order_payload, set_field
from helpers.side_effects import assert_no_trade_executed, assert_positions_unchanged
from src.enums import OrderStatus
from src.messaging.subjects import ORDERS_CREATE_SUBJECT, ORDERS_REJECTED_SUBJECT


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("mutation", "field_name"),
    [
        pytest.param(set_field("quantity", 0), "quantity", id="zero_quantity"),
        pytest.param(set_field("quantity", -1), "quantity", id="negative_quantity"),
        pytest.param(set_field("price", 0), "price", id="zero_price"),
        pytest.param(set_field("price", -10), "price", id="negative_price"),
        pytest.param(set_field("side", "HOLD"), "side", id="invalid_side"),
        pytest.param(set_field("symbol", ""), "symbol", id="empty_symbol"),
        pytest.param(set_field("symbol", "   "), "symbol", id="whitespace_symbol"),
    ],
)
async def test_order_rejected_when_field_value_invalid(
    nats_client,
    db_client,
    message_collector,
    mutation,
    field_name: str,
) -> None:
    payload = base_order_payload()
    mutation(payload)

    positions_before = await db_client.fetch_all_positions()

    await nats_client.publish_json(ORDERS_CREATE_SUBJECT, payload)

    rejected = await message_collector.wait_for(
        ORDERS_REJECTED_SUBJECT,
        timeout=5.0,
        predicate=lambda m: m.json_payload().get("order_id") == payload["order_id"],
    )
    rejected_payload = rejected.json_payload()

    assert rejected_payload["status"] == OrderStatus.REJECTED
    assert rejected_payload.get("reason"), f"Expected a reason for invalid field '{field_name}'"

    # --- side-effect checks ---

    await assert_no_trade_executed(
        message_collector,
        order_id=payload["order_id"],
    )

    await assert_positions_unchanged(
        db_client,
        expected=positions_before,
    )
