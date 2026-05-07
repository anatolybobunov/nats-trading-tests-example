import pytest

from helpers.check import check_order_in_db, check_position_updated
from helpers.orders import place_order, prepare_order
from helpers.wait import wait_for_order_confirmed, wait_for_trade_executed
from src.enums import OrderSide, OrderStatus


@pytest.mark.asyncio
async def test_valid_buy_order_creates_order_emits_events_and_updates_position(
    nats_client,
    db_client,
    message_collector,
) -> None:
    prepared_order = prepare_order(
        symbol="AAPL",
        side=OrderSide.BUY,
        quantity=10,
    )

    await place_order(nats_client, prepared_order)

    confirmed = await wait_for_order_confirmed(
        message_collector,
        order_id=prepared_order.order_id,
    )
    executed = await wait_for_trade_executed(
        message_collector,
        order_id=prepared_order.order_id,
    )
    order_row = await check_order_in_db(
        db_client,
        order_id=prepared_order.order_id,
        expected_status=OrderStatus.CREATED,
    )
    position_row = await check_position_updated(
        db_client,
        symbol=prepared_order.symbol,
        expected_quantity=prepared_order.expected_position_quantity,
    )

    assert confirmed.order_id == prepared_order.order_id
    assert confirmed.status == OrderStatus.CONFIRMED
    assert confirmed.reason is None

    assert executed.order_id == prepared_order.order_id
    assert executed.symbol == prepared_order.symbol
    assert executed.side == prepared_order.order.side
    assert executed.quantity == prepared_order.order.quantity

    assert order_row.order_id == prepared_order.order_id
    assert order_row.symbol == prepared_order.symbol
    assert order_row.side == prepared_order.order.side
    assert order_row.quantity == prepared_order.order.quantity
    assert order_row.price == prepared_order.order.price

    assert position_row.symbol == prepared_order.symbol
    assert position_row.quantity == prepared_order.expected_position_quantity
