import { useEffect, useState } from "react";
import { outbreakAPI } from "../services/api";
import type { Disease } from "../services/types";

type BackendSeriesPoint = { date: string; value: number };
type BackendClimateResponse = {
  region: string;
  temperature: BackendSeriesPoint[];
  rainfall: BackendSeriesPoint[];
};

type ClimatePoint = { name: string; value: number };

export function useForecast(region: string, days: number, disease?: Disease) {
  const [tempData, setTempData] = useState<ClimatePoint[]>([]);
  const [rainData, setRainData] = useState<ClimatePoint[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | undefined>(undefined);

  useEffect(() => {
    let mounted = true;
    async function run() {
      try {
        setLoading(true);
        setError(undefined);
        const res = await outbreakAPI.climate.getForecast(region, days, { disease });
        const payload = (res?.data?.data || res?.data) as unknown as BackendClimateResponse;
        const t = payload?.temperature || [];
        const r = payload?.rainfall || [];
        if (mounted) {
          setTempData(t.map((p) => ({ name: p.date, value: p.value })));
          setRainData(r.map((p) => ({ name: p.date, value: p.value })));
        }
      } catch (e: unknown) {
        const errorMessage = e instanceof Error ? e.message : "Failed to load forecast";
        if (mounted) setError(errorMessage);
      } finally {
        if (mounted) setLoading(false);
      }
    }
    void run();
    return () => {
      mounted = false;
    };
  }, [region, days, disease]);

  return { tempData, rainData, loading, error } as const;
}