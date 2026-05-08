"""Shared helpers for order rejection tests.

Provides base payload factory and mutator functions for parametrized
negative test cases.
"""

from collections.abc import Callable
from typing import Any
from uuid import uuid4


# TODO: вынести этот код из helpers


def base_order_payload() -> dict[str, Any]:
    """Return a valid order payload that can be mutated for negative tests."""
    return {
        "order_id": str(uuid4()),
        "symbol": "AAPL",
        "side": "BUY",
        "quantity": 10,
        "price": 150.0,
    }


def drop_field(field_name: str) -> Callable[[dict[str, Any]], None]:
    """Return a mutator that removes *field_name* from the payload."""

    def mutate(payload: dict[str, Any]) -> None:
        payload.pop(field_name, None)

    return mutate


def set_field(field_name: str, value: Any) -> Callable[[dict[str, Any]], None]:
    """Return a mutator that sets *field_name* to *value*."""

    def mutate(payload: dict[str, Any]) -> None:
        payload[field_name] = value

    return mutate
