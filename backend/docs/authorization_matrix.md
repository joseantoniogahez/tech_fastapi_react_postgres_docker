# Authorization Matrix

Permission policies are defined in `app/dependencies/authorization.py` and consumed by protected routes.

| Permission | Dependency Alias | Endpoint |
| --- | --- | --- |
| `books:create` | `BookCreateAuthorizedUserDependency` | `POST /books/` |
| `books:update` | `BookUpdateAuthorizedUserDependency` | `PUT /books/{id}` |
| `books:delete` | `BookDeleteAuthorizedUserDependency` | `DELETE /books/{id}` |

## Notes

- Permission checks are evaluated after bearer token validation.
- Missing permission returns `403 forbidden` with `meta.permission_id`.
- OpenAPI endpoint docs for protected routes live in `app/openapi/books.py`.
