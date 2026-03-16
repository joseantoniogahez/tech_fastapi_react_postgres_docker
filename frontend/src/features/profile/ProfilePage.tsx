import { FormEvent, useEffect, useRef, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";

import {
  ApiError,
  appendRequestIdDiagnostic,
  getApiErrorRequestId,
  isUnauthorizedError,
} from "@/shared/api/errors";
import { SESSION_QUERY_KEY, updateCurrentUser, useSession } from "@/shared/auth/session";
import {
  getPasswordPolicyViolationKeys,
  isNormalizedUsernameValid,
  normalizeUsername,
} from "@/shared/auth/validation";
import { t } from "@/shared/i18n/ui-text";
import { CenteredMessage } from "@/shared/ui/CenteredMessage";

interface ProfileFormState {
  username: string;
  currentPassword: string;
  newPassword: string;
}

const buildInitialProfileState = (username: string): ProfileFormState => ({
  username,
  currentPassword: "",
  newPassword: "",
});

const getProfileValidationMessage = (formState: ProfileFormState, currentUsername: string): string | null => {
  const normalizedUsername = normalizeUsername(formState.username);
  const normalizedCurrentUsername = normalizeUsername(currentUsername);

  if (!normalizedUsername.length) {
    return t("auth.validation.username.required");
  }
  if (!isNormalizedUsernameValid(formState.username)) {
    return t("auth.validation.username.format");
  }
  if (formState.newPassword && !formState.currentPassword) {
    return t("profile.validation.currentPassword.required");
  }
  if (formState.currentPassword && !formState.newPassword) {
    return t("profile.validation.newPassword.required");
  }
  if (formState.newPassword && formState.currentPassword === formState.newPassword) {
    return t("profile.validation.newPassword.different");
  }

  const [firstPasswordViolation] = getPasswordPolicyViolationKeys(formState.newPassword, normalizedUsername);
  if (formState.newPassword && firstPasswordViolation) {
    return t(firstPasswordViolation);
  }

  const usernameChanged = normalizedUsername !== normalizedCurrentUsername;
  const passwordChanged = formState.newPassword.length > 0;
  if (!usernameChanged && !passwordChanged) {
    return t("profile.validation.noChanges");
  }

  return null;
};

export const ProfilePage = () => {
  const { data: user } = useSession();
  const queryClient = useQueryClient();
  const [formState, setFormState] = useState<ProfileFormState>(() => buildInitialProfileState(user?.username ?? ""));
  const [clientError, setClientError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const lastSyncedUserId = useRef<number | null>(null);

  useEffect(() => {
    if (!user) {
      return;
    }

    if (lastSyncedUserId.current === user.id) {
      return;
    }

    lastSyncedUserId.current = user.id;
    setFormState(buildInitialProfileState(user.username));
  }, [user]);

  const updateMutation = useMutation({
    retry: false,
    mutationFn: updateCurrentUser,
    onSuccess: (updatedUser) => {
      queryClient.setQueryData(SESSION_QUERY_KEY, updatedUser);
      setClientError(null);
      setSuccessMessage(t("profile.success.body", { username: updatedUser.username }));
      setFormState(buildInitialProfileState(updatedUser.username));
    },
    onError: (error) => {
      if (isUnauthorizedError(error)) {
        queryClient.setQueryData(SESSION_QUERY_KEY, null);
      }
    },
  });

  if (!user) {
    return <CenteredMessage title={t("welcome.noSession.title")} body={t("welcome.noSession.body")} />;
  }

  const submit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    updateMutation.reset();

    const validationMessage = getProfileValidationMessage(formState, user.username);
    if (validationMessage) {
      setClientError(validationMessage);
      setSuccessMessage(null);
      return;
    }

    const normalizedUsername = normalizeUsername(formState.username);
    const payload: {
      username?: string;
      current_password?: string;
      new_password?: string;
    } = {};

    if (normalizedUsername !== normalizeUsername(user.username)) {
      payload.username = formState.username.trim();
    }
    if (formState.currentPassword) {
      payload.current_password = formState.currentPassword;
    }
    if (formState.newPassword) {
      payload.new_password = formState.newPassword;
    }

    setClientError(null);
    setSuccessMessage(null);
    updateMutation.mutate(payload);
  };

  const mutationError =
    clientError ??
    (updateMutation.error instanceof ApiError
      ? appendRequestIdDiagnostic(updateMutation.error.message, getApiErrorRequestId(updateMutation.error))
      : updateMutation.isError
        ? t("profile.error.generic")
        : null);

  return (
    <main className="flex min-h-screen items-center justify-center px-6 py-12">
      <section className="w-full max-w-2xl rounded-[var(--radius-card)] border border-[var(--app-border)] bg-[var(--app-surface)] p-8 shadow-[0_16px_40px_rgba(23,33,43,0.08)] sm:p-10">
        <p className="mono-label fade-rise text-[var(--app-subtle)]">{t("profile.badge")}</p>
        <h1 className="fade-rise-delay mt-4 text-3xl font-semibold tracking-tight sm:text-4xl">
          {t("profile.title")}
        </h1>
        <p className="fade-rise-delay-2 mt-4 text-sm text-[var(--app-subtle)]">{t("profile.subtitle")}</p>
        <p className="mt-2 text-sm font-medium text-[var(--app-ink)]">{t("profile.currentUser", { username: user.username })}</p>

        <form className="mt-8 space-y-4" onSubmit={submit}>
          <label className="block">
            <span className="mb-2 block text-sm font-medium text-[var(--app-ink)]">
              {t("profile.fields.username")}
            </span>
            <input
              autoComplete="username"
              className="w-full rounded-2xl border border-[var(--app-border)] bg-white px-4 py-3 text-base outline-none transition focus:border-[var(--app-accent)]"
              name="username"
              onChange={(event) =>
                setFormState((previous) => ({ ...previous, username: event.target.value }))
              }
              required
              value={formState.username}
            />
          </label>

          <label className="block">
            <span className="mb-2 block text-sm font-medium text-[var(--app-ink)]">
              {t("profile.fields.currentPassword")}
            </span>
            <input
              autoComplete="current-password"
              className="w-full rounded-2xl border border-[var(--app-border)] bg-white px-4 py-3 text-base outline-none transition focus:border-[var(--app-accent)]"
              name="currentPassword"
              onChange={(event) =>
                setFormState((previous) => ({ ...previous, currentPassword: event.target.value }))
              }
              type="password"
              value={formState.currentPassword}
            />
          </label>

          <label className="block">
            <span className="mb-2 block text-sm font-medium text-[var(--app-ink)]">
              {t("profile.fields.newPassword")}
            </span>
            <input
              autoComplete="new-password"
              className="w-full rounded-2xl border border-[var(--app-border)] bg-white px-4 py-3 text-base outline-none transition focus:border-[var(--app-accent)]"
              minLength={8}
              name="newPassword"
              onChange={(event) =>
                setFormState((previous) => ({ ...previous, newPassword: event.target.value }))
              }
              type="password"
              value={formState.newPassword}
            />
          </label>

          <ul className="space-y-1 rounded-2xl border border-[var(--app-border)] bg-[var(--app-bg)] px-4 py-3 text-sm text-[var(--app-subtle)]">
            <li>{t("auth.shared.username.hint")}</li>
            <li>{t("auth.shared.password.hint")}</li>
            <li>{t("profile.password.optional")}</li>
          </ul>

          {successMessage ? (
            <p
              className="rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800"
              role="status"
            >
              {successMessage}
            </p>
          ) : null}

          {mutationError ? (
            <p
              className="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700"
              role="alert"
            >
              {mutationError}
            </p>
          ) : null}

          <div className="flex flex-col gap-3 sm:flex-row">
            <button
              className="inline-flex flex-1 items-center justify-center rounded-full bg-[var(--app-ink)] px-5 py-3 text-sm font-semibold text-[var(--app-surface)] transition hover:bg-[var(--app-accent)] disabled:cursor-not-allowed disabled:opacity-70"
              disabled={updateMutation.isPending}
              type="submit"
            >
              {updateMutation.isPending ? t("profile.submit.pending") : t("profile.submit.default")}
            </button>
            <Link
              className="inline-flex flex-1 items-center justify-center rounded-full border border-[var(--app-border)] px-5 py-3 text-sm font-semibold text-[var(--app-ink)] transition hover:border-[var(--app-accent)] hover:text-[var(--app-accent)]"
              to="/welcome"
            >
              {t("profile.actions.cancel")}
            </Link>
          </div>
        </form>
      </section>
    </main>
  );
};
