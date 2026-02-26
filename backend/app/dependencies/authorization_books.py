from typing import Annotated

from fastapi import Depends

from app.const.permission import PermissionId
from app.models.user import User

from .authorization import require_authorized_user

BOOK_PERMISSION_IDS: dict[str, str] = {
    "create": PermissionId.BOOK_CREATE,
    "update": PermissionId.BOOK_UPDATE,
    "delete": PermissionId.BOOK_DELETE,
}

BookCreateAuth = Annotated[
    User,
    Depends(require_authorized_user(BOOK_PERMISSION_IDS["create"])),
]
BookUpdateAuth = Annotated[
    User,
    Depends(require_authorized_user(BOOK_PERMISSION_IDS["update"])),
]
BookDeleteAuth = Annotated[
    User,
    Depends(require_authorized_user(BOOK_PERMISSION_IDS["delete"])),
]
