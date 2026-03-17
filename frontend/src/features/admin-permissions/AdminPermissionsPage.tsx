import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { useSession } from "@/shared/auth/session";
import { userHasPermission } from "@/shared/iam/api";
import { IAM_PERMISSION } from "@/shared/iam/contracts";
import { t } from "@/shared/i18n/ui-text";
import {
  assignRbacRolePermission,
  readRbacPermissions,
  readRbacRoles,
  removeRbacRolePermission,
} from "@/shared/rbac/admin";
import { isRbacPermissionScope, RBAC_PERMISSION_SCOPES, type RbacPermissionScope } from "@/shared/rbac/contracts";
import {
  ADMIN_CARD_CLASS_NAME,
  ADMIN_COMPACT_DANGER_BUTTON_CLASS_NAME,
  ADMIN_FIELD_CLASS_NAME,
  ADMIN_LABEL_CLASS_NAME,
  ADMIN_MUTED_TEXT_CLASS_NAME,
  ADMIN_PAGE_CLASS_NAME,
  ADMIN_PRIMARY_BUTTON_CLASS_NAME,
  ADMIN_SECONDARY_BUTTON_CLASS_NAME,
  ADMIN_TITLE_CLASS_NAME,
  AdminErrorPanel,
} from "@/shared/rbac/ui";

const RBAC_ROLES_QUERY_KEY = ["rbac", "roles"] as const;
const RBAC_PERMISSIONS_QUERY_KEY = ["rbac", "permissions"] as const;
const UI = {
  add: "admin.roles.permissions.add",
  empty: "admin.roles.card.noPermissions",
  help: "admin.pm.help",
  list: "admin.pm.list",
  loading: "admin.common.loading",
  manual: "admin.pm.manual",
  missing: "admin.pm.missing",
  permissions: "admin.roles.card.permissions",
  placeholder: "admin.as.placeholder",
  remove: "admin.roles.permissions.remove",
  rid: "admin.as.rid",
  roleName: "admin.roles.create.name",
  rolesEmpty: "admin.roles.list.empty",
  scope: "admin.roles.permissions.scope.label",
  select: "admin.roles.permissions.select",
  title: "admin.pm.title",
} as const;

const parsePositiveId = (value: string): number | null => {
  const parsedValue = Number(value);
  return Number.isInteger(parsedValue) && parsedValue > 0 ? parsedValue : null;
};

const toCatalogValue = <T extends { id: number }>(items: readonly T[], selectedValue: string): string =>
  items.some((item) => String(item.id) === selectedValue) ? selectedValue : "";

