import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
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
vi.mock("@/shared/auth/session", () => ({
  useSession: () => {
    return useSessionMock();
  },
}));

const renderWelcomePage = () =>
  render(
    <QueryClientProvider client={new QueryClient()}>
      <MemoryRouter>
        <WelcomePage />
      </MemoryRouter>
    </QueryClientProvider>,
  );

describe("WelcomePage", () => {
  beforeEach(() => {
    useSessionMock.mockReset();
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
    expect(screen.queryByRole("button", { name: t("welcome.logout") })).not.toBeInTheDocument();
  });
});
