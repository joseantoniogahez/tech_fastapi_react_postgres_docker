import { QueryClient } from "@tanstack/react-query";

import { defaultMutationPolicy } from "@/app/mutation-policy";
import { defaultQueryPolicy } from "@/app/query-policy";

export const createQueryClient = (): QueryClient =>
  new QueryClient({
    defaultOptions: {
      queries: {
        ...defaultQueryPolicy,
      },
      mutations: {
        ...defaultMutationPolicy,
      },
    },
  });