export const AdminPermissionsPage = () => {
  const queryClient = useQueryClient();
  const session = useSession();
  const [selectedRoleIdInput, setSelectedRoleIdInput] = useState("");
  const [selectedPermissionId, setSelectedPermissionId] = useState("");
  const [selectedScopeInput, setSelectedScopeInput] = useState("");

  const selectedRoleId = parsePositiveId(selectedRoleIdInput);
  const selectedScope = isRbacPermissionScope(selectedScopeInput) ? selectedScopeInput : null;
  const canReadRolesCatalog = userHasPermission(session.data, IAM_PERMISSION.ROLES_MANAGE);

  const rolesQuery = useQuery({
    queryKey: RBAC_ROLES_QUERY_KEY,
    queryFn: readRbacRoles,
    enabled: canReadRolesCatalog,
  });

  const permissionsQuery = useQuery({
    queryKey: RBAC_PERMISSIONS_QUERY_KEY,
    queryFn: readRbacPermissions,
  });

  const assignMutation = useMutation({
    mutationFn: ({ permissionId, roleId, scope }: { permissionId: string; roleId: number; scope: RbacPermissionScope }) =>
      assignRbacRolePermission(roleId, permissionId, { scope }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: RBAC_ROLES_QUERY_KEY });
    },
  });

  const removeMutation = useMutation({
    mutationFn: ({ permissionId, roleId }: { permissionId: string; roleId: number }) =>
      removeRbacRolePermission(roleId, permissionId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: RBAC_ROLES_QUERY_KEY });
    },
  });

  const roles = rolesQuery.data ?? [];
  const permissions = permissionsQuery.data ?? [];
  const selectedRole = roles.find((role) => role.id === selectedRoleId) ?? null;
  const isMutating = assignMutation.isPending || removeMutation.isPending;
  const assignSelectedPermission =
    selectedRoleId !== null && selectedPermissionId !== "" && selectedScope !== null
      ? () => {
          assignMutation.reset();
          assignMutation.mutate({
            permissionId: selectedPermissionId,
            roleId: selectedRoleId,
            scope: selectedScope,
          });
        }
      : undefined;
  const removeSelectedPermission =
    selectedRoleId !== null && selectedPermissionId !== ""
      ? () => {
          removeMutation.reset();
          removeMutation.mutate({ permissionId: selectedPermissionId, roleId: selectedRoleId });
        }
      : undefined;
  const workspaceError = permissionsQuery.error ?? assignMutation.error ?? removeMutation.error;
  const canAssign = assignSelectedPermission !== undefined && !isMutating;
  const canRemoveSelected = removeSelectedPermission !== undefined && !isMutating;

  return (
    <main className={ADMIN_PAGE_CLASS_NAME}>
      <header>
        <h1 className={ADMIN_TITLE_CLASS_NAME}>{t(UI.title)}</h1>
      </header>

      <AdminErrorPanel error={workspaceError} />

      <section className="grid gap-6 lg:grid-cols-2">
        <article className={ADMIN_CARD_CLASS_NAME}>
          <h2 className="text-lg font-semibold">{t(UI.roleName)}</h2>
          {canReadRolesCatalog ? (
            rolesQuery.isPending ? (
              <p className={`mt-3 ${ADMIN_MUTED_TEXT_CLASS_NAME}`}>{t(UI.loading)}</p>
            ) : rolesQuery.error ? (
              <div className="mt-3">
                <AdminErrorPanel error={rolesQuery.error} />
              </div>
            ) : roles.length > 0 ? (
              <label className="mt-3 block">
                <span className={ADMIN_LABEL_CLASS_NAME}>{t(UI.roleName)}</span>
                <select
                  className={ADMIN_FIELD_CLASS_NAME}
                  onChange={(event) => setSelectedRoleIdInput(event.target.value)}
                  value={toCatalogValue(roles, selectedRoleIdInput)}
                >
                  <option value="">-</option>
                  {roles.map((role) => (
                    <option key={role.id} value={role.id}>
                      {role.name}
                    </option>
                  ))}
                </select>
              </label>
            ) : (
              <p className={`mt-3 ${ADMIN_MUTED_TEXT_CLASS_NAME}`}>{t(UI.rolesEmpty)}</p>
            )
          ) : (
            <p className={`mt-3 ${ADMIN_MUTED_TEXT_CLASS_NAME}`}>{t(UI.manual)}</p>
          )}

          <label className="mt-4 block">
            <span className={ADMIN_LABEL_CLASS_NAME}>{t(UI.rid)}</span>
            <input
              className={ADMIN_FIELD_CLASS_NAME}
              inputMode="numeric"
              min="1"
              onChange={(event) => setSelectedRoleIdInput(event.target.value)}
              type="number"
              value={selectedRoleIdInput}
            />
          </label>
        </article>

        <article className={ADMIN_CARD_CLASS_NAME}>
          <h2 className="text-lg font-semibold">{t(UI.permissions)}</h2>
          {permissionsQuery.isPending ? (
            <p className={`mt-3 ${ADMIN_MUTED_TEXT_CLASS_NAME}`}>{t(UI.loading)}</p>
          ) : permissionsQuery.error ? (
            <div className="mt-3">
              <AdminErrorPanel error={permissionsQuery.error} />
            </div>
          ) : permissions.length > 0 ? (
            <>
              <label className="mt-3 block">
                <span className={ADMIN_LABEL_CLASS_NAME}>{t(UI.select)}</span>
                <select
                  className={ADMIN_FIELD_CLASS_NAME}
                  onChange={(event) => setSelectedPermissionId(event.target.value)}
                  value={selectedPermissionId}
                >
                  <option value="">-</option>
                  {permissions.map((permission) => (
                    <option key={permission.id} value={permission.id}>
                      {permission.name}
                    </option>
                  ))}
                </select>
              </label>
              <label className="mt-4 block">
                <span className={ADMIN_LABEL_CLASS_NAME}>{t(UI.scope)}</span>
                <select
                  className={ADMIN_FIELD_CLASS_NAME}
                  onChange={(event) => setSelectedScopeInput(event.target.value)}
                  value={selectedScopeInput}
                >
                  <option value="">-</option>
                  {RBAC_PERMISSION_SCOPES.map((scope) => (
                    <option key={scope} value={scope}>
                      {scope}
                    </option>
                  ))}
                </select>
              </label>
              <p className={`mt-3 ${ADMIN_MUTED_TEXT_CLASS_NAME}`}>{t(UI.help)}</p>
              <div className="mt-4 flex flex-wrap gap-3">
                <button
                  className={ADMIN_PRIMARY_BUTTON_CLASS_NAME}
                  disabled={!canAssign}
                  onClick={assignSelectedPermission}
                  type="button"
                >
                  {t(UI.add)}
                </button>
                <button
                  className={ADMIN_SECONDARY_BUTTON_CLASS_NAME}
                  disabled={!canRemoveSelected}
                  onClick={removeSelectedPermission}
                  type="button"
                >
                  {t(UI.remove)}
                </button>
              </div>
            </>
          ) : (
            <p className={`mt-3 ${ADMIN_MUTED_TEXT_CLASS_NAME}`}>{t(UI.empty)}</p>
          )}
        </article>
      </section>

      <article className={ADMIN_CARD_CLASS_NAME}>
        <h2 className="text-lg font-semibold">{t(UI.list)}</h2>
        {selectedRoleId === null ? (
          <p className={`mt-3 ${ADMIN_MUTED_TEXT_CLASS_NAME}`}>{t(UI.placeholder)}</p>
        ) : !canReadRolesCatalog ? (
          <p className={`mt-3 ${ADMIN_MUTED_TEXT_CLASS_NAME}`}>{t(UI.manual)}</p>
        ) : rolesQuery.isPending ? (
          <p className={`mt-3 ${ADMIN_MUTED_TEXT_CLASS_NAME}`}>{t(UI.loading)}</p>
        ) : rolesQuery.error ? (
          <div className="mt-3">
            <AdminErrorPanel error={rolesQuery.error} />
          </div>
        ) : !selectedRole ? (
          <p className={`mt-3 ${ADMIN_MUTED_TEXT_CLASS_NAME}`}>{t(UI.missing)}</p>
        ) : selectedRole.permissions.length === 0 ? (
          <p className={`mt-3 ${ADMIN_MUTED_TEXT_CLASS_NAME}`}>{t(UI.empty)}</p>
        ) : (
          <ul className="mt-4 space-y-3">
            {selectedRole.permissions.map((permission) => (
              <li
                className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-[var(--app-border)] px-3 py-3"
                key={permission.id}
              >
                <div className="text-sm">
                  <p className="font-semibold">{permission.name}</p>
                  <p className="text-xs text-[var(--app-subtle)]">
                    {permission.id} - {t(UI.scope)}: {permission.scope}
                  </p>
                </div>
                <button
                  className={ADMIN_COMPACT_DANGER_BUTTON_CLASS_NAME}
                  onClick={() => {
                    removeMutation.reset();
                    removeMutation.mutate({ permissionId: permission.id, roleId: selectedRoleId });
                  }}
                  type="button"
                >
                  {t(UI.remove)}
                </button>
              </li>
            ))}
          </ul>
        )}
      </article>
    </main>
  );
};
