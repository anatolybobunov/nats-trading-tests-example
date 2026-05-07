from uuid import UUID

from src.database.models import OrderRow, PositionRow
from src.database.pg_client import PostgresClient
from src.enums import OrderStatus


async def check_order_in_db(
    db_client: PostgresClient,
    *,
    order_id: UUID,
    expected_status: OrderStatus = OrderStatus.CREATED,
) -> OrderRow:
    """Default status assumption follows task.md: new order row appears with CREATED."""
    return await db_client.wait_for_order_status(order_id, expected_status)


async def check_position_updated(
    db_client: PostgresClient,
    *,
    symbol: str,
    expected_quantity: int,
) -> PositionRow:
    return await db_client.wait_for_position_quantity(symbol, expected_quantity)
