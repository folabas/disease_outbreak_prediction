import { useEffect, useMemo, useState } from "react";
import { outbreakAPI } from "../services/api";
import type { Disease, DiseaseData, OutbreakPrediction } from "../services/types";

type PredictionSeriesPoint = { name: string; value: number };
type RiskSummary = { level: string; confidence: number };

export function usePredictions(disease: Disease, region: string, trigger?: number) {
  const [series, setSeries] = useState<PredictionSeriesPoint[]>([]);
  const [risk, setRisk] = useState<RiskSummary | undefined>(undefined);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | undefined>(undefined);

  useEffect(() => {
    let mounted = true;
    async function run() {
      try {
        setLoading(true);
        setError(undefined);

        // Historical disease cases for chart
        const now = new Date();
        const endDate = now.toISOString();
        const start = new Date(now);
        start.setMonth(start.getMonth() - 12);
        const startDate = start.toISOString();
        const histRes = await outbreakAPI.disease.getHistorical({
          disease,
          region,
          startDate,
          endDate,
        });
        const histData = (histRes?.data?.data ?? []) as DiseaseData[];
        const seriesPoints: PredictionSeriesPoint[] = histData.map((d) => ({
          name: d?.period?.end || d?.period?.start,
          value: d?.cases?.confirmed ?? 0,
        }));

        // Regional prediction for risk
        const predRes = await outbreakAPI.predictions.getByRegion(region);
        const outbreak = (predRes?.data?.data ?? {}) as OutbreakPrediction;
        const riskLevel = outbreak?.riskLevel;
        const level = riskLevel ? riskLevel.charAt(0).toUpperCase() + riskLevel.slice(1) : "Unknown";
        const confidence = Number(((outbreak?.confidence ?? 0) * 100).toFixed(1));

        if (mounted) {
          setSeries(seriesPoints);
          setRisk({ level, confidence });
        }
      } catch (e: any) {
        if (mounted) setError(e?.message || "Failed to load prediction data");
      } finally {
        if (mounted) setLoading(false);
      }
    }
    void run();
    return () => {
      mounted = false;
    };
  }, [disease, region, trigger]);

  const stats = useMemo(() => {
    const latest = series.length > 0 ? series[series.length - 1].value : 0;
    const avg =
      series.length > 0
        ? Number((series.reduce((s, p) => s + p.value, 0) / series.length).toFixed(2))
        : 0;
    return { latest, average: isFinite(avg) ? avg : 0 };
  }, [series]);

  return { series, risk, stats, loading, error } as const;
}