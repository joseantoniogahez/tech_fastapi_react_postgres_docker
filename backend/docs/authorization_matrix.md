# Authorization Matrix

Permission policies are defined in `app/dependencies/authorization.py` and consumed by protected routes.

| Permission | Dependency Alias | Endpoint |
| --- | --- | --- |
| `books:create` | `BookCreateAuthorizedUserDependency` | `POST /books/` |
| `books:update` | `BookUpdateAuthorizedUserDependency` | `PUT /books/{id}` |
| `books:delete` | `BookDeleteAuthorizedUserDependency` | `DELETE /books/{id}` |
