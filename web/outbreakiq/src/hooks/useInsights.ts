import { useEffect, useState } from "react";
import { api } from "../services/api.config";

type BackendInsights = {
  metrics?: { accuracy?: number; f1?: number; precision?: number; recall?: number; auc?: number };
  featureImportance?: Array<{ feature?: string; importance?: number; name?: string; value?: number }>;
  notes?: string | string[];
};

export function useInsights(disease: string, region?: string, trigger?: number) {
  const [metrics, setMetrics] = useState<BackendInsights["metrics"] | undefined>(undefined);
  const [featureImportance, setFeatureImportance] = useState<BackendInsights["featureImportance"]>([]);
  const [notes, setNotes] = useState<string[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | undefined>(undefined);

  useEffect(() => {
    let mounted = true;
    async function run() {
      try {
        setLoading(true);
        setError(undefined);
        const res = await api.get("/analytics/insights", { params: { disease, region } });
        const payload = (res?.data?.data ?? {}) as BackendInsights;
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
      } catch (e: any) {
        if (mounted) setError(e?.message || "Failed to load insights");
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