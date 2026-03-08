import { t } from "@/shared/i18n/ui-text";
import { CenteredMessage } from "@/shared/ui/CenteredMessage";

export const NotFoundPage = () => (
  <CenteredMessage title={t("routing.notFound.title")} body={t("routing.notFound.body")} />
);
