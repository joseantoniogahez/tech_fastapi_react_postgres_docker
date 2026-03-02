from .auth import AuthenticatedUser, Credentials, RegisterUser, Token, UpdateCurrentUser
from .author import Author
from .book import AddBook, Book, UpdateBook
from .rbac import (
    CreateRole,
    RBACPermission,
    RBACRole,
    RBACRolePermission,
    SetRolePermission,
    UpdateRole,
    UserRoleAssignment,
)
