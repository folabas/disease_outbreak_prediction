import { useEffect, useState } from "react";
import { outbreakAPI } from "../services/api";
import type { Disease, RecommendationsResponse } from "../services/types";

export function useRecommendations(params?: { disease?: Disease; region?: string; year?: number }, trigger?: number) {
  const [recommendations, setRecommendations] = useState<string[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | undefined>(undefined);

  useEffect(() => {
    let mounted = true;
    async function run() {
      try {
        setLoading(true);
        setError(undefined);
        const res = await outbreakAPI.recommendations.get({ 
          disease: params?.disease, 
          region: params?.region, 
          year: params?.year 
        });
        const payload = (res?.data?.data ?? res?.data) as RecommendationsResponse | undefined;
        const recs = Array.isArray(payload?.recommendations) ? payload!.recommendations : [];
        if (mounted) setRecommendations(recs);
      } catch (e: unknown) {
        const errorMessage = e instanceof Error ? e.message : "Failed to load recommendations";
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
  }, [params?.disease, params?.region, params?.year, trigger]);

  return { recommendations, loading, error } as const;
}