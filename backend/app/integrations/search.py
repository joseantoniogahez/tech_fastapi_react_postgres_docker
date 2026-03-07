from typing import Protocol

from app.core.common.integration import DeleteSearchDocumentCommand, SearchDocumentUpsertCommand


class SearchIndexPort(Protocol):
    async def upsert_document(self, command: SearchDocumentUpsertCommand) -> None: ...

    async def delete_document(self, command: DeleteSearchDocumentCommand) -> None: ...
