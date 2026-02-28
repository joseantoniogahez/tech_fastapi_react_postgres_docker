from typing import Any, Generic, Mapping, Optional, Type, TypeVar

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import InstrumentedAttribute

from app.common.pagination import DEFAULT_LIST_LIMIT, DEFAULT_SORT, MAX_LIST_LIMIT
from app.database import Base
from app.exceptions.repositories import RepositoryException

ModelType = TypeVar("ModelType", bound=Base)
IdType = int


class BaseRepository(Generic[ModelType]):
    def __init__(self, session: AsyncSession, model: Type[ModelType]):
        self.session = session
        self.model = model

    def _get_column(self, column_name: str) -> InstrumentedAttribute[Any]:
        column = getattr(self.model, column_name, None)
        if column is None:
            raise RepositoryException(f"Column '{column_name}' does not exist on '{self.model.__name__}'")
        return column

    def _build_sort_order(self, sort: str) -> tuple[Any, ...]:
        descending = sort.startswith("-")
        column_name = sort[1:] if descending else sort
        if not column_name:
            raise RepositoryException("Sort field cannot be empty")

        column = self._get_column(column_name)
        primary_order = column.desc() if descending else column.asc()
        if column_name == "id":
            return (primary_order,)

        # Add a deterministic tiebreaker so paginated responses stay stable.
        return (primary_order, self._get_column("id").asc())

    def _build_query(
        self,
        *,
        filters: Optional[Mapping[str, Any]] = None,
        sort: Optional[str] = None,
    ) -> Select[tuple[ModelType]]:
        query = select(self.model)
        if filters:
            for column_name, value in filters.items():
                query = query.where(self._get_column(column_name) == value)
        if sort is not None:
            query = query.order_by(*self._build_sort_order(sort))
        return query

    def build(self, **kwargs: Any) -> ModelType:
        return self.model(**kwargs)

    async def create(self, **kwargs: Any) -> ModelType:
        entity = self.build(**kwargs)
        self.session.add(entity)
        await self.session.flush()
        await self.session.refresh(entity)
        return entity

    async def get(self, entity_id: IdType) -> Optional[ModelType]:
        return await self.session.get(self.model, entity_id)

    async def get_one_by(self, filters: Mapping[str, Any]) -> Optional[ModelType]:
        query = self._build_query(filters=filters)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def list(
        self,
        *,
        filters: Optional[Mapping[str, Any]] = None,
        offset: int = 0,
        limit: int = DEFAULT_LIST_LIMIT,
        sort: str = DEFAULT_SORT,
    ) -> list[ModelType]:
        if offset < 0:
            raise RepositoryException("Offset must be greater than or equal to 0")
        if limit < 1:
            raise RepositoryException("Limit must be greater than or equal to 1")

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
        entity = await self.get(entity_id)
        if entity is None:
            return False

        await self.session.delete(entity)
        await self.session.flush()
        return True
