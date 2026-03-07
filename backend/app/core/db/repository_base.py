from collections.abc import Iterable, Mapping
from typing import Any, Protocol, cast

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import InstrumentedAttribute

from app.core.common.pagination import DEFAULT_LIST_LIMIT, DEFAULT_SORT, MAX_LIST_LIMIT
from app.core.db.database import Base
from app.core.errors.repositories import RepositoryError

IdType = int


class SupportsFromDomain[RecordType](Protocol):
    @classmethod
    def from_domain(cls, payload: Any) -> RecordType: ...


class BaseRepository[ModelType: Base]:
    def __init__(
        self,
        session: AsyncSession,
        model: type[ModelType],
        *,
        default_record_type: type[SupportsFromDomain[Any]] | None = None,
    ):
        self.session = session
        self.model = model
        self._default_record_type = default_record_type

    def _get_column(self, column_name: str) -> InstrumentedAttribute[Any]:
        column = getattr(self.model, column_name, None)
        if column is None:
            raise RepositoryError(f"Column '{column_name}' does not exist on '{self.model.__name__}'")
        return column

    def _build_sort_order(self, sort: str) -> tuple[Any, ...]:
        descending = sort.startswith("-")
        column_name = sort[1:] if descending else sort
        if not column_name:
            raise RepositoryError("Sort field cannot be empty")

        column = self._get_column(column_name)
        primary_order = column.desc() if descending else column.asc()
        if column_name == "id":
            return (primary_order,)

        # Add a deterministic tiebreaker so paginated responses stay stable.
        return (primary_order, self._get_column("id").asc())

    def _build_query(
        self,
        *,
        filters: Mapping[str, Any] | None = None,
        sort: str | None = None,
    ) -> Select[tuple[ModelType]]:
        query = select(self.model)
        if filters:
            for column_name, value in filters.items():
                query = query.where(self._get_column(column_name) == value)
        if sort is not None:
            query = query.order_by(*self._build_sort_order(sort))
        return query

    def _resolve_record_type[RecordType](
        self, record_type: type[SupportsFromDomain[RecordType]] | None
    ) -> type[SupportsFromDomain[RecordType]]:
        resolved_record_type = record_type or self._default_record_type
        if resolved_record_type is None:
            raise RepositoryError("Record type must be provided for this repository")
        return cast(type[SupportsFromDomain[RecordType]], resolved_record_type)

    def _to_record[RecordType](
        self,
        payload: Any,
        record_type: type[SupportsFromDomain[RecordType]] | None = None,
    ) -> RecordType:
        resolved_record_type = self._resolve_record_type(record_type)
        return resolved_record_type.from_domain(payload)

    def _to_records[RecordType](
        self,
        payloads: Iterable[Any],
        record_type: type[SupportsFromDomain[RecordType]] | None = None,
    ) -> list[RecordType]:
        resolved_record_type = self._resolve_record_type(record_type)
        return [resolved_record_type.from_domain(payload) for payload in payloads]

    def build(self, **kwargs: Any) -> ModelType:
        return self.model(**kwargs)

    async def create(self, **kwargs: Any) -> ModelType:
        entity = self.build(**kwargs)
        self.session.add(entity)
        await self.session.flush()
        await self.session.refresh(entity)
        return entity

    async def get(self, entity_id: IdType) -> ModelType | None:
        return await self.session.get(self.model, entity_id)

    async def get_one_by(self, filters: Mapping[str, Any]) -> ModelType | None:
        query = self._build_query(filters=filters)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def list(
        self,
        *,
        filters: Mapping[str, Any] | None = None,
        offset: int = 0,
        limit: int = DEFAULT_LIST_LIMIT,
        sort: str = DEFAULT_SORT,
    ) -> list[ModelType]:
        if offset < 0:
            raise RepositoryError("Offset must be greater than or equal to 0")
        if limit < 1:
            raise RepositoryError("Limit must be greater than or equal to 1")

        query = self._build_query(filters=filters, sort=sort).offset(offset).limit(min(limit, MAX_LIST_LIMIT))

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def update(self, entity: ModelType, **changes: Any) -> ModelType:
        for field, value in changes.items():
            self._get_column(field)
            setattr(entity, field, value)

        merged_entity = await self.session.merge(entity)
        await self.session.flush()
        await self.session.refresh(merged_entity)
        return merged_entity

    async def delete(self, entity_id: IdType) -> bool:
        # Use session.get directly so repository adapters can customize `get`
        # return types (DTO records) without breaking delete semantics.
        entity = await self.session.get(self.model, entity_id)
        if entity is None:
            return False

        await self.session.delete(entity)
        await self.session.flush()
        return True
