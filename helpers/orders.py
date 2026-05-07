import structlog
from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID, uuid4

from src.enums import OrderSide
from src.messaging.models import OrderCreate
from src.messaging.nats_client import NatsClient
from src.messaging.subjects import ORDERS_CREATE_SUBJECT

logger = structlog.get_logger(__name__)


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
    symbol: str,
    side: OrderSide = OrderSide.BUY,
    quantity: int,
    price: Decimal,
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
    logger.info(
        "order prepared",
        order_id=str(order_id),
        symbol=symbol,
        side=side.value,
        quantity=quantity,
        price=str(price),
    )
    return PreparedOrder(
        order=order,
        expected_position_quantity=expected_position_quantity,
    )


async def place_order(client: NatsClient, prepared_order: PreparedOrder) -> None:
    logger.info(
        "placing order",
        subject=ORDERS_CREATE_SUBJECT,
        order_id=str(prepared_order.order_id),
        symbol=prepared_order.symbol,
    )
    await client.publish_json(ORDERS_CREATE_SUBJECT, prepared_order.order)
