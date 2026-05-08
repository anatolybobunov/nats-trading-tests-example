import asyncio
from uuid import UUID

import asyncpg
import structlog

from src.pg.models import OrderRow, PositionRow
from src.enums import OrderStatus

logger = structlog.get_logger(__name__)


class PostgresClient:
    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    @classmethod
    async def connect(cls, dsn: str) -> "PostgresClient":
        logger.debug("connecting to PostgreSQL", dsn=dsn)
        pool = await asyncpg.create_pool(dsn=dsn, min_size=1, max_size=5)
        logger.debug("connected to PostgreSQL", dsn=dsn)
        return cls(pool)

    async def close(self) -> None:
        logger.debug("closing pg pool")
        await self._pool.close()

    async def fetch_order(self, order_id: UUID) -> OrderRow | None:
        logger.debug("fetching order", order_id=str(order_id))
        query = """
        SELECT order_id, symbol, side, quantity, price, status, created_at
        FROM orders
        WHERE order_id = $1
        """
        record = await self._pool.fetchrow(query, order_id)
        if record is None:
            logger.debug("order not found", order_id=str(order_id))
            return None
        return OrderRow.model_validate(dict(record))

    async def fetch_position(self, symbol: str) -> PositionRow | None:
        logger.debug("fetching position", symbol=symbol)
        query = """
        SELECT symbol, quantity, updated_at
        FROM positions
        WHERE symbol = $1
        """
        record = await self._pool.fetchrow(query, symbol)
        if record is None:
            logger.debug("position not found", symbol=symbol)
            return None
        return PositionRow.model_validate(dict(record))

    async def fetch_all_orders(self) -> list[OrderRow]:
        logger.debug("fetching all orders")
        query = """
        SELECT order_id, symbol, side, quantity, price, status, created_at
        FROM orders
        ORDER BY created_at ASC
        """
        records = await self._pool.fetch(query)
        orders = [OrderRow.model_validate(dict(record)) for record in records]
        logger.debug("fetched all orders", count=len(orders))
        return orders

    async def fetch_all_positions(self) -> list[PositionRow]:
        logger.debug("fetching all positions")
        query = """
        SELECT symbol, quantity, updated_at
        FROM positions
        ORDER BY symbol ASC
        """
        records = await self._pool.fetch(query)
        positions = [PositionRow.model_validate(dict(record)) for record in records]
        logger.debug("fetched all positions", count=len(positions))
        return positions

    async def wait_for_order_status(
        self,
        order_id: UUID,
        status: OrderStatus,
        *,
        timeout: float = 5.0,
        poll_interval: float = 0.1,
    ) -> OrderRow:
        logger.debug(
            "waiting for order status",
            order_id=str(order_id),
            expected_status=status.value,
            timeout=timeout,
        )
        loop = asyncio.get_running_loop()
        deadline = loop.time() + timeout

        while True:
            order = await self.fetch_order(order_id)
            if order is not None and order.status == status:
                logger.debug(
                    "order reached expected status",
                    order_id=str(order_id),
                    status=status.value,
                )
                return order

            if loop.time() >= deadline:
                logger.debug(
                    "timed out waiting for order status",
                    order_id=str(order_id),
                    expected_status=status.value,
                )
                raise TimeoutError(f"timed out waiting for order {order_id} to reach status '{status}'")
            await asyncio.sleep(poll_interval)

    async def wait_for_position_quantity(
        self,
        symbol: str,
        quantity: int,
        *,
        timeout: float = 5.0,
        poll_interval: float = 0.1,
    ) -> PositionRow:
        logger.debug(
            "waiting for position quantity",
            symbol=symbol,
            expected_quantity=quantity,
            timeout=timeout,
        )
        loop = asyncio.get_running_loop()
        deadline = loop.time() + timeout

        while True:
            position = await self.fetch_position(symbol)
            if position is not None and position.quantity == quantity:
                logger.debug(
                    "position reached expected quantity",
                    symbol=symbol,
                    quantity=quantity,
                )
                return position

            if loop.time() >= deadline:
                logger.debug(
                    "timed out waiting for position quantity",
                    symbol=symbol,
                    expected_quantity=quantity,
                )
                raise TimeoutError(f"timed out waiting for position '{symbol}' quantity to become {quantity}")
            await asyncio.sleep(poll_interval)

    async def execute(self, query: str, *args) -> str:
        logger.debug("executing query", query=query, args=args)
        async with self._pool.acquire() as conn:
            result = await conn.execute(query, *args)
            logger.debug("query executed", query=query, result=result)
            return result
