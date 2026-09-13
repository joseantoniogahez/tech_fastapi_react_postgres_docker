# OpenAPI Documentation Pattern

## Goal

Keep routers readable while preserving explicit endpoint documentation.

## Current structure

OpenAPI metadata is owned by the feature that exposes the endpoint.

- shared helpers: `app/core/common/openapi.py`
- feature docs:
  - `app/features/auth/openapi.py`
  - `app/features/audit_log/openapi.py`
  - `app/features/health/openapi.py`
  - `app/features/rbac/openapi/__init__.py`
  - `app/features/rbac/openapi/docs.py`
  - `app/features/rbac/openapi/params.py`

Routers consume those constants with `**DOC_CONSTANT`.

## Router pattern

```python
@router.get("/roles", response_model=list[RBACRole], **GET_ROLES_DOC)
async def list_roles(...):
    ...
```

Typed payload/path aliases can also live next to feature docs:

```python
RoleIdPath = Annotated[int, Path(ge=1)]
CreateRolePayload = Annotated[CreateRoleRequest, Body(...)]
```

## Naming conventions

- endpoint metadata: `<ENDPOINT_NAME>_DOC`
- payload/path aliases: descriptive singular names such as `CreateRolePayload`, `RoleIdPath`
- shared helpers:
  - `build_error_response`
  - `INTERNAL_ERROR_EXAMPLE`

## Adding docs for a new endpoint

1. Add metadata constants in the feature OpenAPI module.
1. Import them in the feature router.
1. Keep examples close to the feature, not in a global demo module.
1. Update `docs/operations/api_endpoints.md` with the method, path, authentication, permission,
   OpenAPI visibility, success status, and every documented error status.
1. Run the documentation and router contract tests after updating the docs.

## Preventive Contract

`tests/contracts/test_documentation_contracts.py` compares application `APIRoute` objects, the endpoint
inventory, and generated OpenAPI by exact method and path. For each operation it also requires exact
success/error status equality and matching authentication, permission, and OpenAPI visibility.

The generated schema is the runtime side of this contract. Do not maintain a separate hand-written
OpenAPI operation inventory. CORS, request correlation, and readiness are implemented and
documented; rate limiting is documented here only after its runtime behavior exists.

## Runtime Exposure

`APP_ENV` has a finite, validated vocabulary. The `/docs`, `/redoc`, and `/openapi.json` HTTP routes
are enabled only for `local`, `test`, and `development`; they are absent in `staging` and
`production`. Unknown environments fail settings validation instead of silently exposing docs.

Programmatic artifact generation remains supported in the controlled `test` environment. The
frontend OpenAPI sync script sets that environment explicitly and compares the normalized
25-operation schema.
