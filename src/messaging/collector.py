import asyncio
from collections.abc import Awaitable, Callable

from nats.aio.msg import Msg
from nats.aio.subscription import Subscription

from src.messaging.nats_client import NatsClient
from src.messaging.models import NatsMessage


class MessageCollector:
    def __init__(self, client: NatsClient) -> None:
        self._client = client
        self._subscriptions: dict[str, Subscription] = {}
        self._queues: dict[str, asyncio.Queue[NatsMessage]] = {}
        self._pending: dict[str, list[NatsMessage]] = {}

    async def start(self, subjects: list[str]) -> None:
        for subject in subjects:
            if subject in self._subscriptions:
                continue

            queue: asyncio.Queue[NatsMessage] = asyncio.Queue()
            self._queues[subject] = queue
            self._pending[subject] = []

            subscription = await self._client.subscribe(subject, cb=self._make_handler(subject))
            self._subscriptions[subject] = subscription

    async def wait_for(
        self,
        subject: str,
        *,
        timeout: float = 5.0,
        predicate: Callable[[NatsMessage], bool] | None = None,
    ) -> NatsMessage:
        if subject not in self._queues:
            msg = f"subject '{subject}' is not subscribed"
            raise ValueError(msg)

        pending = self._pending[subject]
        if predicate is None and pending:
            return pending.pop(0)
        if predicate is not None:
            for index, message in enumerate(pending):
                if predicate(message):
                    return pending.pop(index)

        queue = self._queues[subject]
        loop = asyncio.get_running_loop()
        deadline = loop.time() + timeout

        while True:
            remaining = deadline - loop.time()
            if remaining <= 0:
                raise TimeoutError(f"timed out waiting for subject '{subject}'")

            message = await asyncio.wait_for(queue.get(), timeout=remaining)
            if predicate is None or predicate(message):
                return message
            pending.append(message)

    async def drain(self, subject: str) -> list[NatsMessage]:
        if subject not in self._queues:
            msg = f"subject '{subject}' is not subscribed"
            raise ValueError(msg)

        drained = list(self._pending[subject])
        self._pending[subject].clear()

        queue = self._queues[subject]
        while True:
            try:
                drained.append(queue.get_nowait())
            except asyncio.QueueEmpty:
                break
        return drained

    async def reset(self) -> None:
        for subject in list(self._queues.keys()):
            await self.drain(subject)

    async def stop(self) -> None:
        for subscription in self._subscriptions.values():
            await subscription.unsubscribe()

        self._subscriptions.clear()
        self._queues.clear()
        self._pending.clear()

    def _make_handler(self, subject: str) -> Callable[[Msg], Awaitable[None]]:
        async def on_message(msg: Msg) -> None:
            headers = dict(msg.headers) if msg.headers is not None else None
            message = NatsMessage(
                subject=msg.subject,
                data=msg.data,
                headers=headers,
                reply=msg.reply,
            )
            await self._queues[subject].put(message)

        return on_message
