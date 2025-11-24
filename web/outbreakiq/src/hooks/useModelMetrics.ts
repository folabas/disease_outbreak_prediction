import { useEffect, useState } from "react";
import { outbreakAPI } from "../services/api";
import type {
  AlertMetricRow,
  ModelMetricRow,
  RegressionMetricRow,
} from "../services/types";

interface UseModelMetricsOptions {
  disease?: string;
}

interface MetricsState {
  model?: ModelMetricRow;
  regression?: RegressionMetricRow;
  alert?: AlertMetricRow;
}

export function useModelMetrics(options?: UseModelMetricsOptions) {
  const [data, setData] = useState<MetricsState>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | undefined>(undefined);

  useEffect(() => {
    let mounted = true;
    async function run() {
      try {
        setLoading(true);
        setError(undefined);

        const [modelRes, regressionRes, alertRes] = await Promise.allSettled([
          outbreakAPI.analytics.getModelMetrics({ disease: options?.disease }),
          outbreakAPI.analytics.getRegressionMetrics(),
          outbreakAPI.analytics.getAlertMetrics({ disease: options?.disease }),
        ]);

        if (!mounted) return;
        const next: MetricsState = {};

        if (modelRes.status === "fulfilled") {
          const rows = modelRes.value.data?.data?.rows ?? [];
          next.model = rows.find((row: ModelMetricRow) =>
            options?.disease ? row.disease?.toLowerCase() === options.disease?.toLowerCase() : true
          );
        }
        if (regressionRes.status === "fulfilled") {
          const rows = regressionRes.value.data?.data?.rows ?? [];
          next.regression = rows.find((row: RegressionMetricRow) =>
            options?.disease ? row.disease?.toLowerCase() === options.disease?.toLowerCase() : true
          );
        }
        if (alertRes.status === "fulfilled") {
          const rows = alertRes.value.data?.data?.rows ?? [];
          next.alert = rows.find((row: AlertMetricRow) =>
            options?.disease ? row.disease?.toLowerCase() === options.disease?.toLowerCase() : true
          );
        }

        setData(next);
      } catch (err: any) {
        if (mounted) {
          setError(err?.message || "Failed to load metrics");
        }
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    }

    void run();
    return () => {
      mounted = false;
    };
  }, [options?.disease]);

  return { data, loading, error } as const;
}
