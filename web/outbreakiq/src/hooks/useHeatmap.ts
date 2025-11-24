import { useEffect, useState } from "react";
import { outbreakAPI } from "../services/api";
import type { Disease, GeoData } from "../services/types";

export function useHeatmap(region: string, disease: Disease, trigger?: number) {
  const [geojson, setGeojson] = useState<GeoData | undefined>(undefined);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | undefined>(undefined);

  useEffect(() => {
    let mounted = true;
    async function run() {
      try {
        setLoading(true);
        setError(undefined);
        const res = await outbreakAPI.geo.getHeatmap({ dataType: "risk", region, disease });
        const data = (res?.data?.data || res?.data) as GeoData | undefined;
        if (mounted) setGeojson(data);
      } catch (e: unknown) {
        const errorMessage = e instanceof Error ? e.message : "Failed to load heatmap";
        if (mounted) setError(errorMessage);
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
  }, [region, disease, trigger]);

  return { geojson, loading, error } as const;
}