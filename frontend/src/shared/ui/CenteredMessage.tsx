import { t } from "@/shared/i18n/ui-text";

interface CenteredMessageProps {
  title: string;
  body?: string;
}

export const CenteredMessage = ({ title, body }: CenteredMessageProps) => (
  <main className="flex min-h-screen items-center justify-center px-6 py-12">
    <section className="fade-rise w-full max-w-xl rounded-[var(--radius-card)] border border-[var(--app-border)] bg-[var(--app-surface)] p-8 sm:p-10">
      <p className="mono-label text-[var(--app-subtle)]">{t("shared.centeredMessage.stateLabel")}</p>
      <h1 className="mt-4 text-3xl font-semibold tracking-tight sm:text-4xl">{title}</h1>
      {body ? <p className="mt-4 text-base text-[var(--app-subtle)]">{body}</p> : null}
    </section>
  </main>
);
