import { startTransition } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";

import { authLogoutMutationPolicy } from "@/app/mutation-policy";
import { SESSION_QUERY_KEY, logout, useSession } from "@/shared/auth/session";
import { t } from "@/shared/i18n/ui-text";
import { CenteredMessage } from "@/shared/ui/CenteredMessage";

export const WelcomePage = () => {
  const { data: user } = useSession();
  const queryClient = useQueryClient();
  const navigate = useNavigate();

  const logoutMutation = useMutation({
    ...authLogoutMutationPolicy,
    mutationFn: () => {
      logout();
    },
    onSuccess: async () => {
      queryClient.setQueryData(SESSION_QUERY_KEY, null);
      await queryClient.invalidateQueries({ queryKey: SESSION_QUERY_KEY });
      startTransition(() => {
        void navigate("/login", { replace: true });
      });
    },
  });

  if (!user) {
    return <CenteredMessage title={t("welcome.noSession.title")} body={t("welcome.noSession.body")} />;
  }

  const closeSession = () => {
    logoutMutation.mutate();
  };

  return (
    <main className="flex min-h-screen items-center justify-center px-6 py-12">
      <section className="w-full max-w-3xl rounded-[var(--radius-card)] border border-[var(--app-border)] bg-[var(--app-surface)] p-8 shadow-[0_16px_40px_rgba(23,33,43,0.08)] sm:p-12">
        <p className="mono-label fade-rise text-[var(--app-subtle)]">{t("welcome.badge")}</p>
        <h1 className="fade-rise-delay mt-4 text-4xl font-semibold tracking-tight sm:text-6xl">
          {t("welcome.greeting", { username: user.username })}
        </h1>
        <p className="fade-rise-delay-2 mt-6 max-w-xl text-base text-[var(--app-subtle)] sm:text-lg">
          {t("welcome.sessionActive.body")}
        </p>
        <div className="fade-rise-delay-2 mt-10">
          <button
            className="rounded-full border border-[var(--app-border)] bg-transparent px-5 py-3 text-sm font-semibold text-[var(--app-ink)] transition hover:border-[var(--app-accent)] hover:text-[var(--app-accent)]"
            disabled={logoutMutation.isPending}
            onClick={closeSession}
            type="button"
          >
            {logoutMutation.isPending ? t("welcome.logout.pending") : t("welcome.logout")}
          </button>
        </div>
      </section>
    </main>
  );
};
