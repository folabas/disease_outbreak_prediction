import { useCallback, useEffect, useState } from "react";
import { outbreakAPI } from "../services/api";
import type { ReportArtifact, ReportsHealth } from "../services/types";

export function useReports(trigger?: number) {
  const [artifacts, setArtifacts] = useState<ReportArtifact[]>([]);
  const [health, setHealth] = useState<ReportsHealth | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | undefined>(undefined);
  const [refreshing, setRefreshing] = useState(false);
  const [refreshOutput, setRefreshOutput] = useState<string | undefined>(undefined);

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      setError(undefined);
      const [artifactsRes, healthRes] = await Promise.all([
        outbreakAPI.analytics.getArtifacts(),
        outbreakAPI.analytics.getHealth(),
      ]);
      setArtifacts(artifactsRes.data?.data?.artifacts ?? []);
      setHealth(healthRes.data?.data?.health ?? null);
    } catch (err: any) {
      setError(err?.message || "Failed to load reporting data");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void fetchData();
  }, [fetchData, trigger]);

  const refreshReports = useCallback(async () => {
    try {
      setRefreshing(true);
      setRefreshOutput(undefined);
      setError(undefined);
      const res = await outbreakAPI.analytics.refreshReports();
      const payload = res.data?.data;
      const combined = `${payload?.stdout ?? ""}\n${payload?.stderr ?? ""}`.trim();
      setRefreshOutput(combined || "Refresh completed.");
      await fetchData();
    } catch (err: any) {
      setError(err?.message || "Failed to refresh reports");
    } finally {
      setRefreshing(false);
    }
  }, [fetchData]);

  return {
    artifacts,
    health,
    loading,
    error,
    refreshing,
    refreshOutput,
    refreshReports,
  } as const;
}
