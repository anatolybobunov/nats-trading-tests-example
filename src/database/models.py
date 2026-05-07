from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel

from src.enums import OrderSide, OrderStatus


class OrderRow(BaseModel):
    order_id: UUID
    symbol: str
    side: OrderSide
    quantity: int
    price: Decimal
    status: OrderStatus
    created_at: datetime


class PositionRow(BaseModel):
    symbol: str
    quantity: int
    updated_at: datetime
