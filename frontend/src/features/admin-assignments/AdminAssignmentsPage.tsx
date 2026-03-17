import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { useSession } from "@/shared/auth/session";
import { userHasPermission } from "@/shared/iam/api";
import { IAM_PERMISSION } from "@/shared/iam/contracts";
import { t } from "@/shared/i18n/ui-text";
import {
  assignRbacUserRole,
  readAdminUsers,
  readRbacRoleUsers,
  readRbacRoles,
  readRbacUserRoles,
  removeRbacUserRole,
} from "@/shared/rbac/admin";
import {
  ADMIN_CARD_CLASS_NAME,
  ADMIN_COMPACT_DANGER_BUTTON_CLASS_NAME,
  ADMIN_FIELD_CLASS_NAME,
  ADMIN_LABEL_CLASS_NAME,
  ADMIN_MUTED_TEXT_CLASS_NAME,
  ADMIN_PAGE_CLASS_NAME,
  ADMIN_PRIMARY_BUTTON_CLASS_NAME,
  ADMIN_TITLE_CLASS_NAME,
  AdminErrorPanel,
} from "@/shared/rbac/ui";

const RBAC_USERS_QUERY_KEY = ["rbac", "users"] as const;
const RBAC_ROLES_QUERY_KEY = ["rbac", "roles"] as const;
const RBAC_ASSIGNMENTS_QUERY_KEY = ["rbac", "assignments"] as const;
const UI = {
  loading: "admin.common.loading",
  placeholder: "admin.as.placeholder",
  remove: "admin.roles.permissions.remove",
  rid: "admin.as.rid",
  roleEmpty: "admin.as.rEmpty",
  roleLabel: "admin.users.columns.roles",
  roleList: "admin.as.rTitle",
  rolesEmpty: "admin.roles.list.empty",
  submit: "admin.as.submit",
  submitPending: "admin.as.pending",
  title: "admin.as.title",
  uid: "admin.as.uid",
  userEmpty: "admin.as.uEmpty",
  userLabel: "admin.users.columns.username",
  userList: "admin.as.uTitle",
  usersEmpty: "admin.users.list.empty",
} as const;

const parsePositiveId = (value: string): number | null => {
  const parsedValue = Number(value);
  return Number.isInteger(parsedValue) && parsedValue > 0 ? parsedValue : null;
};

const toCatalogValue = <T extends { id: number }>(items: readonly T[], selectedValue: string): string =>
  items.some((item) => String(item.id) === selectedValue) ? selectedValue : "";

