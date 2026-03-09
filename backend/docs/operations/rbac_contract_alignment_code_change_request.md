# Code Change Request: RBAC Contract Alignment and Data Consistency

## How to Use This Template With the AI Assistant

1. Fill every section with exact scope and constraints.
1. Reference backend playbook/contracts the assistant must follow.
1. Define mandatory tests and validation commands.
1. Paste the completed template in your request to the assistant.

## Problem and Goal

Current RBAC APIs allow managing role inheritance and user-role assignments, but API responses do not expose role hierarchy metadata and assignment read endpoints are incomplete.
In addition, permission name uniqueness is required by product rules but is not currently enforced at the database/model level.
The goal is to align RBAC contracts with requirements without changing existing successful behavior.

## Scope (In / Out)

### In Scope

- Add read endpoints for role assignment visibility:
- `GET /v1/rbac/users/{user_id}/roles` returns roles assigned directly to a user.
- `GET /v1/rbac/roles/{role_id}/users` returns users directly assigned to a role.
- Extend role response contracts to expose hierarchy metadata:
- Add `parent_role_ids: int[]` to role payloads returned by `GET /v1/rbac/roles`, `POST /v1/rbac/roles`, and `PUT /v1/rbac/roles/{role_id}`.
- Enforce permission name uniqueness:
- Add DB unique constraint for `permissions.name` in Alembic migration.
- Update ORM model to mirror uniqueness contract.
- Update docs and contract tests impacted by these changes.

### Out of Scope

- Redesign of permission scope model (`own`, `tenant`, `any`).
- Changes to existing role-permission upsert/remove semantics.
- Changes to token payload format.
- New external integrations.

## API, Data, and Authorization Implications

- API changes:
- New `GET /v1/rbac/users/{user_id}/roles` endpoint.
- New `GET /v1/rbac/roles/{role_id}/users` endpoint.
- `RBACRole` response includes `parent_role_ids`.
- Authorization:
- Require `user_roles:manage` for the two new read endpoints (scope `any`).
- Keep existing permissions for all current endpoints unchanged.
- Data model/migration:
- Add unique constraint on `permissions.name`.
- Ensure migration is forward-compatible with current seeded permissions.
- Docs/contracts to update:
- `backend/docs/operations/api_endpoints.md`
- `backend/docs/operations/authorization_matrix.md`
- `backend/docs/operations/error_mapping.md` (if new error mapping notes are needed)

## Observability and Error Handling

- Keep logging and normalized error shape unchanged.
- Expected error behavior:
- `400 invalid_input` for invalid IDs.
- `401 unauthorized` for missing/invalid token.
- `403 forbidden` for missing `user_roles:manage`.
- `404 not_found` for unknown user/role IDs.
- `409 conflict` for uniqueness violations related to permission names (repository conflict translation when applicable).

## Acceptance Criteria

- New assignment-read endpoints return deterministic, sorted data and are permission-protected.
- Role responses include `parent_role_ids` and match persisted inheritance links.
- Existing role/permission assignment endpoints keep current response shape and behavior (except added `parent_role_ids` on role payloads).
- Database rejects duplicate `permissions.name` values.
- OpenAPI/operations docs and authorization matrix match actual behavior.

## AI Execution Constraints (Required)

- Docs the AI must read before coding (minimum):
  - `backend/docs/backend_playbook.md`
  - `backend/docs/operations/api_endpoints.md`
  - `backend/docs/operations/authorization_matrix.md`
  - `backend/docs/operations/error_mapping.md`
  - `backend/docs/architecture/dependency_injection.md`
  - `backend/docs/architecture/openapi_documentation.md`
  - `backend/docs/architecture/unit_of_work.md`
- Mandatory implementation constraints:
  - Keep router/service/repository boundaries.
  - Keep DI/UoW behavior intact unless explicitly requested otherwise.
  - Preserve normalized error mapping unless explicitly requested otherwise.
- Expected AI output:
  - Implement only in-scope changes.
  - Add/update tests and docs as required.
  - Report executed validation commands and outcomes.

## Required Tests

- Existing tests to update:
  - `backend/tests/routers/test_rbac_admin.py`
  - `backend/tests/test_main.py` (if endpoint inventory assertions are impacted)
  - `backend/tests/routers/test_authorization_policy_coverage.py`
  - `backend/tests/test_permission_catalog_consistency.py` (if docs/catalog changes are required)
- New tests required:
  - Router tests for new read endpoints and permission denial behavior.
  - Service tests for role response mapping with `parent_role_ids`.
  - Repository tests for listing user roles and role users.
  - Migration/DB behavior test for unique `permissions.name` constraint (or equivalent repository-level conflict assertion).
- Documentation contracts to update and validate:
  - Endpoint catalog and authorization matrix consistency tests.

## Reviewer Validation Checklist

- [ ] Request references affected contracts and docs.
- [ ] Scope boundaries are explicit and realistic.
- [ ] Acceptance criteria are testable.
- [ ] AI execution constraints are explicit and reproducible.
- [ ] Test expectations are complete for changed behavior.
