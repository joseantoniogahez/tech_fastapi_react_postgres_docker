from typing import Annotated

from fastapi import Depends

from app.const.permission import PermissionId
from app.models.user import User

from .authorization import require_authorized_user

BookCreateAuthorizedUserDependency = Annotated[User, Depends(require_authorized_user(PermissionId.BOOK_CREATE))]
BookUpdateAuthorizedUserDependency = Annotated[User, Depends(require_authorized_user(PermissionId.BOOK_UPDATE))]
BookDeleteAuthorizedUserDependency = Annotated[User, Depends(require_authorized_user(PermissionId.BOOK_DELETE))]


__all__ = [
    "BookCreateAuthorizedUserDependency",
    "BookUpdateAuthorizedUserDependency",
    "BookDeleteAuthorizedUserDependency",
]
