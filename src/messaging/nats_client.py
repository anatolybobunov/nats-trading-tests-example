import json
from collections.abc import Awaitable, Callable
from typing import Any

import structlog
from nats.aio.client import Client
from nats.aio.msg import Msg
from nats.aio.subscription import Subscription
from pydantic import BaseModel

logger = structlog.get_logger(__name__)


class NatsClient:
    def __init__(self, connection: Client) -> None:
        self._connection = connection

    @classmethod
    async def connect(cls, servers: list[str], *, name: str = "e2e-tests") -> "NatsClient":
        logger.debug("connecting to NATS", servers=servers, name=name)
        connection = Client()
        await connection.connect(servers=servers, name=name)
        logger.debug("connected to NATS", servers=servers, name=name)
        return cls(connection)

    async def close(self) -> None:
        logger.debug("closing NATS connection")
        await self._connection.drain()
        await self._connection.close()
        logger.debug("NATS connection closed")

    async def publish_json(
        self,
        subject: str,
        payload: dict[str, Any] | BaseModel,
        *,
        headers: dict[str, str] | None = None,
    ) -> None:
        body: dict[str, Any]
        if isinstance(payload, BaseModel):
            body = payload.model_dump(mode="json")
        else:
            body = payload

        data = json.dumps(body).encode("utf-8")
        logger.debug(
            "publishing message",
            subject=subject,
            headers=headers,
            body=body,
            wire_payload=data.decode("utf-8"),
        )
        await self._connection.publish(subject, payload=data, headers=headers)

    async def subscribe(
        self,
        subject: str,
        *,
        cb: Callable[[Msg], Awaitable[None]] | None = None,
    ) -> Subscription:
        logger.debug("subscribing to subject", subject=subject)
        sub = await self._connection.subscribe(subject, cb=cb)
        logger.debug("subscribed to subject", subject=subject, sid=sub._id)
        return sub
