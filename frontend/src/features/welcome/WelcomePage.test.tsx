import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import type { Mock } from "vitest";

import { WelcomePage } from "@/features/welcome/WelcomePage";
import { t } from "@/shared/i18n/ui-text";

interface SessionUser {
  id: number;
  username: string;
  disabled: boolean;
}

interface SessionState {
  data: SessionUser | null;
}

const useSessionMock: Mock<() => SessionState> = vi.fn();
const logoutMock: Mock<() => void> = vi.fn();
const navigateMock: Mock<(to: string, options: { replace: boolean }) => void> = vi.fn();

vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual<typeof import("react-router-dom")>("react-router-dom");
  return {
    ...actual,
    useNavigate: () => navigateMock,
  };
});

vi.mock("@/shared/auth/session", () => ({
  SESSION_QUERY_KEY: ["auth", "session"] as const,
  logout: () => {
    logoutMock();
  },
  useSession: () => {
    return useSessionMock();
  },
}));

const renderWelcomePage = (queryClient = new QueryClient()) =>
  render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <WelcomePage />
      </MemoryRouter>
    </QueryClientProvider>,
  );

describe("WelcomePage", () => {
  beforeEach(() => {
    useSessionMock.mockReset();
    logoutMock.mockReset();
    navigateMock.mockReset();
  });

  it("renders no-session state when user is not available", async () => {
    useSessionMock.mockReturnValue({ data: null });

    renderWelcomePage();

    expect(await screen.findByRole("heading", { name: t("welcome.noSession.title") })).toBeInTheDocument();
    expect(screen.getByText(t("welcome.noSession.body"))).toBeInTheDocument();
  });

  it("renders greeting when user session is available", async () => {
    useSessionMock.mockReturnValue({
      data: {
        id: 1,
        username: "alice",
        disabled: false,
      },
    });

    renderWelcomePage();

    expect(await screen.findByRole("heading", { name: t("welcome.greeting", { username: "alice" }) })).toBeInTheDocument();
    expect(screen.getByText(t("welcome.sessionActive.body"))).toBeInTheDocument();
    expect(screen.getByRole("button", { name: t("welcome.logout") })).toBeInTheDocument();
  });

  it("runs logout flow and redirects to login", async () => {
    useSessionMock.mockReturnValue({
      data: {
        id: 7,
        username: "bob",
        disabled: false,
      },
    });

    const queryClient = new QueryClient();
    const setQueryDataSpy = vi.spyOn(queryClient, "setQueryData");
    const invalidateQueriesSpy = vi.spyOn(queryClient, "invalidateQueries");
    const user = userEvent.setup();

    renderWelcomePage(queryClient);

    await user.click(await screen.findByRole("button", { name: t("welcome.logout") }));

    await waitFor(() => {
      expect(logoutMock).toHaveBeenCalledTimes(1);
    });
    expect(setQueryDataSpy).toHaveBeenCalledWith(["auth", "session"], null);
    expect(invalidateQueriesSpy).toHaveBeenCalledWith({ queryKey: ["auth", "session"] });
    expect(navigateMock).toHaveBeenCalledWith("/login", { replace: true });
  });
});
