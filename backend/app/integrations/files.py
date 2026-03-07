from typing import Protocol

from app.core.common.integration import StoredFileResult, StoreFileCommand


class FileStoragePort(Protocol):
    async def store(self, command: StoreFileCommand) -> StoredFileResult: ...

    async def delete(self, *, bucket: str, path: str) -> bool: ...
