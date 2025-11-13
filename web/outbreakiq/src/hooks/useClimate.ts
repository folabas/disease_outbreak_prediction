import { useEffect, useMemo, useState } from "react";
import { outbreakAPI } from "../services/api";

type BackendSeriesPoint = { date: string; value: number };
type BackendClimateResponse = {
  region: string;
  temperature: BackendSeriesPoint[];
  rainfall: BackendSeriesPoint[];
};

type ClimatePoint = { name: string; value: number };
type ClimateStats = {
  avgTemp: number;
  totalRain: number;
  highTemp: number;
  heavyRain: number;
};

export function useClimate(region: string, params?: { startDate?: string; endDate?: string }) {
  const [tempData, setTempData] = useState<ClimatePoint[]>([]);
  const [rainData, setRainData] = useState<ClimatePoint[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | undefined>(undefined);

  useEffect(() => {
    let mounted = true;
    async function run() {
      try {
        setLoading(true);
        setError(undefined);
        const res = await outbreakAPI.climate.getByRegion(region, { startDate: params?.startDate, endDate: params?.endDate });
        const payload = (res?.data?.data || res?.data) as unknown as BackendClimateResponse;
        const t = payload?.temperature || [];
        const r = payload?.rainfall || [];
        if (mounted) {
          setTempData(t.map((p) => ({ name: p.date, value: p.value })));
          setRainData(r.map((p) => ({ name: p.date, value: p.value })));
        }
      } catch (e: any) {
        if (mounted) setError(e?.message || "Failed to load climate data");
      } finally {
        if (mounted) setLoading(false);
      }
    }
    void run();
    return () => {
      mounted = false;
    };
  }, [region, params?.startDate, params?.endDate]);

  const stats: ClimateStats = useMemo(() => {
    const avgTemp =
      tempData.length > 0
        ? Number(
            (
              tempData.reduce((sum, p) => sum + p.value, 0) / tempData.length
            ).toFixed(2)
          )
        : 0;
    const totalRain = Number(rainData.reduce((sum, p) => sum + p.value, 0).toFixed(2));
    const highTemp = tempData.reduce((m, p) => (p.value > m ? p.value : m), -Infinity);
    const heavyRain = rainData.reduce((m, p) => (p.value > m ? p.value : m), -Infinity);
    return {
      avgTemp: isFinite(avgTemp) ? avgTemp : 0,
      totalRain: isFinite(totalRain) ? totalRain : 0,
      highTemp: isFinite(highTemp) ? highTemp : 0,
      heavyRain: isFinite(heavyRain) ? heavyRain : 0,
    };
  }, [tempData, rainData]);

  return { tempData, rainData, stats, loading, error } as const;
}