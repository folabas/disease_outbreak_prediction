import { useEffect, useMemo, useState } from "react";
import { outbreakAPI } from "../services/api";
import type { Disease } from "../services/types";

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
        // Normalize date formats
        const { normalizeDate, sortByDate } = await import("../utils/dateUtils");
        const rawPoints: PredictionSeriesPoint[] = items.map((d: unknown) => {
          const item = d as Record<string, unknown>;
          const period = item?.period as { end?: string; start?: string } | undefined;
          const dateStr = period?.end || period?.start || String(item?.date || item?.name || "");
          const casesValue = item?.cases;
          const casesNum = typeof casesValue === "object" && casesValue !== null
            ? Number((casesValue as { confirmed?: number; total?: number })?.confirmed ?? (casesValue as { confirmed?: number; total?: number })?.total ?? 0)
            : Number(casesValue || 0);
          return {
            name: normalizeDate(dateStr),
            value: casesNum,
          };
        }).filter((p) => p.name); // Filter out invalid dates
        
        // Aggregate by normalized date
        const totals: Record<string, number> = {};
        const order: string[] = [];
        for (const p of rawPoints) {
          const k = String(p.name || "");
          if (!totals.hasOwnProperty(k)) order.push(k);
          totals[k] = (totals[k] || 0) + (Number(p.value) || 0);
        }
        // Sort by date
        const seriesPoints: PredictionSeriesPoint[] = sortByDate(
          order.map((k) => ({ name: k, value: totals[k] }))
        )

        // Explicit prediction via POST (includes disease + region)
        const predRes = await outbreakAPI.predictions.postPredict({ disease, region });
        const { normalizeApiResponse } = await import("../utils/apiUtils");
        const payload = normalizeApiResponse<{ summary?: { riskLevel?: string; confidence?: number } }>(predRes);
        const summary = payload?.summary ?? {};
        const rl: string | undefined = summary?.riskLevel;
        const level = rl ? rl.charAt(0).toUpperCase() + rl.slice(1) : "Unknown";
        const confidence = Number(((summary?.confidence ?? 0) * 100).toFixed(1));

        if (mounted) {
          setSeries(seriesPoints);
          setRisk({ level, confidence });
        }
      } catch (e: unknown) {
        const errorMessage = e instanceof Error ? e.message : "Failed to load prediction data";
        if (mounted) setError(errorMessage);
      } finally {
        if (mounted) setLoading(false);
      }
    }
    if (trigger === undefined || trigger > 0) {
      void run();
    }
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