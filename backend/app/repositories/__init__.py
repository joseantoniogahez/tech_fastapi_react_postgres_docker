from typing import Any, Generic, Mapping, Optional, Type, TypeVar

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import InstrumentedAttribute

from app import ExceptionBase
from app.database import Base


class RepositoryException(ExceptionBase):
    pass


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

    def _build_query(
        self,
        *,
        filters: Optional[Mapping[str, Any]] = None,
        order_by: Optional[str] = None,
    ) -> Select[tuple[ModelType]]:
        query = select(self.model)
        if filters:
            for column_name, value in filters.items():
                query = query.where(self._get_column(column_name) == value)
        if order_by is not None:
            query = query.order_by(self._get_column(order_by))
        return query

    def build(self, **kwargs: Any) -> ModelType:
        return self.model(**kwargs)

    async def create(self, **kwargs: Any) -> ModelType:
        entity = self.build(**kwargs)
        self.session.add(entity)
        await self.session.commit()
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
        limit: Optional[int] = None,
        order_by: Optional[str] = None,
    ) -> list[ModelType]:
        query = self._build_query(filters=filters, order_by=order_by).offset(offset)
        if limit is not None:
            query = query.limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def update(self, entity: ModelType, **changes: Any) -> ModelType:
        for field, value in changes.items():
            self._get_column(field)
            setattr(entity, field, value)

        merged_entity = await self.session.merge(entity)
        await self.session.commit()
        await self.session.refresh(merged_entity)
        return merged_entity

    async def delete(self, entity_id: IdType) -> bool:
        entity = await self.get(entity_id)
        if entity is None:
            return False

        await self.session.delete(entity)
        await self.session.commit()
        return True


__all__ = [
    "BaseRepository",
    "RepositoryException",
    "IdType",
]
