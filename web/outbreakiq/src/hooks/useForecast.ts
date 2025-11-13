import { useEffect, useState } from "react";
import { outbreakAPI } from "../services/api";

type BackendSeriesPoint = { date: string; value: number };
type BackendClimateResponse = {
  region: string;
  temperature: BackendSeriesPoint[];
  rainfall: BackendSeriesPoint[];
};

type ClimatePoint = { name: string; value: number };

export function useForecast(region: string, days: number) {
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
        const res = await outbreakAPI.climate.getForecast(region, days);
        const payload = (res?.data?.data || res?.data) as unknown as BackendClimateResponse;
        const t = payload?.temperature || [];
        const r = payload?.rainfall || [];
        if (mounted) {
          setTempData(t.map((p) => ({ name: p.date, value: p.value })));
          setRainData(r.map((p) => ({ name: p.date, value: p.value })));
        }
      } catch (e: any) {
        if (mounted) setError(e?.message || "Failed to load forecast");
      } finally {
        if (mounted) setLoading(false);
      }
    }
    void run();
    return () => {
      mounted = false;
    };
  }, [region, days]);

  return { tempData, rainData, loading, error } as const;
}