import structlog
from uuid import UUID

from src.pg.models import OrderRow, PositionRow
from src.pg.pg_client import PostgresClient
from src.enums import OrderStatus

logger = structlog.get_logger(__name__)


async def check_order_in_db(
    db_client: PostgresClient,
    *,
    order_id: UUID,
    expected_status: OrderStatus = OrderStatus.CREATED,
) -> OrderRow:
    """Default status assumption follows task.md: new order row appears with CREATED."""
    logger.info("checking order in pg", order_id=str(order_id), expected_status=expected_status.value)
    return await db_client.wait_for_order_status(order_id, expected_status)


async def check_position_updated(
    db_client: PostgresClient,
    *,
    symbol: str,
    expected_quantity: int,
) -> PositionRow:
    logger.info(
        "checking position updated in pg",
        symbol=symbol,
        expected_quantity=expected_quantity,
    )
    return await db_client.wait_for_position_quantity(symbol, expected_quantity)
