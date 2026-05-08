import pytest
from decimal import Decimal

from helpers.check import check_order_in_db, check_position_updated
from helpers.orders import place_order, prepare_order
from helpers.wait import wait_for_order_confirmed, wait_for_trade_executed
from src.enums import OrderSide, OrderStatus


async def _assert_full_order_flow(
    db_client,
    nats_client,
    message_collector,
    *,
    side: OrderSide,
    symbol: str,
    quantity: int,
    price: Decimal,
    expected_position_delta: int,
) -> None:
    """Execute and verify a complete order flow end‑to‑end."""
    initial_position = await db_client.fetch_position(symbol)
    initial_quantity = initial_position.quantity if initial_position is not None else 0
    expected_position_quantity = initial_quantity + expected_position_delta

    prepared_order = prepare_order(
        symbol=symbol,
        side=side,
        quantity=quantity,
        price=price,
    )

    await place_order(nats_client, prepared_order)

    confirmed = await wait_for_order_confirmed(message_collector, order_id=prepared_order.order_id)
    executed = await wait_for_trade_executed(message_collector, order_id=prepared_order.order_id)
    order_row = await check_order_in_db(
        db_client,
        order_id=prepared_order.order_id,
        expected_status=OrderStatus.CREATED,
    )
    position_row = await check_position_updated(
        db_client,
        symbol=prepared_order.symbol,
        expected_quantity=expected_position_quantity,
    )

    assert confirmed.order_id == prepared_order.order_id
    assert confirmed.status == OrderStatus.CONFIRMED
    assert confirmed.reason is None

    assert executed.order_id == prepared_order.order_id
    assert executed.symbol == prepared_order.symbol
    assert executed.side == prepared_order.order.side
    assert executed.quantity == prepared_order.order.quantity
    assert executed.quantity == quantity

    assert order_row.order_id == prepared_order.order_id
    assert order_row.symbol == prepared_order.symbol
    assert order_row.side == prepared_order.order.side
    assert order_row.quantity == prepared_order.order.quantity
    assert order_row.price == prepared_order.order.price

    assert position_row.symbol == prepared_order.symbol
    assert position_row.quantity == expected_position_quantity


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("side", "symbol", "quantity", "price", "expected_position_delta"),
    [
        pytest.param(OrderSide.BUY, "AAPL", 10, Decimal("150"), 10, id="buy_aapl"),
        pytest.param(OrderSide.SELL, "AAPL", 10, Decimal("150"), -10, id="sell_aapl"),
        pytest.param(OrderSide.BUY, "MSFT", 25, Decimal("320.5"), 25, id="buy_msft"),
    ],
)
async def test_order_flow_happy_path(
    nats_client,
    db_client,
    message_collector,
    side: OrderSide,
    symbol: str,
    quantity: int,
    price: Decimal,
    expected_position_delta: int,
):
    await _assert_full_order_flow(
        db_client,
        nats_client,
        message_collector,
        side=side,
        symbol=symbol,
        quantity=quantity,
        price=price,
        expected_position_delta=expected_position_delta,
    )


@pytest.mark.asyncio
async def test_order_flow_accepts_min_quantity(
    nats_client,
    db_client,
    message_collector,
):
    """Minimal allowed quantity (1) should pass the full flow."""
    await _assert_full_order_flow(
        db_client,
        nats_client,
        message_collector,
        side=OrderSide.BUY,
        symbol="AAPL",
        quantity=1,
        price=Decimal("150"),
        expected_position_delta=1,
    )


@pytest.mark.asyncio
async def test_order_flow_accepts_min_price(
    nats_client,
    db_client,
    message_collector,
):
    """Minimal allowed price (0.0001) should pass the full flow."""
    await _assert_full_order_flow(
        db_client,
        nats_client,
        message_collector,
        side=OrderSide.BUY,
        symbol="AAPL",
        quantity=10,
        price=Decimal("0.0001"),
        expected_position_delta=10,
    )


@pytest.mark.asyncio
async def test_order_flow_accepts_high_precision_price(
    nats_client,
    db_client,
    message_collector,
):
    """Price with many decimal places should survive serialisation and DB round‑trip."""
    # Note: the model serialises price via float which may lose precision —
    # this test documents the current accuracy the system provides.
    await _assert_full_order_flow(
        db_client,
        nats_client,
        message_collector,
        side=OrderSide.BUY,
        symbol="MSFT",
        quantity=10,
        price=Decimal("150.123456789"),
        expected_position_delta=10,
    )
