import { useEffect } from "react";
import { Navigate, Outlet, useLocation } from "react-router-dom";

import { useSession } from "@/shared/auth/session";
import { userHasPermission } from "@/shared/iam/api";
import { emitObservabilityEvent } from "@/shared/observability/events";

interface PermissionRouteProps {
  requiredPermission: string;
  fallbackTo?: string;
}

export const PermissionRoute = ({ requiredPermission, fallbackTo = "/welcome" }: PermissionRouteProps) => {
  const { data: user } = useSession();
  const location = useLocation();
  const hasRequiredPermission = userHasPermission(user, requiredPermission);

  useEffect(() => {
    if (!user || hasRequiredPermission) {
      return;
    }

    emitObservabilityEvent({
      event_name: "routing.route_error",
      level: "warn",
      context: {
        route: location.pathname,
        reason: "missing_permission",
        required_permission: requiredPermission,
        redirect_to: fallbackTo,
      },
    });
  }, [fallbackTo, hasRequiredPermission, location.pathname, requiredPermission, user]);

  if (!user) {
    return <Navigate replace to="/login" />;
  }

  if (!hasRequiredPermission) {
    return <Navigate replace to={fallbackTo} />;
  }

  return <Outlet />;
};
