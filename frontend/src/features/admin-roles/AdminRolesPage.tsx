import { FormEvent, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { t } from "@/shared/i18n/ui-text";
import {
  assignRbacRoleInheritance,
  createRbacRole,
  deleteRbacRole,
  readRbacRoles,
  removeRbacRoleInheritance,
  updateRbacRole,
} from "@/shared/rbac/admin";
import {
  ADMIN_CARD_CLASS_NAME,
  ADMIN_COMPACT_SECONDARY_BUTTON_CLASS_NAME,
  ADMIN_DANGER_BUTTON_CLASS_NAME,
  ADMIN_FIELD_CLASS_NAME,
  ADMIN_INLINE_LABEL_CLASS_NAME,
  ADMIN_LABEL_CLASS_NAME,
  ADMIN_MUTED_TEXT_CLASS_NAME,
  ADMIN_PAGE_CLASS_NAME,
  ADMIN_PRIMARY_BUTTON_CLASS_NAME,
  ADMIN_SECONDARY_BUTTON_CLASS_NAME,
  ADMIN_SUBCARD_CLASS_NAME,
  ADMIN_TITLE_CLASS_NAME,
  AdminErrorPanel,
} from "@/shared/rbac/ui";
import { CenteredMessage } from "@/shared/ui/CenteredMessage";

const RBAC_ROLES_QUERY_KEY = ["rbac", "roles"] as const;

export const AdminRolesPage = () => {
  const queryClient = useQueryClient();

  const [createRoleName, setCreateRoleName] = useState("");
  const [roleNameDraftById, setRoleNameDraftById] = useState<Record<number, string>>({});
  const [selectedParentByRoleId, setSelectedParentByRoleId] = useState<Record<number, string>>({});

  const rolesQuery = useQuery({
    queryKey: RBAC_ROLES_QUERY_KEY,
    queryFn: readRbacRoles,
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

  const roles = rolesQuery.data ?? [];

  const roleNameById = useMemo(
    () => new Map((rolesQuery.data ?? []).map((role) => [role.id, role.name])),
    [rolesQuery.data],
  );

  const pageError =
    rolesQuery.error ??
    createRoleMutation.error ??
    updateRoleMutation.error ??
    deleteRoleMutation.error ??
    addParentMutation.error ??
    removeParentMutation.error;

  if (rolesQuery.isPending) {
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
    <main className={ADMIN_PAGE_CLASS_NAME}>
      <header>
        <h1 className={ADMIN_TITLE_CLASS_NAME}>{t("admin.roles.title")}</h1>
        <p className={`mt-2 ${ADMIN_MUTED_TEXT_CLASS_NAME}`}>{t("admin.roles.subtitle")}</p>
      </header>

      <AdminErrorPanel error={pageError} />

      <section className={ADMIN_CARD_CLASS_NAME}>
        <h2 className="text-lg font-semibold">{t("admin.roles.create.title")}</h2>
        <form className="mt-4 flex flex-wrap items-end gap-3" onSubmit={submitCreateRole}>
          <label className="min-w-72 flex-1">
            <span className={ADMIN_LABEL_CLASS_NAME}>{t("admin.roles.create.name")}</span>
            <input
              className={ADMIN_FIELD_CLASS_NAME}
              onChange={(event) => setCreateRoleName(event.target.value)}
              required
              value={createRoleName}
            />
          </label>
          <button
            className={ADMIN_PRIMARY_BUTTON_CLASS_NAME}
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
        <section className={ADMIN_CARD_CLASS_NAME}>
          <p className={ADMIN_MUTED_TEXT_CLASS_NAME}>{t("admin.roles.list.empty")}</p>
        </section>
      ) : (
        roles.map((role) => {
          const currentRoleNameDraft = roleNameDraftById[role.id] ?? role.name;
          const currentParentSelection = selectedParentByRoleId[role.id] ?? "";

          return (
            <section
              className={ADMIN_CARD_CLASS_NAME}
              key={role.id}
            >
              <div className="flex flex-wrap items-end gap-3">
                <label className="min-w-72 flex-1">
                  <span className={ADMIN_LABEL_CLASS_NAME}>{t("admin.roles.create.name")}</span>
                  <input
                    className={ADMIN_FIELD_CLASS_NAME}
                    onChange={(event) =>
                      setRoleNameDraftById((previous) => ({ ...previous, [role.id]: event.target.value }))
                    }
                    value={currentRoleNameDraft}
                  />
                </label>
                <button
                  className={ADMIN_SECONDARY_BUTTON_CLASS_NAME}
                  disabled={updateRoleMutation.isPending}
                  onClick={() => saveRoleName(role.id, role.name)}
                  type="button"
                >
                  {updateRoleMutation.isPending
                    ? t("admin.roles.actions.update.pending")
                    : t("admin.roles.actions.update")}
                </button>
                <button
                  className={ADMIN_DANGER_BUTTON_CLASS_NAME}
                  disabled={deleteRoleMutation.isPending}
                  onClick={() => confirmAndDeleteRole(role.id, role.name)}
                  type="button"
                >
                  {t("admin.roles.actions.delete")}
                </button>
              </div>

              <div className="mt-5">
                <article className={ADMIN_SUBCARD_CLASS_NAME}>
                  <h3 className="text-sm font-semibold">{t("admin.roles.card.parents")}</h3>
                  <div className="mt-3 flex flex-wrap items-end gap-2">
                    <label className="min-w-52 flex-1">
                      <span className={ADMIN_INLINE_LABEL_CLASS_NAME}>{t("admin.roles.parents.select")}</span>
                      <select
                        className={`${ADMIN_FIELD_CLASS_NAME} text-sm`}
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
                      className={ADMIN_COMPACT_SECONDARY_BUTTON_CLASS_NAME}
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
                    <p className={`mt-3 ${ADMIN_MUTED_TEXT_CLASS_NAME}`}>{t("admin.roles.card.noParents")}</p>
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
              </div>
            </section>
          );
        })
      )}
    </main>
  );
};
