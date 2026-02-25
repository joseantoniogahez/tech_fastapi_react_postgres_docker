from .authentication import (
    AuthCredentialsDependency,
    BearerTokenDependency,
    CurrentActiveUserDependency,
    CurrentUserDependency,
    get_auth_credentials,
    get_current_active_user,
    get_current_user,
)
from .authorization import (
    AuthorizedUserPolicyDependency,
    PermissionPolicyDependency,
    require_authorized_user,
    require_permission,
)
from .authorization_books import (
    BookCreateAuthorizedUserDependency,
    BookDeleteAuthorizedUserDependency,
    BookUpdateAuthorizedUserDependency,
)
from .db import DbSessionDependency, UnitOfWorkDependency, get_db_session, get_unit_of_work
from .repositories import (
    AuthorRepositoryDependency,
    AuthRepositoryDependency,
    BookRepositoryDependency,
    get_auth_repository,
    get_author_repository,
    get_book_repository,
)
from .services import (
    AuthorServiceDependency,
    AuthServiceDependency,
    AuthSettingsDependency,
    BookServiceDependency,
    get_auth_service,
    get_auth_settings,
    get_authors_service,
    get_books_service,
)

__all__ = [
    "AuthorizedUserPolicyDependency",
    "BookCreateAuthorizedUserDependency",
    "BookDeleteAuthorizedUserDependency",
    "BookUpdateAuthorizedUserDependency",
    "PermissionPolicyDependency",
    "require_authorized_user",
    "require_permission",
    "AuthCredentialsDependency",
    "AuthRepositoryDependency",
    "AuthServiceDependency",
    "AuthSettingsDependency",
    "AuthorRepositoryDependency",
    "AuthorServiceDependency",
    "BearerTokenDependency",
    "BookRepositoryDependency",
    "BookServiceDependency",
    "CurrentActiveUserDependency",
    "CurrentUserDependency",
    "DbSessionDependency",
    "UnitOfWorkDependency",
    "get_auth_credentials",
    "get_auth_repository",
    "get_auth_service",
    "get_auth_settings",
    "get_author_repository",
    "get_authors_service",
    "get_book_repository",
    "get_books_service",
    "get_current_active_user",
    "get_current_user",
    "get_db_session",
    "get_unit_of_work",
]
