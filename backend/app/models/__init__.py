from datetime import datetime

from sqlalchemy import DateTime
from sqlalchemy.orm import Mapped, declarative_mixin, mapped_column

from app.database import Base


@declarative_mixin
class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)


class BaseModel(Base, TimestampMixin):
    __abstract__ = True
