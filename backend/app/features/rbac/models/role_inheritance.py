from sqlalchemy import CheckConstraint, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db.database import Base


class RoleInheritance(Base):
    __tablename__ = "role_inheritances"
    __table_args__ = (
        CheckConstraint(
            "role_id <> parent_role_id",
            name="ck_role_inheritances_not_self",
        ),
    )

    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"), primary_key=True)
    parent_role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"), primary_key=True)
