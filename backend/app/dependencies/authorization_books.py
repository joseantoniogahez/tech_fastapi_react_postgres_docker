from typing import Annotated

from fastapi import Depends

from app.authorization import PermissionId, PermissionScope
from app.models.user import User

from .authorization import require_authorized_user

BOOK_PERMISSION_IDS: dict[str, str] = {
    "create": PermissionId.BOOK_CREATE,
    "update": PermissionId.BOOK_UPDATE,
    "delete": PermissionId.BOOK_DELETE,
}

BookCreateAuth = Annotated[
    User,
    Depends(require_authorized_user(BOOK_PERMISSION_IDS["create"], required_scope=PermissionScope.ANY)),
]
BookUpdateAuth = Annotated[
    User,
    Depends(require_authorized_user(BOOK_PERMISSION_IDS["update"], required_scope=PermissionScope.ANY)),
]
BookDeleteAuth = Annotated[
    User,
    Depends(require_authorized_user(BOOK_PERMISSION_IDS["delete"], required_scope=PermissionScope.ANY)),
]
