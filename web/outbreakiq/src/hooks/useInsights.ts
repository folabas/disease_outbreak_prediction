import { useEffect, useState } from "react";
import { outbreakAPI } from "../services/api";
import type { FeatureImportanceEntry, InsightMetricsSummary, InsightsAnalyticsResponse } from "../services/types";

export function useInsights(disease: string, region?: string, trigger?: number) {
  const [metrics, setMetrics] = useState<InsightMetricsSummary | undefined>(undefined);
  const [featureImportance, setFeatureImportance] = useState<FeatureImportanceEntry[]>([]);
  const [notes, setNotes] = useState<string[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | undefined>(undefined);

  useEffect(() => {
    let mounted = true;
    async function run() {
      try {
        setLoading(true);
        setError(undefined);
        const res = await outbreakAPI.analytics.getInsights({ disease, region });
        const payload = (res?.data?.data ?? {}) as InsightsAnalyticsResponse;
        if (mounted) {
          setMetrics(payload?.metrics);
          setFeatureImportance(payload?.featureImportance || []);

          const incomingNotes = payload?.notes;
          if (Array.isArray(incomingNotes)) {
            setNotes(incomingNotes);
          } else if (typeof incomingNotes === "string") {
            setNotes([incomingNotes]);
          } else {
            setNotes([]);
          }
        }
      } catch (e: unknown) {
        const errorMessage = e instanceof Error ? e.message : "Failed to load insights";
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

  return { metrics, featureImportance, notes, loading, error } as const;
}