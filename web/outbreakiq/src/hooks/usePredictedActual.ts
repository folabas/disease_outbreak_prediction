import { useEffect, useState } from "react";
import { api } from "../services/api.config";

type SeriesItem = { date: string; actual?: number | null; predicted?: number | null };

export function usePredictedActual(params: { disease: string; region: string; window?: number }, trigger?: number) {
  const [series, setSeries] = useState<SeriesItem[]>([]);
  const [liveOnly, setLiveOnly] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | undefined>(undefined);

  useEffect(() => {
    let mounted = true;
    async function run() {
      try {
        setLoading(true);
        setError(undefined);
        const res = await api.get("/charts/predicted-actual", {
          params: { disease: params.disease, region: params.region, window: params.window ?? 30 },
        });
        const body = res?.data || {};
        const data = body?.data || {};
        if (mounted) {
          setSeries(Array.isArray(data?.series) ? data.series : []);
          setLiveOnly(Boolean(data?.live_only));
        }
      } catch (e: any) {
        if (mounted) setError(e?.message || "Failed to load chart data");
      } finally {
        if (mounted) setLoading(false);
      }
    }
    if (trigger && trigger > 0) {
      void run();
    }
    return () => {
      mounted = false;
    };
  }, [params.disease, params.region, params.window, trigger]);

  return { series, liveOnly, loading, error } as const;
}