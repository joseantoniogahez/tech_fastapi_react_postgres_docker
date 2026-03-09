# Feature Request: Admin User Management (CRUD + Soft Delete)

## How to Use This Template With the AI Assistant

1. Fill every section with concrete details (no placeholders).
1. Reference backend docs/contracts the assistant must follow.
1. Define hard scope boundaries and required validations.
1. Paste the completed template in your request to the assistant.

## Problem and Goal

The backend currently supports account self-service (`/v1/users/register`, `/v1/users/me`) and user-role assignment, but it does not provide an administrative user management API.
The goal is to add admin-level user CRUD operations with logical deletion (soft delete), where deleting a user sets `disabled = true` and never removes the row physically.

## Scope (In / Out)

### In Scope

- Add admin user management endpoints under `/v1/rbac/users`:
- `GET /v1/rbac/users` (list users, including `id`, `username`, `disabled`, and assigned role IDs).
- `GET /v1/rbac/users/{user_id}` (single user detail with assigned role IDs).
- `POST /v1/rbac/users` (create user with `username`, `password`, optional `role_ids`).
- `PUT /v1/rbac/users/{user_id}` (update `username`, optional password rotation, optional `disabled` toggle, optional full role set replacement).
- `DELETE /v1/rbac/users/{user_id}` (soft delete only, sets `disabled=true`, idempotent 204 if already disabled).
- Reuse existing username normalization and password policy from auth domain.
- Keep write operations in `UnitOfWork`.
- Keep existing `/v1/users/register` and `/v1/users/me` behavior unchanged.

### Out of Scope

- Physical user deletion from the database.
- Password reset by email, OTP, or external identity providers.
- Multi-tenant authorization redesign.
- Bulk user import/export.
- Pagination redesign for unrelated endpoints.

## API, Data, and Authorization Implications

- Add a new permission to `PERMISSION_CATALOG`:
- `users:manage` with display name `Manage users`.
- Add authorization dependency alias for user admin management (for example `RBACUserAdminAuth`).
- Require `users:manage` (scope `any`) for all new `/v1/rbac/users*` endpoints.
- Keep `user_roles:manage` behavior for existing assignment endpoints unless explicitly migrated in this change.
- API contracts:
- `AdminUserResponse`: `id`, `username`, `disabled`, `role_ids`.
- `CreateAdminUserRequest`: `username`, `password`, `role_ids?`.
- `UpdateAdminUserRequest`: `username?`, `current_password?`, `new_password?`, `disabled?`, `role_ids?`.
- Data model:
- No new user table columns required.
- Soft delete is implemented only by setting `users.disabled = true`.
- No cascade deletes in `user_roles` on soft delete.
- Docs/contracts to update:
- `backend/docs/operations/api_endpoints.md`
- `backend/docs/operations/authorization_matrix.md`
- `backend/docs/operations/authentication.md`
- `backend/docs/operations/error_mapping.md` (if new domain mapping details are introduced)

## Observability and Error Handling

- Keep normalized error payload contract unchanged: `{ detail, status, code, meta?, request_id }`.
- Expected error behavior:
- `400 invalid_input` for invalid payload/path/query.
- `401 unauthorized` for missing/invalid token.
- `403 forbidden` for missing `users:manage`.
- `404 not_found` for unknown `user_id`.
- `409 conflict` for duplicated normalized username.
- Ensure request completion and authorization decision logs remain present and consistent with current logging shape.

## Acceptance Criteria

- Admin can create, list, read, update, and soft-delete users via `/v1/rbac/users*`.
- `DELETE /v1/rbac/users/{user_id}` never deletes rows physically and always leaves `disabled=true`.
- Inactive users cannot authenticate (`POST /v1/token` returns `403 forbidden`).
- Username normalization and password policy match existing auth behavior.
- All new protected routes require `users:manage` and are documented in authorization matrix.
- API endpoint catalog and OpenAPI docs reflect the new contracts.
- Existing auth/rbac flows continue passing current tests without behavioral regression.

## AI Execution Constraints (Required)

- Docs the AI must read before coding (minimum):
  - `backend/docs/backend_playbook.md`
  - `backend/docs/operations/api_endpoints.md`
  - `backend/docs/operations/authorization_matrix.md`
  - `backend/docs/operations/authentication.md`
  - `backend/docs/operations/error_mapping.md`
  - `backend/docs/architecture/dependency_injection.md`
  - `backend/docs/architecture/unit_of_work.md`
  - `backend/docs/architecture/openapi_documentation.md`
- Allowed files/modules to change:
  - `backend/app/features/rbac/*`
  - `backend/app/core/authorization/*`
  - `backend/app/core/setup/dependencies.py`
  - `backend/tests/routers/test_rbac_admin.py`
  - `backend/tests/services/test_rbac.py`
  - `backend/tests/repositories/test_rbac_repository.py`
  - `backend/tests/test_permission_catalog_consistency.py`
  - `backend/docs/operations/*`
  - `backend/utils/rbac_bootstrap.py`
- Protected files/modules that must not change:
  - `backend/app/features/health/*`
  - `backend/app/features/outbox/*`
  - `frontend/*`
- Expected AI output:
  - Implement behavior changes.
  - Add/update tests.
  - Update impacted contracts/docs.
  - Report executed validation commands and outcomes.

## Required Tests

- Router tests:
  - Authorization checks for each new `/v1/rbac/users*` endpoint.
  - Happy-path CRUD + soft-delete behavior.
  - Not-found/conflict/validation cases.
- Service tests:
  - Username normalization and password policy reuse.
  - Soft-delete behavior and disabled toggle semantics.
- Repository tests:
  - User list/detail retrieval with role IDs.
  - Soft-delete update semantics.
- Documentation contract tests:
  - Update and pass endpoint/authorization contract tests.

## Reviewer Validation Checklist

- [ ] Request aligns with `backend/docs/backend_playbook.md`.
- [ ] Public endpoint contract impact is explicit.
- [ ] Permission and scope impact is explicit.
- [ ] AI execution constraints are explicit and enforceable.
- [ ] Test expectations are specific and complete.
