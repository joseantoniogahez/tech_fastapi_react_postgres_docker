import { useEffect } from "react";
import { isRouteErrorResponse, useRouteError } from "react-router-dom";

import { appendRequestIdDiagnostic, getApiErrorRequestId } from "@/shared/api/errors";
import { t } from "@/shared/i18n/ui-text";
import { emitObservabilityEvent } from "@/shared/observability/events";
import { CenteredMessage } from "@/shared/ui/CenteredMessage";

export const RouteErrorBoundary = () => {
  const routeError = useRouteError();

  const requestId = getApiErrorRequestId(routeError);
  const baseBody = isRouteErrorResponse(routeError)
    ? `${t("routing.error.body")} (status=${routeError.status})`
    : t("routing.error.body");

  useEffect(() => {
    emitObservabilityEvent({
      event_name: "routing.route_error",
      level: "error",
      request_id: requestId,
      context: {
        is_route_error_response: isRouteErrorResponse(routeError),
      },
    });
  }, [requestId, routeError]);

  return (
    <CenteredMessage
      title={t("routing.error.title")}
      body={appendRequestIdDiagnostic(baseBody, requestId)}
    />
  );
};
