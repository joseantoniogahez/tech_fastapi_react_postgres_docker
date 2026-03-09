from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db.base import BaseModel


class Permission(BaseModel):
    __tablename__ = "permissions"

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
