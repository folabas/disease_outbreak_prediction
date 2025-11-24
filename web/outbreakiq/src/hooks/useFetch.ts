import { useEffect, useRef, useState } from "react";
import type { AxiosResponse } from "axios";
import type { ApiResponse } from "../services/types";

type UseFetchOptions = {
  immediate?: boolean;
};

export function useFetch<T>(
  fetcher: () => Promise<AxiosResponse<ApiResponse<T>>>,
  deps: any[] = [],
  options: UseFetchOptions = { immediate: true }
) {
  const [data, setData] = useState<T | undefined>(undefined);
  const [loading, setLoading] = useState<boolean>(options.immediate ?? true);
  const [error, setError] = useState<string | undefined>(undefined);
  const mounted = useRef(true);

  useEffect(() => {
    mounted.current = true;
    if (options.immediate) {
      void run();
    }
    return () => {
      mounted.current = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  async function run() {
    try {
      setLoading(true);
      setError(undefined);
      const res = await fetcher();
      // Normalize API response structure
      const { normalizeApiResponse } = await import("../utils/apiUtils");
      const normalized = normalizeApiResponse<T>(res);
      if (mounted.current) {
        setData(normalized);
      }
    } catch (e: unknown) {
      if (mounted.current) {
        const { extractErrorMessage } = await import("../utils/apiUtils");
        const errorMessage = extractErrorMessage(e);
        setError(errorMessage);
      }
    } finally {
      if (mounted.current) {
        setLoading(false);
      }
    }
  }

  return { data, loading, error, refetch: run } as const;
}