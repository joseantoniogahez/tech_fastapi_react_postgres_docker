from typing import Any

from app.core.common.schema import ApplicationSchema


class PublishMessageCommand(ApplicationSchema):
    topic: str
    key: str | None = None
    payload: dict[str, Any]


class EnqueueJobCommand(ApplicationSchema):
    job_name: str
    payload: dict[str, Any]


class SearchDocumentUpsertCommand(ApplicationSchema):
    index: str
    document_id: str
    body: dict[str, Any]


class DeleteSearchDocumentCommand(ApplicationSchema):
    index: str
    document_id: str


class StoreFileCommand(ApplicationSchema):
    bucket: str
    path: str
    content_type: str
    body: bytes


class StoredFileResult(ApplicationSchema):
    bucket: str
    path: str
    etag: str | None = None
