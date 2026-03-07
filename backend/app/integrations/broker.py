from typing import Protocol

from app.core.common.integration import PublishMessageCommand


class MessageBrokerPort(Protocol):
    async def publish(self, message: PublishMessageCommand) -> None: ...
