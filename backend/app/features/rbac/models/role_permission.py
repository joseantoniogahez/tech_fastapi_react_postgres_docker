from sqlalchemy import CheckConstraint, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.authorization import PERMISSION_SCOPES, PermissionScope
from app.core.db.database import Base


class RolePermission(Base):
    __tablename__ = "role_permissions"
    __table_args__ = (
        CheckConstraint(
            f"scope IN ({', '.join(repr(scope) for scope in PERMISSION_SCOPES)})",
            name="ck_role_permissions_scope",
        ),
    )

    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"), primary_key=True)
    permission_id: Mapped[str] = mapped_column(ForeignKey("permissions.id"), primary_key=True)
    scope: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=PermissionScope.ANY,
        server_default=PermissionScope.ANY,
    )
