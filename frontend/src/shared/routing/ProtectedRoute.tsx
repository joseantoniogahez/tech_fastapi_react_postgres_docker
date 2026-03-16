import { useEffect } from "react";
import { Navigate, Outlet, useLocation } from "react-router-dom";

import { appendRequestIdDiagnostic, getApiErrorRequestId } from "@/shared/api/errors";
import { useSession } from "@/shared/auth/session";
import { t } from "@/shared/i18n/ui-text";
import { emitObservabilityEvent } from "@/shared/observability/events";
import { CenteredMessage } from "@/shared/ui/CenteredMessage";

export const ProtectedRoute = () => {
  const { data: user, isPending, isError, error } = useSession();
  const location = useLocation();

  useEffect(() => {
    if (!isError) {
      return;
    }

    emitObservabilityEvent({
      event_name: "routing.protected.error",
      level: "error",
      request_id: getApiErrorRequestId(error),
      context: {
        route: location.pathname,
      },
    });
  }, [error, isError, location.pathname]);

  if (isPending) {
    return (
      <CenteredMessage
        title={t("routing.protected.validating.title")}
        body={t("routing.protected.validating.body")}
      />
    );
  }

  if (isError) {
    const requestId = getApiErrorRequestId(error);
    return (
      <CenteredMessage
        title={t("routing.protected.error.title")}
        body={appendRequestIdDiagnostic(t("routing.protected.error.body"), requestId)}
      />
    );
  }

  if (!user) {
    return <Navigate replace to="/login" />;
  }

  return <Outlet />;
};
