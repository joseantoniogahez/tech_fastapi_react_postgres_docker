import { FormEvent, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { appendRequestIdDiagnostic, ApiError, getApiErrorRequestId } from "@/shared/api/errors";
import { useSession } from "@/shared/auth/session";
import { userHasPermission } from "@/shared/iam/api";
import { IAM_PERMISSION } from "@/shared/iam/contracts";
import { t } from "@/shared/i18n/ui-text";
import {
  assignRbacRoleInheritance,
  assignRbacRolePermission,
  createRbacRole,
  deleteRbacRole,
  readRbacPermissions,
  readRbacRoles,
  removeRbacRoleInheritance,
  removeRbacRolePermission,
  updateRbacRole,
} from "@/shared/rbac/admin";
import { CenteredMessage } from "@/shared/ui/CenteredMessage";

const RBAC_ROLES_QUERY_KEY = ["rbac", "roles"] as const;
const RBAC_PERMISSIONS_QUERY_KEY = ["rbac", "permissions"] as const;

const formatUiError = (error: unknown): string => {
  if (error instanceof ApiError) {
    return appendRequestIdDiagnostic(error.message, getApiErrorRequestId(error));
  }
  return t("admin.common.error.generic");
};

export const AdminRolesPage = () => {
  const queryClient = useQueryClient();
  const session = useSession();

  const [createRoleName, setCreateRoleName] = useState("");
  const [roleNameDraftById, setRoleNameDraftById] = useState<Record<number, string>>({});
  const [selectedParentByRoleId, setSelectedParentByRoleId] = useState<Record<number, string>>({});
  const [selectedPermissionByRoleId, setSelectedPermissionByRoleId] = useState<Record<number, string>>({});

  const rolesQuery = useQuery({
    queryKey: RBAC_ROLES_QUERY_KEY,
    queryFn: readRbacRoles,
  });
  const permissionsQuery = useQuery({
    queryKey: RBAC_PERMISSIONS_QUERY_KEY,
    queryFn: readRbacPermissions,
  });

  const createRoleMutation = useMutation({
    mutationFn: (name: string) => createRbacRole({ name }),
    onSuccess: async () => {
      setCreateRoleName("");
      await queryClient.invalidateQueries({ queryKey: RBAC_ROLES_QUERY_KEY });
    },
  });

  const updateRoleMutation = useMutation({
    mutationFn: ({ roleId, name }: { roleId: number; name: string }) => updateRbacRole(roleId, { name }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: RBAC_ROLES_QUERY_KEY });
    },
  });

  const deleteRoleMutation = useMutation({
    mutationFn: (roleId: number) => deleteRbacRole(roleId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: RBAC_ROLES_QUERY_KEY });
    },
  });

  const addParentMutation = useMutation({
    mutationFn: ({ roleId, parentRoleId }: { roleId: number; parentRoleId: number }) =>
      assignRbacRoleInheritance(roleId, parentRoleId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: RBAC_ROLES_QUERY_KEY });
    },
  });

  const removeParentMutation = useMutation({
    mutationFn: ({ roleId, parentRoleId }: { roleId: number; parentRoleId: number }) =>
      removeRbacRoleInheritance(roleId, parentRoleId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: RBAC_ROLES_QUERY_KEY });
    },
  });

  const addPermissionMutation = useMutation({
    mutationFn: ({ roleId, permissionId }: { roleId: number; permissionId: string }) =>
      assignRbacRolePermission(roleId, permissionId, { scope: "any" }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: RBAC_ROLES_QUERY_KEY });
    },
  });

  const removePermissionMutation = useMutation({
    mutationFn: ({ roleId, permissionId }: { roleId: number; permissionId: string }) =>
      removeRbacRolePermission(roleId, permissionId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: RBAC_ROLES_QUERY_KEY });
    },
  });

  const roles = rolesQuery.data ?? [];
  const permissions = permissionsQuery.data ?? [];
  const canManageRolePermissions = userHasPermission(session.data, IAM_PERMISSION.ROLE_PERMISSIONS_MANAGE);

  const roleNameById = useMemo(
    () => new Map((rolesQuery.data ?? []).map((role) => [role.id, role.name])),
    [rolesQuery.data],
  );

  const pageError =
    rolesQuery.error ??
    permissionsQuery.error ??
    createRoleMutation.error ??
    updateRoleMutation.error ??
    deleteRoleMutation.error ??
    addParentMutation.error ??
    removeParentMutation.error ??
    addPermissionMutation.error ??
    removePermissionMutation.error;
  const errorMessage = pageError ? formatUiError(pageError) : null;

  if (rolesQuery.isPending || permissionsQuery.isPending) {
    return <CenteredMessage title={t("admin.common.loading")} />;
  }

  const submitCreateRole = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    createRoleMutation.reset();
    createRoleMutation.mutate(createRoleName);
  };

  const saveRoleName = (roleId: number, currentName: string) => {
    const roleNameDraft = roleNameDraftById[roleId] ?? currentName;
    updateRoleMutation.reset();
    updateRoleMutation.mutate({ roleId, name: roleNameDraft });
  };

  const confirmAndDeleteRole = (roleId: number, roleName: string) => {
    const confirmed = window.confirm(t("admin.roles.actions.delete.confirm", { roleName }));
    if (!confirmed) {
      return;
    }
    deleteRoleMutation.reset();
    deleteRoleMutation.mutate(roleId);
  };

  return (
    <main className="mx-auto flex w-full max-w-6xl flex-col gap-6 px-6 py-10">
      <header>
        <h1 className="text-3xl font-semibold tracking-tight">{t("admin.roles.title")}</h1>
        <p className="mt-2 text-sm text-[var(--app-subtle)]">{t("admin.roles.subtitle")}</p>
      </header>

      {errorMessage ? (
        <section className="rounded-2xl border border-red-200 bg-red-50 px-4 py-3">
          <h2 className="text-sm font-semibold text-red-800">{t("admin.common.error.title")}</h2>
          <p className="mt-1 text-sm text-red-700">{errorMessage}</p>
        </section>
      ) : null}

      <section className="rounded-2xl border border-[var(--app-border)] bg-[var(--app-surface)] p-5">
        <h2 className="text-lg font-semibold">{t("admin.roles.create.title")}</h2>
        <form className="mt-4 flex flex-wrap items-end gap-3" onSubmit={submitCreateRole}>
          <label className="min-w-72 flex-1">
            <span className="mb-2 block text-sm font-medium">{t("admin.roles.create.name")}</span>
            <input
              className="w-full rounded-xl border border-[var(--app-border)] px-3 py-2"
              onChange={(event) => setCreateRoleName(event.target.value)}
              required
              value={createRoleName}
            />
          </label>
          <button
            className="rounded-full bg-[var(--app-ink)] px-5 py-2 text-sm font-semibold text-[var(--app-surface)] disabled:opacity-70"
            disabled={createRoleMutation.isPending}
            type="submit"
          >
            {createRoleMutation.isPending
              ? t("admin.roles.create.submit.pending")
              : t("admin.roles.create.submit")}
          </button>
        </form>
      </section>

      {roles.length === 0 ? (
        <section className="rounded-2xl border border-[var(--app-border)] bg-[var(--app-surface)] p-5">
          <p className="text-sm text-[var(--app-subtle)]">{t("admin.roles.list.empty")}</p>
        </section>
      ) : (
        roles.map((role) => {
          const currentRoleNameDraft = roleNameDraftById[role.id] ?? role.name;
          const currentParentSelection = selectedParentByRoleId[role.id] ?? "";
          const currentPermissionSelection = selectedPermissionByRoleId[role.id] ?? "";
          const assignedPermissionIds = new Set(role.permissions.map((permission) => permission.id));

          return (
            <section
              className="rounded-2xl border border-[var(--app-border)] bg-[var(--app-surface)] p-5"
              key={role.id}
            >
              <div className="flex flex-wrap items-end gap-3">
                <label className="min-w-72 flex-1">
                  <span className="mb-2 block text-sm font-medium">{t("admin.roles.create.name")}</span>
                  <input
                    className="w-full rounded-xl border border-[var(--app-border)] px-3 py-2"
                    onChange={(event) =>
                      setRoleNameDraftById((previous) => ({ ...previous, [role.id]: event.target.value }))
                    }
                    value={currentRoleNameDraft}
                  />
                </label>
                <button
                  className="rounded-full border border-[var(--app-border)] px-4 py-2 text-sm font-semibold disabled:opacity-70"
                  disabled={updateRoleMutation.isPending}
                  onClick={() => saveRoleName(role.id, role.name)}
                  type="button"
                >
                  {updateRoleMutation.isPending
                    ? t("admin.roles.actions.update.pending")
                    : t("admin.roles.actions.update")}
                </button>
                <button
                  className="rounded-full border border-red-300 px-4 py-2 text-sm font-semibold text-red-700 disabled:opacity-70"
                  disabled={deleteRoleMutation.isPending}
                  onClick={() => confirmAndDeleteRole(role.id, role.name)}
                  type="button"
                >
                  {t("admin.roles.actions.delete")}
                </button>
              </div>

              <div className="mt-5 grid gap-5 lg:grid-cols-2">
                <article className="rounded-xl border border-[var(--app-border)] p-4">
                  <h3 className="text-sm font-semibold">{t("admin.roles.card.parents")}</h3>
                  <div className="mt-3 flex flex-wrap items-end gap-2">
                    <label className="min-w-52 flex-1">
                      <span className="mb-1 block text-xs font-medium">{t("admin.roles.parents.select")}</span>
                      <select
                        className="w-full rounded-xl border border-[var(--app-border)] px-3 py-2 text-sm"
                        onChange={(event) =>
                          setSelectedParentByRoleId((previous) => ({
                            ...previous,
                            [role.id]: event.target.value,
                          }))
                        }
                        value={currentParentSelection}
                      >
                        <option value="">-</option>
                        {roles
                          .filter(
                            (candidateRole) =>
                              candidateRole.id !== role.id && !role.parent_role_ids.includes(candidateRole.id),
                          )
                          .map((candidateRole) => (
                            <option key={candidateRole.id} value={candidateRole.id}>
                              {candidateRole.name}
                            </option>
                          ))}
                      </select>
                    </label>
                    <button
                      className="rounded-full border border-[var(--app-border)] px-3 py-2 text-xs font-semibold disabled:opacity-70"
                      disabled={!currentParentSelection || addParentMutation.isPending}
                      onClick={() => {
                        const parentRoleId = Number(currentParentSelection);
                        addParentMutation.reset();
                        addParentMutation.mutate({ roleId: role.id, parentRoleId });
                        setSelectedParentByRoleId((previous) => ({ ...previous, [role.id]: "" }));
                      }}
                      type="button"
                    >
                      {t("admin.roles.parents.add")}
                    </button>
                  </div>

                  {role.parent_role_ids.length === 0 ? (
                    <p className="mt-3 text-sm text-[var(--app-subtle)]">{t("admin.roles.card.noParents")}</p>
                  ) : (
                    <ul className="mt-3 flex flex-wrap gap-2">
                      {role.parent_role_ids.map((parentRoleId) => (
                        <li className="flex items-center gap-2 rounded-full border border-[var(--app-border)] px-3 py-1" key={parentRoleId}>
                          <span className="text-xs">
                            {roleNameById.get(parentRoleId) ?? String(parentRoleId)}
                          </span>
                          <button
                            className="text-xs font-semibold text-red-700"
                            disabled={removeParentMutation.isPending}
                            onClick={() => {
                              removeParentMutation.reset();
                              removeParentMutation.mutate({ roleId: role.id, parentRoleId });
                            }}
                            type="button"
                          >
                            {t("admin.roles.parents.remove")}
                          </button>
                        </li>
                      ))}
                    </ul>
                  )}
                </article>

                <article className="rounded-xl border border-[var(--app-border)] p-4">
                  <h3 className="text-sm font-semibold">{t("admin.roles.card.permissions")}</h3>
                  {canManageRolePermissions ? (
                    <div className="mt-3 flex flex-wrap items-end gap-2">
                      <label className="min-w-52 flex-1">
                        <span className="mb-1 block text-xs font-medium">{t("admin.roles.permissions.select")}</span>
                        <select
                          className="w-full rounded-xl border border-[var(--app-border)] px-3 py-2 text-sm"
                          onChange={(event) =>
                            setSelectedPermissionByRoleId((previous) => ({
                              ...previous,
                              [role.id]: event.target.value,
                            }))
                          }
                          value={currentPermissionSelection}
                        >
                          <option value="">-</option>
                          {permissions
                            .filter((permission) => !assignedPermissionIds.has(permission.id))
                            .map((permission) => (
                              <option key={permission.id} value={permission.id}>
                                {permission.name}
                              </option>
                            ))}
                        </select>
                      </label>
                      <button
                        className="rounded-full border border-[var(--app-border)] px-3 py-2 text-xs font-semibold disabled:opacity-70"
                        disabled={!currentPermissionSelection || addPermissionMutation.isPending}
                        onClick={() => {
                          addPermissionMutation.reset();
                          addPermissionMutation.mutate({
                            roleId: role.id,
                            permissionId: currentPermissionSelection,
                          });
                          setSelectedPermissionByRoleId((previous) => ({ ...previous, [role.id]: "" }));
                        }}
                        type="button"
                      >
                        {t("admin.roles.permissions.add")}
                      </button>
                    </div>
                  ) : null}

                  {role.permissions.length === 0 ? (
                    <p className="mt-3 text-sm text-[var(--app-subtle)]">{t("admin.roles.card.noPermissions")}</p>
                  ) : (
                    <ul className="mt-3 space-y-2">
                      {role.permissions.map((permission) => (
                        <li
                          className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-[var(--app-border)] px-3 py-2"
                          key={permission.id}
                        >
                          <div className="text-xs">
                            <p className="font-semibold">{permission.name}</p>
                            <p className="text-[var(--app-subtle)]">
                              {permission.id} - {t("admin.roles.permissions.scope.label")}: {permission.scope}
                            </p>
                          </div>
                          <button
                            className="text-xs font-semibold text-red-700 disabled:opacity-70"
                            disabled={removePermissionMutation.isPending}
                            hidden={!canManageRolePermissions}
                            onClick={() => {
                              removePermissionMutation.reset();
                              removePermissionMutation.mutate({
                                roleId: role.id,
                                permissionId: permission.id,
                              });
                            }}
                            type="button"
                          >
                            {t("admin.roles.permissions.remove")}
                          </button>
                        </li>
                      ))}
                    </ul>
                  )}
                </article>
              </div>
            </section>
          );
        })
      )}
    </main>
  );
};
