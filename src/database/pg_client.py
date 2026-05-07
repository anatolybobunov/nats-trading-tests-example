import asyncio
from uuid import UUID

import asyncpg

from src.database.models import OrderRow, PositionRow
from src.enums import OrderStatus


class PostgresClient:
    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    @classmethod
    async def connect(cls, dsn: str) -> "PostgresClient":
        pool = await asyncpg.create_pool(dsn=dsn, min_size=1, max_size=5)
        return cls(pool)

    async def close(self) -> None:
        await self._pool.close()

    async def fetch_order(self, order_id: UUID) -> OrderRow | None:
        query = """
        SELECT order_id, symbol, side, quantity, price, status, created_at
        FROM orders
        WHERE order_id = $1
        """
        record = await self._pool.fetchrow(query, order_id)
        if record is None:
            return None
        return OrderRow.model_validate(dict(record))

    async def fetch_position(self, symbol: str) -> PositionRow | None:
        query = """
        SELECT symbol, quantity, updated_at
        FROM positions
        WHERE symbol = $1
        """
        record = await self._pool.fetchrow(query, symbol)
        if record is None:
            return None
        return PositionRow.model_validate(dict(record))

    async def wait_for_order_status(
        self,
        order_id: UUID,
        status: OrderStatus,
        *,
        timeout: float = 5.0,
        poll_interval: float = 0.1,
    ) -> OrderRow:
        loop = asyncio.get_running_loop()
        deadline = loop.time() + timeout

        while True:
            order = await self.fetch_order(order_id)
            if order is not None and order.status == status:
                return order

            if loop.time() >= deadline:
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
        loop = asyncio.get_running_loop()
        deadline = loop.time() + timeout

        while True:
            position = await self.fetch_position(symbol)
            if position is not None and position.quantity == quantity:
                return position

            if loop.time() >= deadline:
                raise TimeoutError(f"timed out waiting for position '{symbol}' quantity to become {quantity}")
            await asyncio.sleep(poll_interval)

    async def execute(self, query: str, *args) -> str:
        async with self._pool.acquire() as conn:
            return await conn.execute(query, *args)
