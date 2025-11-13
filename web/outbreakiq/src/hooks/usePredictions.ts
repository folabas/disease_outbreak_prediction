import { useEffect, useMemo, useState } from "react";
import { outbreakAPI } from "../services/api";
import type { Disease, DiseaseData, OutbreakPrediction } from "../services/types";

type PredictionSeriesPoint = { name: string; value: number };
type RiskSummary = { level: string; confidence: number };

export function usePredictions(disease: Disease, region: string, trigger?: number) {
  const [series, setSeries] = useState<PredictionSeriesPoint[]>([]);
  const [risk, setRisk] = useState<RiskSummary | undefined>(undefined);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | undefined>(undefined);

  useEffect(() => {
    let mounted = true;
    async function run() {
      try {
        setLoading(true);
        setError(undefined);

        // Historical disease cases for chart (only on explicit trigger)
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
        const payloadAny: any = histRes?.data?.data ?? {};
        const items: any[] = Array.isArray(payloadAny)
          ? payloadAny
          : Array.isArray(payloadAny?.history)
          ? payloadAny.history
          : [];
        const rawPoints: PredictionSeriesPoint[] = items.map((d: any) => ({
          name: d?.period?.end || d?.period?.start || d?.date,
          value: d?.cases?.confirmed ?? d?.cases ?? 0,
        }));
        const totals: Record<string, number> = {};
        const order: string[] = [];
        for (const p of rawPoints) {
          const k = String(p.name || "");
          if (!totals.hasOwnProperty(k)) order.push(k);
          totals[k] = (totals[k] || 0) + (Number(p.value) || 0);
        }
        const seriesPoints: PredictionSeriesPoint[] = order.map((k) => ({ name: k, value: totals[k] }))

        // Explicit prediction via POST (includes disease + region)
        const predRes = await outbreakAPI.predictions.postPredict({ disease, region });
        const payload: any = predRes?.data?.data ?? predRes?.data ?? {};
        const summary = payload?.summary ?? {};
        const rl: string | undefined = summary?.riskLevel;
        const level = rl ? rl.charAt(0).toUpperCase() + rl.slice(1) : "Unknown";
        const confidence = Number(((summary?.confidence ?? 0) * 100).toFixed(1));

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
    if (trigger && trigger > 0) {
      void run();
    }
    return () => {
      mounted = false;
    };
  }, [trigger]);

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