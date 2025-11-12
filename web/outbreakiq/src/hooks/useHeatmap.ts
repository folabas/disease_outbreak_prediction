import { useEffect, useState } from "react";
import { outbreakAPI } from "../services/api";

export function useHeatmap(region: string, disease: string) {
  const [geojson, setGeojson] = useState<any | undefined>(undefined);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | undefined>(undefined);

  useEffect(() => {
    let mounted = true;
    async function run() {
      try {
        setLoading(true);
        setError(undefined);
        const res = await outbreakAPI.geo.getHeatmap({ dataType: "risk", region });
        const data = res?.data?.data;
        if (mounted) setGeojson(data);
      } catch (e: any) {
        if (mounted) setError(e?.message || "Failed to load heatmap");
      } finally {
        if (mounted) setLoading(false);
      }
    }
    void run();
    return () => {
      mounted = false;
    };
  }, [region, disease]);

  return { geojson, loading, error } as const;
}