import { FormEvent, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { useSession } from "@/shared/auth/session";
import { userHasPermission } from "@/shared/iam/api";
import { IAM_PERMISSION } from "@/shared/iam/contracts";
import { t } from "@/shared/i18n/ui-text";
import {
  createAdminUser,
  readAdminUsers,
  readRbacRoles,
  softDeleteAdminUser,
  updateAdminUser,
  type CreateAdminUserPayload,
  type UpdateAdminUserPayload,
} from "@/shared/rbac/admin";
import { type AdminUser } from "@/shared/rbac/contracts";
import {
  ADMIN_CARD_CLASS_NAME,
  ADMIN_COMPACT_DANGER_BUTTON_CLASS_NAME,
  ADMIN_COMPACT_SECONDARY_BUTTON_CLASS_NAME,
  ADMIN_FIELD_CLASS_NAME,
  ADMIN_FORM_GRID_CLASS_NAME,
  ADMIN_LABEL_CLASS_NAME,
  ADMIN_MUTED_TEXT_CLASS_NAME,
  ADMIN_PAGE_CLASS_NAME,
  ADMIN_PRIMARY_BUTTON_CLASS_NAME,
  ADMIN_SECONDARY_BUTTON_CLASS_NAME,
  ADMIN_TITLE_CLASS_NAME,
  AdminErrorPanel,
} from "@/shared/rbac/ui";
import { CenteredMessage } from "@/shared/ui/CenteredMessage";

const RBAC_USERS_QUERY_KEY = ["rbac", "users"] as const;
const RBAC_ROLES_QUERY_KEY = ["rbac", "roles"] as const;

interface CreateUserFormState {
  username: string;
  password: string;
  roleIds: number[];
}

interface EditUserFormState {
  username: string;
  currentPassword: string;
  newPassword: string;
  disabled: boolean;
  roleIds: number[];
}

const INITIAL_CREATE_USER_FORM_STATE: CreateUserFormState = {
  username: "",
  password: "",
  roleIds: [],
};

const getRoleIdsFromMultiSelect = (selectElement: HTMLSelectElement): number[] =>
  Array.from(selectElement.selectedOptions)
    .map((option) => Number(option.value))
    .filter((value) => Number.isInteger(value) && value > 0);

const toCreateUserPayload = (
  formState: CreateUserFormState,
  includeRoleAssignments: boolean,
): CreateAdminUserPayload => {
  const payload: CreateAdminUserPayload = {
    username: formState.username,
    password: formState.password,
  };
  if (includeRoleAssignments) {
    payload.role_ids = formState.roleIds;
  }
  return payload;
};

const toUpdateUserPayload = (formState: EditUserFormState, includeRoleAssignments: boolean): UpdateAdminUserPayload => {
  const payload: UpdateAdminUserPayload = {
    username: formState.username,
    disabled: formState.disabled,
  };
  if (includeRoleAssignments) {
    payload.role_ids = formState.roleIds;
  }

  if (formState.currentPassword.trim() || formState.newPassword.trim()) {
    payload.current_password = formState.currentPassword;
    payload.new_password = formState.newPassword;
  }

  return payload;
};

const toEditFormState = (user: AdminUser): EditUserFormState => ({
  username: user.username,
  currentPassword: "",
  newPassword: "",
  disabled: user.disabled,
  roleIds: user.role_ids,
});

export const AdminUsersPage = () => {
  const queryClient = useQueryClient();
  const session = useSession();
  const [createFormState, setCreateFormState] = useState<CreateUserFormState>(INITIAL_CREATE_USER_FORM_STATE);
  const [editingUser, setEditingUser] = useState<AdminUser | null>(null);
  const [editFormState, setEditFormState] = useState<EditUserFormState | null>(null);
  const canManageUserRoles = userHasPermission(session.data, IAM_PERMISSION.USER_ROLES_MANAGE);

  const usersQuery = useQuery({
    queryKey: RBAC_USERS_QUERY_KEY,
    queryFn: readAdminUsers,
  });
  const rolesQuery = useQuery({
    queryKey: RBAC_ROLES_QUERY_KEY,
    queryFn: readRbacRoles,
  });

  const createMutation = useMutation({
    mutationFn: (payload: CreateAdminUserPayload) => createAdminUser(payload),
    onSuccess: async () => {
      setCreateFormState(INITIAL_CREATE_USER_FORM_STATE);
      await queryClient.invalidateQueries({ queryKey: RBAC_USERS_QUERY_KEY });
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ userId, payload }: { userId: number; payload: UpdateAdminUserPayload }) =>
      updateAdminUser(userId, payload),
    onSuccess: async () => {
      setEditingUser(null);
      setEditFormState(null);
      await queryClient.invalidateQueries({ queryKey: RBAC_USERS_QUERY_KEY });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (userId: number) => softDeleteAdminUser(userId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: RBAC_USERS_QUERY_KEY });
    },
  });

  const users = usersQuery.data ?? [];
  const roles = rolesQuery.data ?? [];
  const roleNameById = useMemo(
    () => new Map((rolesQuery.data ?? []).map((role) => [role.id, role.name])),
    [rolesQuery.data],
  );

  const pageError =
    usersQuery.error ?? rolesQuery.error ?? createMutation.error ?? updateMutation.error ?? deleteMutation.error;

  if (usersQuery.isPending || rolesQuery.isPending) {
    return <CenteredMessage title={t("admin.common.loading")} />;
  }

  const submitCreateForm = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    createMutation.reset();
    createMutation.mutate(toCreateUserPayload(createFormState, canManageUserRoles));
  };

  const submitEditForm = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!editingUser || !editFormState) {
      return;
    }
    updateMutation.reset();
    updateMutation.mutate({
      userId: editingUser.id,
      payload: toUpdateUserPayload(editFormState, canManageUserRoles),
    });
  };

  const startEditingUser = (user: AdminUser) => {
    setEditingUser(user);
    setEditFormState(toEditFormState(user));
    updateMutation.reset();
  };

  const cancelEditingUser = () => {
    setEditingUser(null);
    setEditFormState(null);
    updateMutation.reset();
  };

  const confirmAndDeleteUser = (user: AdminUser) => {
    const confirmed = window.confirm(t("admin.users.actions.delete.confirm", { username: user.username }));
    if (!confirmed) {
      return;
    }
    deleteMutation.reset();
    deleteMutation.mutate(user.id);
  };

  return (
    <main className={ADMIN_PAGE_CLASS_NAME}>
      <header>
        <h1 className={ADMIN_TITLE_CLASS_NAME}>{t("admin.users.title")}</h1>
        <p className={`mt-2 ${ADMIN_MUTED_TEXT_CLASS_NAME}`}>{t("admin.users.subtitle")}</p>
      </header>

      <AdminErrorPanel error={pageError} />

      <section className={ADMIN_CARD_CLASS_NAME}>
        <h2 className="text-lg font-semibold">{t("admin.users.create.title")}</h2>
        <form className={ADMIN_FORM_GRID_CLASS_NAME} onSubmit={submitCreateForm}>
          <label className="block">
            <span className={ADMIN_LABEL_CLASS_NAME}>{t("admin.users.create.username")}</span>
            <input
              className={ADMIN_FIELD_CLASS_NAME}
              name="username"
              onChange={(event) =>
                setCreateFormState((previous) => ({ ...previous, username: event.target.value }))
              }
              required
              value={createFormState.username}
            />
          </label>

          <label className="block">
            <span className={ADMIN_LABEL_CLASS_NAME}>{t("admin.users.create.password")}</span>
            <input
              className={ADMIN_FIELD_CLASS_NAME}
              name="password"
              onChange={(event) =>
                setCreateFormState((previous) => ({ ...previous, password: event.target.value }))
              }
              required
              type="password"
              value={createFormState.password}
            />
          </label>

          {canManageUserRoles ? (
            <label className="block md:col-span-2">
              <span className={ADMIN_LABEL_CLASS_NAME}>{t("admin.users.create.roles")}</span>
              <select
                className={`min-h-28 ${ADMIN_FIELD_CLASS_NAME}`}
                multiple
                onChange={(event) => {
                  const selectedRoleIds = getRoleIdsFromMultiSelect(event.currentTarget);
                  setCreateFormState((previous) => ({
                    ...previous,
                    roleIds: selectedRoleIds,
                  }));
                }}
                value={createFormState.roleIds.map(String)}
              >
                {roles.map((role) => (
                  <option key={role.id} value={role.id}>
                    {role.name}
                  </option>
                ))}
              </select>
            </label>
          ) : null}

          <div className="md:col-span-2">
            <button
              className={ADMIN_PRIMARY_BUTTON_CLASS_NAME}
              disabled={createMutation.isPending}
              type="submit"
            >
              {createMutation.isPending
                ? t("admin.users.create.submit.pending")
                : t("admin.users.create.submit")}
            </button>
          </div>
        </form>
      </section>

      <section className={ADMIN_CARD_CLASS_NAME}>
        <h2 className="text-lg font-semibold">{t("admin.users.list.title")}</h2>
        {users.length === 0 ? (
          <p className={`mt-3 ${ADMIN_MUTED_TEXT_CLASS_NAME}`}>{t("admin.users.list.empty")}</p>
        ) : (
          <div className="mt-3 overflow-x-auto">
            <table className="w-full min-w-[700px] border-collapse text-left text-sm">
              <thead>
                <tr className="border-b border-[var(--app-border)]">
                  <th className="px-2 py-2 font-semibold">{t("admin.users.columns.username")}</th>
                  <th className="px-2 py-2 font-semibold">{t("admin.users.columns.status")}</th>
                  <th className="px-2 py-2 font-semibold">{t("admin.users.columns.roles")}</th>
                  <th className="px-2 py-2 font-semibold">{t("admin.users.columns.actions")}</th>
                </tr>
              </thead>
              <tbody>
                {users.map((user) => (
                  <tr className="border-b border-[var(--app-border)]" key={user.id}>
                    <td className="px-2 py-3">{user.username}</td>
                    <td className="px-2 py-3">
                      {user.disabled ? t("admin.users.status.disabled") : t("admin.users.status.active")}
                    </td>
                    <td className="px-2 py-3">
                      {user.role_ids.length > 0
                        ? user.role_ids.map((roleId) => roleNameById.get(roleId) ?? String(roleId)).join(", ")
                        : "-"}
                    </td>
                    <td className="px-2 py-3">
                      <div className="flex flex-wrap gap-2">
                        <button
                          className={ADMIN_COMPACT_SECONDARY_BUTTON_CLASS_NAME}
                          onClick={() => startEditingUser(user)}
                          type="button"
                        >
                          {t("admin.users.actions.edit")}
                        </button>
                        <button
                          className={ADMIN_COMPACT_DANGER_BUTTON_CLASS_NAME}
                          disabled={deleteMutation.isPending}
                          onClick={() => confirmAndDeleteUser(user)}
                          type="button"
                        >
                          {t("admin.users.actions.delete")}
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {editingUser && editFormState ? (
        <section className={ADMIN_CARD_CLASS_NAME}>
          <h2 className="text-lg font-semibold">
            {t("admin.users.edit.title")}: {editingUser.username}
          </h2>
          <form className={ADMIN_FORM_GRID_CLASS_NAME} onSubmit={submitEditForm}>
            <label className="block">
              <span className={ADMIN_LABEL_CLASS_NAME}>{t("admin.users.edit.username")}</span>
              <input
                className={ADMIN_FIELD_CLASS_NAME}
                name="edit-username"
                onChange={(event) =>
                  setEditFormState((previous) => ({ ...previous!, username: event.target.value }))
                }
                required
                value={editFormState.username}
              />
            </label>

            <label className="block">
              <span className={ADMIN_LABEL_CLASS_NAME}>{t("admin.users.edit.currentPassword")}</span>
              <input
                className={ADMIN_FIELD_CLASS_NAME}
                name="edit-current-password"
                onChange={(event) =>
                  setEditFormState((previous) => ({ ...previous!, currentPassword: event.target.value }))
                }
                type="password"
                value={editFormState.currentPassword}
              />
            </label>

            <label className="block">
              <span className={ADMIN_LABEL_CLASS_NAME}>{t("admin.users.edit.newPassword")}</span>
              <input
                className={ADMIN_FIELD_CLASS_NAME}
                name="edit-new-password"
                onChange={(event) =>
                  setEditFormState((previous) => ({ ...previous!, newPassword: event.target.value }))
                }
                type="password"
                value={editFormState.newPassword}
              />
            </label>

            <label className="flex items-center gap-2 pt-8">
              <input
                checked={editFormState.disabled}
                onChange={(event) =>
                  setEditFormState((previous) => ({ ...previous!, disabled: event.target.checked }))
                }
                type="checkbox"
              />
              <span className="text-sm font-medium">{t("admin.users.edit.disabled")}</span>
            </label>

            {canManageUserRoles ? (
              <label className="block md:col-span-2">
                <span className={ADMIN_LABEL_CLASS_NAME}>{t("admin.users.edit.roles")}</span>
                <select
                  className={`min-h-28 ${ADMIN_FIELD_CLASS_NAME}`}
                  multiple
                  onChange={(event) => {
                    const selectedRoleIds = getRoleIdsFromMultiSelect(event.currentTarget);
                    setEditFormState((previous) => ({
                      ...previous!,
                      roleIds: selectedRoleIds,
                    }));
                  }}
                  value={editFormState.roleIds.map(String)}
                >
                  {roles.map((role) => (
                    <option key={role.id} value={role.id}>
                      {role.name}
                    </option>
                  ))}
                </select>
              </label>
            ) : null}

            <div className="flex gap-3 md:col-span-2">
              <button
                className={ADMIN_PRIMARY_BUTTON_CLASS_NAME}
                disabled={updateMutation.isPending}
                type="submit"
              >
                {updateMutation.isPending ? t("admin.users.edit.submit.pending") : t("admin.users.edit.submit")}
              </button>
              <button
                className={ADMIN_SECONDARY_BUTTON_CLASS_NAME}
                onClick={cancelEditingUser}
                type="button"
              >
                {t("admin.users.edit.cancel")}
              </button>
            </div>
          </form>
        </section>
      ) : null}
    </main>
  );
};
