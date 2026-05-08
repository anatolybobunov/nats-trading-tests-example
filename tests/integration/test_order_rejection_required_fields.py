import pytest

from utils.rejection_payloads import base_order_payload, drop_field
from utils.side_effects import assert_no_trade_executed, assert_positions_unchanged
from src.enums import OrderStatus
from src.nts.subjects import ORDERS_CREATE_SUBJECT, ORDERS_REJECTED_SUBJECT


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("mutation", "field_name"),
    [
        pytest.param(drop_field("symbol"), "symbol", id="missing_symbol"),
        pytest.param(drop_field("side"), "side", id="missing_side"),
        pytest.param(drop_field("quantity"), "quantity", id="missing_quantity"),
        pytest.param(drop_field("price"), "price", id="missing_price"),
    ],
)
async def test_order_rejected_when_field_missing(
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

    # Wait for the rejection message
    rejected = await message_collector.wait_for(
        ORDERS_REJECTED_SUBJECT,
        timeout=5.0,
        predicate=lambda m: m.json_payload().get("order_id") == payload["order_id"],
    )
    rejected_payload = rejected.json_payload()

    assert rejected_payload["status"] == OrderStatus.REJECTED
    assert rejected_payload.get("reason"), f"Expected a reason for missing field '{field_name}'"

    # --- side-effect checks ---

    await assert_no_trade_executed(
        message_collector,
        order_id=payload["order_id"],
    )

    await assert_positions_unchanged(
        db_client,
        expected=positions_before,
    )
