import asyncio

import structlog

from src.pg.models import PositionRow
from src.pg.pg_client import PostgresClient
from src.nts.collector import MessageCollector
from src.nts.subjects import TRADES_EXECUTED_SUBJECT


logger = structlog.get_logger(__name__)


async def assert_no_trade_executed(
    collector: MessageCollector,
    *,
    order_id: str,
    window: float = 2.0,
) -> None:
    """Verify that no *trades.executed* message appears for *order_id* within *window*.

    Drains any pending messages on the subject first, then waits for
    *window* seconds.  If a matching message arrives during that window
    the assertion fails.
    """
    await collector.drain(TRADES_EXECUTED_SUBJECT)
    logger.info("checking no trade executed", order_id=order_id, window=window)

    try:
        await asyncio.wait_for(
            _collect_matching(collector, order_id=order_id),
            timeout=window,
        )
    except asyncio.TimeoutError:
        return  # expected — no matching message arrived

    raise AssertionError(f"Unexpected *trades.executed* message for order_id={order_id!r}")


async def _collect_matching(
    collector: MessageCollector,
    *,
    order_id: str,
) -> None:
    """Wait until a matching trade message arrives (should NOT happen)."""
    await collector.wait_for(
        TRADES_EXECUTED_SUBJECT,
        timeout=9999,  # outer asyncio.wait_for governs the real timeout
        predicate=lambda m: m.json_payload().get("order_id") == order_id,
    )


async def assert_positions_unchanged(
    db_client: PostgresClient,
    *,
    expected: list[PositionRow],
) -> None:
    """Assert that current positions match the *expected* snapshot."""
    positions_after = await db_client.fetch_all_positions()
    assert positions_after == expected, (
        f"Positions changed:\n  before={_fmt_positions(expected)}\n  after ={_fmt_positions(positions_after)}"
    )


def _fmt_positions(rows: list[PositionRow]) -> str:
    parts: list[str] = []
    for r in rows:
        parts.append(f"{r.symbol}: qty={r.quantity} @ {r.updated_at}")
    return ", ".join(parts) if parts else "(empty)"
