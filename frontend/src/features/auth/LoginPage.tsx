import { FormEvent, startTransition, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Link, Navigate, useNavigate } from "react-router-dom";

import { authLoginMutationPolicy } from "@/app/mutation-policy";
import { ApiError, appendRequestIdDiagnostic, getApiErrorRequestId } from "@/shared/api/errors";
import { SESSION_QUERY_KEY, loginWithCredentials, readCurrentUser, useSession } from "@/shared/auth/session";
import { t } from "@/shared/i18n/ui-text";
import { CenteredMessage } from "@/shared/ui/CenteredMessage";

interface LoginFormState {
  username: string;
  password: string;
}

const INITIAL_FORM_STATE: LoginFormState = {
  username: "",
  password: "",
};

export const LoginPage = () => {
  const [formState, setFormState] = useState<LoginFormState>(INITIAL_FORM_STATE);
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const session = useSession();

  const loginMutation = useMutation({
    ...authLoginMutationPolicy,
    mutationFn: async ({ username, password }: LoginFormState) => {
      await loginWithCredentials({ username, password });
      return await readCurrentUser();
    },
    onSuccess: async (user) => {
      queryClient.setQueryData(SESSION_QUERY_KEY, user);
      await queryClient.invalidateQueries({ queryKey: SESSION_QUERY_KEY });
      startTransition(() => {
        void navigate("/welcome", { replace: true });
      });
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
    loginMutation.reset();
    loginMutation.mutate(formState);
  };

  const mutationError =
    loginMutation.error instanceof ApiError
      ? appendRequestIdDiagnostic(loginMutation.error.message, getApiErrorRequestId(loginMutation.error))
      : t("auth.login.error.generic");

  return (
    <main className="flex min-h-screen items-center justify-center px-6 py-12">
      <section className="w-full max-w-md rounded-[var(--radius-card)] border border-[var(--app-border)] bg-[var(--app-surface)] p-8 shadow-[0_16px_40px_rgba(23,33,43,0.08)] sm:p-10">
        <p className="mono-label fade-rise text-[var(--app-subtle)]">{t("auth.login.badge")}</p>
        <h1 className="fade-rise-delay mt-4 text-3xl font-semibold tracking-tight sm:text-4xl">
          {t("auth.login.title")}
        </h1>
        <p className="fade-rise-delay-2 mt-4 text-sm text-[var(--app-subtle)]">
          {t("auth.login.subtitle")}
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
              autoComplete="current-password"
              className="w-full rounded-2xl border border-[var(--app-border)] bg-white px-4 py-3 text-base outline-none transition focus:border-[var(--app-accent)]"
              name="password"
              onChange={(event) =>
                setFormState((previous) => ({ ...previous, password: event.target.value }))
              }
              required
              type="password"
              value={formState.password}
            />
          </label>

          {loginMutation.isError ? (
            <p
              className="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700"
              role="alert"
            >
              {mutationError}
            </p>
          ) : null}

          <button
            className="w-full rounded-full bg-[var(--app-ink)] px-5 py-3 text-sm font-semibold text-[var(--app-surface)] transition hover:bg-[var(--app-accent)] disabled:cursor-not-allowed disabled:opacity-70"
            disabled={loginMutation.isPending}
            type="submit"
          >
            {loginMutation.isPending ? t("auth.login.submit.pending") : t("auth.login.submit.default")}
          </button>
        </form>

        <p className="mt-6 text-sm text-[var(--app-subtle)]">
          {t("auth.login.footer.firstTime")}{" "}
          <Link className="font-semibold text-[var(--app-ink)] underline underline-offset-4" to="/register">
            {t("auth.login.footer.createAccount")}
          </Link>
          .
        </p>
      </section>
    </main>
  );
};
