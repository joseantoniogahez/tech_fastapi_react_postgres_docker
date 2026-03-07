import { Link, Navigate } from "react-router-dom";

import { useSession } from "@/shared/auth/session";
import { t } from "@/shared/i18n/ui-text";
import { CenteredMessage } from "@/shared/ui/CenteredMessage";

export const LandingPage = () => {
  const { data: user, isPending } = useSession();

  if (isPending) {
    return <CenteredMessage title={t("landing.loading.title")} />;
  }

  if (user) {
    return <Navigate replace to="/welcome" />;
  }

  return (
    <main className="flex min-h-screen items-center justify-center px-6 py-12">
      <section className="w-full max-w-4xl rounded-[var(--radius-card)] border border-[var(--app-border)] bg-[var(--app-surface)] p-8 shadow-[0_16px_40px_rgba(23,33,43,0.08)] sm:p-10">
        <p className="mono-label fade-rise text-[var(--app-subtle)]">{t("landing.badge.portal")}</p>
        <h1 className="fade-rise-delay mt-4 max-w-2xl text-4xl font-semibold tracking-tight sm:text-6xl">
          {t("landing.title")}
        </h1>
        <p className="fade-rise-delay-2 mt-6 max-w-xl text-base text-[var(--app-subtle)] sm:text-lg">
          {t("landing.subtitle")}
        </p>
        <div className="fade-rise-delay-2 mt-10">
          <Link
            className="inline-flex items-center justify-center rounded-full bg-[var(--app-ink)] px-6 py-3 text-sm font-semibold text-[var(--app-surface)] transition hover:bg-[var(--app-accent)] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--app-accent)]"
            to="/login"
          >
            {t("landing.cta.login")}
          </Link>
        </div>
      </section>
    </main>
  );
};
