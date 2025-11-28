import { useEffect, useState } from "react";
import { outbreakAPI } from "../services/api";
import type { Disease, OutbreakAlert } from "../services/types";

export function useDiseaseAlerts(disease: Disease, region?: string, threshold = 0.7) {
  const [alerts, setAlerts] = useState<OutbreakAlert[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | undefined>(undefined);

  useEffect(() => {
    let mounted = true;
    async function run() {
      try {
        setLoading(true);
        setError(undefined);
        const res = await outbreakAPI.disease.getAlerts({ disease, region, threshold });
        const payload = (res?.data?.data ?? res?.data) as OutbreakAlert[] | undefined;
        const alertsList = Array.isArray(payload) ? payload : [];
        if (mounted) setAlerts(alertsList);
      } catch (e: unknown) {
        const errorMessage = e instanceof Error ? e.message : "Failed to load disease alerts";
        if (mounted) setError(errorMessage);
      } finally {
        if (mounted) setLoading(false);
      }
    }
    void run();
    return () => {
      mounted = false;
    };
  }, [disease, region, threshold]);

  return { alerts, loading, error } as const;
}

