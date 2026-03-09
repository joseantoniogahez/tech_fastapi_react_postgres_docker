import { useEffect, useMemo, useState } from "react";
import { Link, Outlet, useLocation } from "react-router-dom";

import { useSession } from "@/shared/auth/session";
import { IAM_PERMISSION } from "@/shared/iam/contracts";
import { userHasPermission } from "@/shared/iam/api";
import { t } from "@/shared/i18n/ui-text";

interface AdminMenuItem {
  key: "routing.nav.admin.users" | "routing.nav.admin.roles";
  permissionId: string;
  to: "/admin/users" | "/admin/roles";
}

const ADMIN_MENU_ITEMS: readonly AdminMenuItem[] = [
  {
    key: "routing.nav.admin.users",
    permissionId: IAM_PERMISSION.USERS_MANAGE,
    to: "/admin/users",
  },
  {
    key: "routing.nav.admin.roles",
    permissionId: IAM_PERMISSION.ROLES_MANAGE,
    to: "/admin/roles",
  },
];

export const RootLayout = () => {
  const { data: user } = useSession();
  const location = useLocation();
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  useEffect(() => {
    setIsMenuOpen(false);
  }, [location.pathname]);

  const visibleAdminItems = useMemo(() => {
    if (!user) {
      return [];
    }
    return ADMIN_MENU_ITEMS.filter((menuItem) => userHasPermission(user, menuItem.permissionId));
  }, [user]);

  if (!user) {
    return <Outlet />;
  }

  return (
    <div className="min-h-screen">
      <header className="sticky top-0 z-20 border-b border-[var(--app-border)] bg-[var(--app-surface)]">
        <div className="mx-auto flex w-full max-w-6xl items-center justify-between px-4 py-3">
          <button
            aria-controls="app-navigation-panel"
            aria-expanded={isMenuOpen}
            aria-label={t("routing.nav.menu.toggle")}
            className="inline-flex h-10 w-10 items-center justify-center rounded-full border border-[var(--app-border)]"
            onClick={() => setIsMenuOpen((previous) => !previous)}
            type="button"
          >
            <span aria-hidden className="text-lg">
              &#8801;
            </span>
          </button>
          <Link className="text-sm font-semibold" to="/welcome">
            {t("routing.nav.home")}
          </Link>
        </div>
      </header>

      <div className="mx-auto flex w-full max-w-6xl">
        <nav
          className="w-64 shrink-0 border-r border-[var(--app-border)] bg-[var(--app-surface)] p-4"
          hidden={!isMenuOpen}
          id="app-navigation-panel"
        >
          <ul className="space-y-2">
            <li>
              <Link className="block rounded-xl px-3 py-2 text-sm font-medium hover:bg-[var(--app-bg)]" to="/welcome">
                {t("routing.nav.home")}
              </Link>
            </li>
            {visibleAdminItems.length > 0 ? (
              <li>
                <p className="px-3 pt-2 text-xs font-semibold uppercase tracking-wide text-[var(--app-subtle)]">
                  {t("routing.nav.admin.group")}
                </p>
                <ul className="mt-1 space-y-1">
                  {visibleAdminItems.map((menuItem) => (
                    <li key={menuItem.to}>
                      <Link
                        className="block rounded-xl px-3 py-2 text-sm font-medium hover:bg-[var(--app-bg)]"
                        to={menuItem.to}
                      >
                        {t(menuItem.key)}
                      </Link>
                    </li>
                  ))}
                </ul>
              </li>
            ) : null}
          </ul>
        </nav>

        <div className="min-w-0 flex-1">
          <Outlet />
        </div>
      </div>
    </div>
  );
};
