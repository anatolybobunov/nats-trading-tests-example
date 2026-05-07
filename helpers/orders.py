from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID, uuid4

from src.enums import OrderSide
from src.messaging.models import OrderCreate
from src.messaging.nats_client import NatsClient
from src.messaging.subjects import ORDERS_CREATE_SUBJECT


@dataclass(frozen=True)
class PreparedOrder:
    order: OrderCreate
    expected_position_quantity: int

    @property
    def order_id(self) -> UUID:
        return self.order.order_id

    @property
    def symbol(self) -> str:
        return self.order.symbol


def prepare_order(
    *,
    symbol: str = "AAPL",
    side: OrderSide = OrderSide.BUY,
    quantity: int = 10,
    price: Decimal = Decimal("150.25"),
) -> PreparedOrder:
    order_id = uuid4()
    order = OrderCreate(
        order_id=order_id,
        symbol=symbol,
        side=side,
        quantity=quantity,
        price=price,
    )
    expected_position_quantity = quantity if side == OrderSide.BUY else -quantity
    return PreparedOrder(
        order=order,
        expected_position_quantity=expected_position_quantity,
    )


async def place_order(client: NatsClient, prepared_order: PreparedOrder) -> None:
    await client.publish_json(ORDERS_CREATE_SUBJECT, prepared_order.order)
