import { useSession } from "@/shared/auth/session";
import { t } from "@/shared/i18n/ui-text";
import { CenteredMessage } from "@/shared/ui/CenteredMessage";

export const WelcomePage = () => {
  const { data: user } = useSession();

  if (!user) {
    return <CenteredMessage title={t("welcome.noSession.title")} body={t("welcome.noSession.body")} />;
  }

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
      </section>
    </main>
  );
};
