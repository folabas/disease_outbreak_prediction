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
      // ApiResponse<T> expected
      const body = res?.data as ApiResponse<T>;
      if (mounted.current) {
        setData(body?.data ?? (undefined as unknown as T));
      }
    } catch (e: any) {
      if (mounted.current) {
        setError(e?.message || "Request failed");
      }
    } finally {
      if (mounted.current) {
        setLoading(false);
      }
    }
  }

  return { data, loading, error, refetch: run } as const;
}