export const AdminAssignmentsPage = () => {
  const queryClient = useQueryClient();
  const session = useSession();
  const [selectedUserIdInput, setSelectedUserIdInput] = useState("");
  const [selectedRoleIdInput, setSelectedRoleIdInput] = useState("");

  const selectedUserId = parsePositiveId(selectedUserIdInput);
  const selectedRoleId = parsePositiveId(selectedRoleIdInput);
  const canReadUsersCatalog = userHasPermission(session.data, IAM_PERMISSION.USERS_MANAGE);
  const canReadRolesCatalog = userHasPermission(session.data, IAM_PERMISSION.ROLES_MANAGE);

  const usersQuery = useQuery({
    queryKey: RBAC_USERS_QUERY_KEY,
    queryFn: readAdminUsers,
    enabled: canReadUsersCatalog,
  });

  const rolesQuery = useQuery({
    queryKey: RBAC_ROLES_QUERY_KEY,
    queryFn: readRbacRoles,
    enabled: canReadRolesCatalog,
  });

  const userRolesQuery = useQuery({
    queryKey: [...RBAC_ASSIGNMENTS_QUERY_KEY, "user-roles", selectedUserId] as const,
    queryFn: () => readRbacUserRoles(selectedUserId!),
    enabled: selectedUserId !== null,
  });

  const roleUsersQuery = useQuery({
    queryKey: [...RBAC_ASSIGNMENTS_QUERY_KEY, "role-users", selectedRoleId] as const,
    queryFn: () => readRbacRoleUsers(selectedRoleId!),
    enabled: selectedRoleId !== null,
  });

  const assignMutation = useMutation({
    mutationFn: ({ userId, roleId }: { userId: number; roleId: number }) => assignRbacUserRole(userId, roleId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: RBAC_ASSIGNMENTS_QUERY_KEY });
    },
  });

  const removeMutation = useMutation({
    mutationFn: ({ userId, roleId }: { userId: number; roleId: number }) => removeRbacUserRole(userId, roleId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: RBAC_ASSIGNMENTS_QUERY_KEY });
    },
  });

  const users = usersQuery.data ?? [];
  const roles = rolesQuery.data ?? [];
  const userRoles = userRolesQuery.data ?? [];
  const roleUsers = roleUsersQuery.data ?? [];
  const isMutating = assignMutation.isPending || removeMutation.isPending;
  const assignSelection =
    selectedUserId !== null && selectedRoleId !== null
      ? () => {
          assignMutation.reset();
          assignMutation.mutate({ userId: selectedUserId, roleId: selectedRoleId });
        }
      : undefined;
  const canAssign = assignSelection !== undefined && !isMutating;
  const workspaceError = assignMutation.error ?? removeMutation.error;

  return (
    <main className={ADMIN_PAGE_CLASS_NAME}>
      <header>
        <h1 className={ADMIN_TITLE_CLASS_NAME}>{t(UI.title)}</h1>
      </header>

      <AdminErrorPanel error={workspaceError} />

      <section className="grid gap-6 md:grid-cols-2">
        <article className={ADMIN_CARD_CLASS_NAME}>
          <h2 className="text-lg font-semibold">{t(UI.userLabel)}</h2>
          {canReadUsersCatalog ? (
            usersQuery.isPending ? (
              <p className={`mt-3 ${ADMIN_MUTED_TEXT_CLASS_NAME}`}>{t(UI.loading)}</p>
            ) : usersQuery.error ? (
              <div className="mt-3">
                <AdminErrorPanel error={usersQuery.error} />
              </div>
            ) : users.length > 0 ? (
              <label className="mt-3 block">
                <span className={ADMIN_LABEL_CLASS_NAME}>{t(UI.userLabel)}</span>
                <select
                  className={ADMIN_FIELD_CLASS_NAME}
                  onChange={(event) => setSelectedUserIdInput(event.target.value)}
                  value={toCatalogValue(users, selectedUserIdInput)}
                >
                  <option value="">-</option>
                  {users.map((user) => (
                    <option key={user.id} value={user.id}>
                      {user.username}
                    </option>
                  ))}
                </select>
              </label>
            ) : (
              <p className={`mt-3 ${ADMIN_MUTED_TEXT_CLASS_NAME}`}>{t(UI.usersEmpty)}</p>
            )
          ) : null}

          <label className="mt-4 block">
            <span className={ADMIN_LABEL_CLASS_NAME}>{t(UI.uid)}</span>
            <input
              className={ADMIN_FIELD_CLASS_NAME}
              inputMode="numeric"
              min="1"
              onChange={(event) => setSelectedUserIdInput(event.target.value)}
              type="number"
              value={selectedUserIdInput}
            />
          </label>
        </article>

        <article className={ADMIN_CARD_CLASS_NAME}>
          <h2 className="text-lg font-semibold">{t(UI.roleLabel)}</h2>
          {canReadRolesCatalog ? (
            rolesQuery.isPending ? (
              <p className={`mt-3 ${ADMIN_MUTED_TEXT_CLASS_NAME}`}>{t(UI.loading)}</p>
            ) : rolesQuery.error ? (
              <div className="mt-3">
                <AdminErrorPanel error={rolesQuery.error} />
              </div>
            ) : roles.length > 0 ? (
              <label className="mt-3 block">
                <span className={ADMIN_LABEL_CLASS_NAME}>{t(UI.roleLabel)}</span>
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
          ) : null}

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
      </section>

      <div className="flex justify-end">
        <button
          className={ADMIN_PRIMARY_BUTTON_CLASS_NAME}
          disabled={!canAssign}
          onClick={assignSelection}
          type="button"
        >
          {assignMutation.isPending ? t(UI.submitPending) : t(UI.submit)}
        </button>
      </div>

      <section className="grid gap-6 lg:grid-cols-2">
        <article className={ADMIN_CARD_CLASS_NAME}>
          <h2 className="text-lg font-semibold">{t(UI.userList)}</h2>
          {selectedUserId === null ? (
            <p className={`mt-3 ${ADMIN_MUTED_TEXT_CLASS_NAME}`}>{t(UI.placeholder)}</p>
          ) : userRolesQuery.isPending ? (
            <p className={`mt-3 ${ADMIN_MUTED_TEXT_CLASS_NAME}`}>{t(UI.loading)}</p>
          ) : userRolesQuery.error ? (
            <div className="mt-3">
              <AdminErrorPanel error={userRolesQuery.error} />
            </div>
          ) : userRoles.length === 0 ? (
            <p className={`mt-3 ${ADMIN_MUTED_TEXT_CLASS_NAME}`}>{t(UI.userEmpty)}</p>
          ) : (
            <ul className="mt-4 space-y-3">
              {userRoles.map((role) => (
                <li
                  className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-[var(--app-border)] px-3 py-3"
                  key={role.id}
                >
                  <div className="text-sm">
                    <p className="font-semibold">{role.name}</p>
                    <p className="text-xs text-[var(--app-subtle)]">{role.id}</p>
                  </div>
                  <button
                    className={ADMIN_COMPACT_DANGER_BUTTON_CLASS_NAME}
                    onClick={() => {
                      removeMutation.reset();
                      removeMutation.mutate({ userId: selectedUserId, roleId: role.id });
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

        <article className={ADMIN_CARD_CLASS_NAME}>
          <h2 className="text-lg font-semibold">{t(UI.roleList)}</h2>
          {selectedRoleId === null ? (
            <p className={`mt-3 ${ADMIN_MUTED_TEXT_CLASS_NAME}`}>{t(UI.placeholder)}</p>
          ) : roleUsersQuery.isPending ? (
            <p className={`mt-3 ${ADMIN_MUTED_TEXT_CLASS_NAME}`}>{t(UI.loading)}</p>
          ) : roleUsersQuery.error ? (
            <div className="mt-3">
              <AdminErrorPanel error={roleUsersQuery.error} />
            </div>
          ) : roleUsers.length === 0 ? (
            <p className={`mt-3 ${ADMIN_MUTED_TEXT_CLASS_NAME}`}>{t(UI.roleEmpty)}</p>
          ) : (
            <ul className="mt-4 space-y-3">
              {roleUsers.map((user) => (
                <li
                  className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-[var(--app-border)] px-3 py-3"
                  key={user.id}
                >
                  <div className="text-sm">
                    <p className="font-semibold">{user.username}</p>
                    <p className="text-xs text-[var(--app-subtle)]">{user.id}</p>
                  </div>
                  <button
                    className={ADMIN_COMPACT_DANGER_BUTTON_CLASS_NAME}
                    onClick={() => {
                      removeMutation.reset();
                      removeMutation.mutate({ userId: user.id, roleId: selectedRoleId });
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
      </section>
    </main>
  );
};
