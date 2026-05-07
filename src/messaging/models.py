import json
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field

from src.enums import OrderSide, OrderStatus


class NatsMessage(BaseModel):
    subject: str
    data: bytes
    headers: dict[str, str] | None = None
    reply: str | None = None
    received_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    def json_payload(self) -> dict[str, Any]:
        return json.loads(self.data.decode("utf-8"))


class OrderCreate(BaseModel):
    order_id: UUID
    symbol: str
    side: OrderSide
    quantity: int = Field(gt=0)
    price: Decimal = Field(gt=0)


class OrderConfirmed(BaseModel):
    order_id: UUID
    status: Literal[OrderStatus.CONFIRMED, OrderStatus.REJECTED]
    reason: str | None = None


class TradeExecuted(BaseModel):
    order_id: UUID
    symbol: str
    side: OrderSide
    quantity: int
    executed_at: datetime
