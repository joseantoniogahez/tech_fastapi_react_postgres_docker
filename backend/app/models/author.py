from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models import BaseModel


class Author(BaseModel):
    __tablename__ = "authors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
