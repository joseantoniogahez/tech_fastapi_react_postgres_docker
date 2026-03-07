from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db.base import BaseModel


class Role(BaseModel):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
