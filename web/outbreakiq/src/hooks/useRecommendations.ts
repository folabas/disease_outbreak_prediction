import { useEffect, useState } from "react";
import { outbreakAPI } from "../services/api";

export function useRecommendations(params?: { disease?: string; region?: string; year?: number }) {
  const [recommendations, setRecommendations] = useState<string[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | undefined>(undefined);

  useEffect(() => {
    let mounted = true;
    async function run() {
      try {
        setLoading(true);
        setError(undefined);
        const res = await outbreakAPI.recommendations.get({ disease: params?.disease, region: params?.region, year: params?.year });
        const data = res?.data?.data || {};
        const recs = Array.isArray(data?.recommendations) ? data.recommendations : [];
        if (mounted) setRecommendations(recs);
      } catch (e: any) {
        if (mounted) setError(e?.message || "Failed to load recommendations");
      } finally {
        if (mounted) setLoading(false);
      }
    }
    void run();
    return () => {
      mounted = false;
    };
  }, [params?.disease, params?.region, params?.year]);

  return { recommendations, loading, error } as const;
}