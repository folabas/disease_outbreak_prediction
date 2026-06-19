import { useEffect, useState } from "react";
import { outbreakAPI } from "../services/api";
import type { Disease, HotspotEntry } from "../services/types";

export interface HotspotFeature {
  region: string;
  score: number;
}

export function useHotspots(disease: Disease, year: number | undefined, topNOrTrigger: number = 5) {
  const [features, setFeatures] = useState<HotspotFeature[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | undefined>(undefined);

  // If topNOrTrigger is > 20, treat it as a trigger (reload counter), otherwise as topN
  // This maintains backward compatibility with pages that pass reload as the third param
  const topN = topNOrTrigger > 20 ? 5 : Math.max(1, Math.min(20, topNOrTrigger));

  useEffect(() => {
    let mounted = true;
    async function run() {
      try {
        setLoading(true);
        setError(undefined);
        const res = await outbreakAPI.analytics.getHotspots({ disease, year, top_n: topN });
        const payload = (res?.data?.data ?? res?.data) as { hotspots?: HotspotEntry[] } | undefined;
        const arr = Array.isArray(payload?.hotspots) ? payload!.hotspots : [];
        if (mounted) {
          setFeatures(arr.map((entry) => ({ 
            region: String(entry.region || ""), 
            score: Number(entry.score || 0) 
          })));
        }
      } catch (e: unknown) {
        const errorMessage = e instanceof Error ? e.message : "Failed to load hotspots";
        if (mounted) setError(errorMessage);
      } finally {
        if (mounted) setLoading(false);
      }
    }
    void run();
    return () => {
      mounted = false;
    };
  }, [disease, year, topNOrTrigger, topN]);

  return { features, loading, error } as const;
}