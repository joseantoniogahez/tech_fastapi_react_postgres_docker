import { FormEvent, useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { Link, Navigate } from "react-router-dom";

import { ApiError, appendRequestIdDiagnostic, getApiErrorRequestId } from "@/shared/api/errors";
import { type AuthenticatedUser, registerUser, useSession } from "@/shared/auth/session";
import {
  getPasswordPolicyViolationKeys,
  isNormalizedUsernameValid,
  normalizeUsername,
} from "@/shared/auth/validation";
import { t } from "@/shared/i18n/ui-text";
import { CenteredMessage } from "@/shared/ui/CenteredMessage";

interface RegisterFormState {
  username: string;
  password: string;
}

const INITIAL_FORM_STATE: RegisterFormState = {
  username: "",
  password: "",
};

const getRegisterValidationMessage = (formState: RegisterFormState): string | null => {
  const normalizedUsername = normalizeUsername(formState.username);

  if (!normalizedUsername.length) {
    return t("auth.validation.username.required");
  }
  if (!isNormalizedUsernameValid(formState.username)) {
    return t("auth.validation.username.format");
  }

  const [firstPasswordViolation] = getPasswordPolicyViolationKeys(formState.password, normalizedUsername);
  return firstPasswordViolation ? t(firstPasswordViolation) : null;
};

export const RegisterPage = () => {
  const [formState, setFormState] = useState<RegisterFormState>(INITIAL_FORM_STATE);
  const [clientError, setClientError] = useState<string | null>(null);
  const [registeredUser, setRegisteredUser] = useState<AuthenticatedUser | null>(null);
  const session = useSession();

  const registerMutation = useMutation({
    retry: false,
    mutationFn: registerUser,
    onSuccess: (user) => {
      setRegisteredUser(user);
      setClientError(null);
      setFormState(INITIAL_FORM_STATE);
    },
  });

  if (session.isPending) {
    return <CenteredMessage title={t("auth.login.validating.title")} />;
  }

  if (session.data) {
    return <Navigate replace to="/welcome" />;
  }

  const submit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    registerMutation.reset();
    setRegisteredUser(null);

    const validationMessage = getRegisterValidationMessage(formState);
    if (validationMessage) {
      setClientError(validationMessage);
      return;
    }

    setClientError(null);
    registerMutation.mutate({
      username: formState.username.trim(),
      password: formState.password,
    });
  };

  const mutationError =
    clientError ??
    (registerMutation.error instanceof ApiError
      ? appendRequestIdDiagnostic(registerMutation.error.message, getApiErrorRequestId(registerMutation.error))
      : registerMutation.isError
        ? t("auth.register.error.generic")
        : null);

  if (registeredUser) {
    return (
      <main className="flex min-h-screen items-center justify-center px-6 py-12">
        <section className="w-full max-w-md rounded-[var(--radius-card)] border border-[var(--app-border)] bg-[var(--app-surface)] p-8 shadow-[0_16px_40px_rgba(23,33,43,0.08)] sm:p-10">
          <p className="mono-label fade-rise text-[var(--app-subtle)]">{t("auth.register.badge")}</p>
          <h1 className="fade-rise-delay mt-4 text-3xl font-semibold tracking-tight sm:text-4xl">
            {t("auth.register.success.title")}
          </h1>
          <p className="fade-rise-delay-2 mt-4 text-sm text-[var(--app-subtle)]">
            {t("auth.register.success.body", { username: registeredUser.username })}
          </p>
          <div className="mt-8">
            <Link
              className="inline-flex w-full items-center justify-center rounded-full bg-[var(--app-ink)] px-5 py-3 text-sm font-semibold text-[var(--app-surface)] transition hover:bg-[var(--app-accent)]"
              to="/login"
            >
              {t("auth.register.footer.signIn")}
            </Link>
          </div>
        </section>
      </main>
    );
  }

  return (
    <main className="flex min-h-screen items-center justify-center px-6 py-12">
      <section className="w-full max-w-md rounded-[var(--radius-card)] border border-[var(--app-border)] bg-[var(--app-surface)] p-8 shadow-[0_16px_40px_rgba(23,33,43,0.08)] sm:p-10">
        <p className="mono-label fade-rise text-[var(--app-subtle)]">{t("auth.register.badge")}</p>
        <h1 className="fade-rise-delay mt-4 text-3xl font-semibold tracking-tight sm:text-4xl">
          {t("auth.register.title")}
        </h1>
        <p className="fade-rise-delay-2 mt-4 text-sm text-[var(--app-subtle)]">
          {t("auth.register.subtitle")}
        </p>

        <form className="mt-8 space-y-4" onSubmit={submit}>
          <label className="block">
            <span className="mb-2 block text-sm font-medium text-[var(--app-ink)]">
              {t("auth.login.fields.username")}
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
              {t("auth.login.fields.password")}
            </span>
            <input
              autoComplete="new-password"
              className="w-full rounded-2xl border border-[var(--app-border)] bg-white px-4 py-3 text-base outline-none transition focus:border-[var(--app-accent)]"
              minLength={8}
              name="password"
              onChange={(event) =>
                setFormState((previous) => ({ ...previous, password: event.target.value }))
              }
              required
              type="password"
              value={formState.password}
            />
          </label>

          <ul className="space-y-1 rounded-2xl border border-[var(--app-border)] bg-[var(--app-bg)] px-4 py-3 text-sm text-[var(--app-subtle)]">
            <li>{t("auth.shared.username.hint")}</li>
            <li>{t("auth.shared.password.hint")}</li>
          </ul>

          {mutationError ? (
            <p
              className="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700"
              role="alert"
            >
              {mutationError}
            </p>
          ) : null}

          <button
            className="w-full rounded-full bg-[var(--app-ink)] px-5 py-3 text-sm font-semibold text-[var(--app-surface)] transition hover:bg-[var(--app-accent)] disabled:cursor-not-allowed disabled:opacity-70"
            disabled={registerMutation.isPending}
            type="submit"
          >
            {registerMutation.isPending ? t("auth.register.submit.pending") : t("auth.register.submit.default")}
          </button>
        </form>

        <p className="mt-6 text-sm text-[var(--app-subtle)]">
          {t("auth.register.footer.haveAccount")}{" "}
          <Link className="font-semibold text-[var(--app-ink)] underline underline-offset-4" to="/login">
            {t("auth.register.footer.signIn")}
          </Link>
          .
        </p>
      </section>
    </main>
  );
};
