from typing import Protocol

from app.core.common.integration import EnqueueJobCommand


class JobSchedulerPort(Protocol):
    async def enqueue(self, job: EnqueueJobCommand) -> str: ...
