import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { QueryClientProvider } from "@tanstack/react-query";
import { RouterProvider, createBrowserRouter } from "react-router-dom";

import { appRoutes } from "@/app/routes";
import { createQueryClient } from "@/app/query-client";
import { readFrontendEnvConfig } from "@/shared/api/env";
import { installGlobalRuntimeErrorHandlers } from "@/shared/observability/runtime-errors";
import "@/app/styles.css";

readFrontendEnvConfig();
installGlobalRuntimeErrorHandlers();

const router = createBrowserRouter(appRoutes);
const queryClient = createQueryClient();

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>
  </StrictMode>
);
