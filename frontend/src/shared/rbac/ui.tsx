/* eslint-disable react-refresh/only-export-components */
import { appendRequestIdDiagnostic, ApiError, getApiErrorRequestId } from "@/shared/api/errors";
import { t } from "@/shared/i18n/ui-text";

export const ADMIN_PAGE_CLASS_NAME = "mx-auto flex w-full max-w-6xl flex-col gap-6 px-6 py-10";
export const ADMIN_CARD_CLASS_NAME = "rounded-2xl border border-[var(--app-border)] bg-[var(--app-surface)] p-5";
export const ADMIN_FIELD_CLASS_NAME = "w-full rounded-xl border border-[var(--app-border)] px-3 py-2";
export const ADMIN_FORM_GRID_CLASS_NAME = "mt-4 grid gap-4 md:grid-cols-2";
export const ADMIN_LABEL_CLASS_NAME = "mb-2 block text-sm font-medium";
export const ADMIN_INLINE_LABEL_CLASS_NAME = "mb-1 block text-xs font-medium";
export const ADMIN_MUTED_TEXT_CLASS_NAME = "text-sm text-[var(--app-subtle)]";
export const ADMIN_SUBCARD_CLASS_NAME = "rounded-xl border border-[var(--app-border)] p-4";
export const ADMIN_TITLE_CLASS_NAME = "text-3xl font-semibold tracking-tight";
export const ADMIN_PRIMARY_BUTTON_CLASS_NAME =
  "rounded-full bg-[var(--app-ink)] px-5 py-2 text-sm font-semibold text-[var(--app-surface)] disabled:opacity-70";
export const ADMIN_SECONDARY_BUTTON_CLASS_NAME =
  "rounded-full border border-[var(--app-border)] px-4 py-2 text-sm font-semibold disabled:opacity-70";
export const ADMIN_COMPACT_SECONDARY_BUTTON_CLASS_NAME =
  "rounded-full border border-[var(--app-border)] px-3 py-1 text-xs font-semibold disabled:opacity-70";
export const ADMIN_DANGER_BUTTON_CLASS_NAME =
  "rounded-full border border-red-300 px-4 py-2 text-sm font-semibold text-red-700 disabled:opacity-70";
export const ADMIN_COMPACT_DANGER_BUTTON_CLASS_NAME =
  "rounded-full border border-red-300 px-3 py-1 text-xs font-semibold text-red-700 disabled:opacity-70";

export const formatAdminUiError = (error: unknown): string => {
  if (error instanceof ApiError) {
    return appendRequestIdDiagnostic(error.message, getApiErrorRequestId(error));
  }
  return t("admin.common.error.generic");
};

export const AdminErrorPanel = ({ error }: { error: unknown }) => {
  if (!error) {
    return null;
  }

  return (
    <section className="rounded-2xl border border-red-200 bg-red-50 px-4 py-3" role="alert">
      <h2 className="text-sm font-semibold text-red-800">{t("admin.common.error.title")}</h2>
      <p className="mt-1 text-sm text-red-700">{formatAdminUiError(error)}</p>
    </section>
  );
};
