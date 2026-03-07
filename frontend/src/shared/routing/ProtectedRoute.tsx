import { Navigate, Outlet } from "react-router-dom";

import { useSession } from "@/shared/auth/session";
import { t } from "@/shared/i18n/ui-text";
import { CenteredMessage } from "@/shared/ui/CenteredMessage";

export const ProtectedRoute = () => {
  const { data: user, isPending, isError } = useSession();

  if (isPending) {
    return (
      <CenteredMessage
        title={t("routing.protected.validating.title")}
        body={t("routing.protected.validating.body")}
      />
    );
  }

  if (isError) {
    return (
      <CenteredMessage
        title={t("routing.protected.error.title")}
        body={t("routing.protected.error.body")}
      />
    );
  }

  if (!user) {
    return <Navigate replace to="/login" />;
  }

  return <Outlet />;
};
