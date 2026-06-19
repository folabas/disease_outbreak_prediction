import { useEffect, useState } from "react";
import { api } from "../services/api.config";
import { normalizeDate, sortByDate } from "../utils/dateUtils";

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
          const rawSeries = Array.isArray(data?.series) ? data.series : [];
          // Normalize date formats and ensure proper types
          const normalizedSeries: SeriesItem[] = rawSeries.map((item: any) => ({
            date: normalizeDate(item?.date || item?.name || ""),
            actual: typeof item?.actual === "number" ? item.actual : (item?.actual === null ? null : undefined),
            predicted: typeof item?.predicted === "number" ? item.predicted : (item?.predicted === null ? null : undefined),
          })).filter((item: SeriesItem) => item.date); // Filter out items without valid dates
          
          // Sort by date
          const sorted = sortByDate(normalizedSeries);
          setSeries(sorted);
          setLiveOnly(Boolean(data?.live_only));
        }
      } catch (e: unknown) {
        const errorMessage = e instanceof Error ? e.message : "Failed to load chart data";
        if (mounted) setError(errorMessage);
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