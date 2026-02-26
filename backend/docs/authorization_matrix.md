# Authorization Matrix

Permission policies are defined in `app/dependencies/authorization.py` and consumed by protected routes.

| Permission     | Dependency Alias                     | Endpoint             |
| -------------- | ------------------------------------ | -------------------- |
| `books:create` | `BookCreateAuthorizedUserDependency` | `POST /books/`       |
| `books:update` | `BookUpdateAuthorizedUserDependency` | `PUT /books/{id}`    |
| `books:delete` | `BookDeleteAuthorizedUserDependency` | `DELETE /books/{id}` |

## Base Role Catalog (Bootstrap)

Seed source: `utils/rbac_bootstrap.py`

| Role          | Base Permissions                                       |
| ------------- | ------------------------------------------------------ |
| `admin_role`  | `books:create`, `books:update`, `books:delete`         |
| `reader_role` | none (read access behavior is controlled per endpoint) |

## Notes

- Permission checks are evaluated after bearer token validation.
- Missing permission returns `403 forbidden` with `meta.permission_id`.
- OpenAPI endpoint docs for protected routes live in `app/openapi/books.py`.
- Bootstrap command is idempotent: `python -m utils.rbac_bootstrap`.
