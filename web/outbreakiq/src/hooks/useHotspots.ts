import { useEffect, useState } from "react";
import { outbreakAPI } from "../services/api";
import type { Disease } from "../services/types";

export function useHotspots(disease: Disease, year: number) {
  const [features, setFeatures] = useState<any[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | undefined>(undefined);

  useEffect(() => {
    let mounted = true;
    async function run() {
      try {
        setLoading(true);
        setError(undefined);
        const res = await outbreakAPI.analytics.getHotspots({ disease, year });
        const body: any = res?.data ?? {};
        const data: any = body?.data ?? body;
        const arr = Array.isArray(data?.hotspots) ? data.hotspots : (Array.isArray(data) ? data : []);
        if (mounted) setFeatures(arr);
      } catch (e: any) {
        if (mounted) setError(e?.message || "Failed to load hotspots");
      } finally {
        if (mounted) setLoading(false);
      }
    }
    void run();
    return () => {
      mounted = false;
    };
  }, [disease, year]);

  return { features, loading, error } as const;
}