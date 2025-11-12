import { useEffect, useMemo, useState } from "react";
import { outbreakAPI } from "../services/api";

type GrowthEntry = { region: string; value: number };
type BackendPopulationResponse = {
  region?: string;
  growthRates?: GrowthEntry[];
  density?: GrowthEntry[];
};

type GeoFeature = {
  type: "Feature";
  geometry: { type: string; coordinates: any };
  properties: Record<string, any> & { region?: string; density?: number };
};

type DensityMap = {
  type: "FeatureCollection";
  features: GeoFeature[];
};

type PopulationStats = {
  avgDensity: number;
  topGrowthRegion: string | undefined;
};

export function usePopulation(region?: string) {
  const [growthData, setGrowthData] = useState<GrowthEntry[]>([]);
  const [densityData, setDensityData] = useState<GrowthEntry[]>([]);
  const [densityMap, setDensityMap] = useState<DensityMap | undefined>(undefined);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | undefined>(undefined);

  useEffect(() => {
    let mounted = true;
    async function run() {
      try {
        setLoading(true);
        setError(undefined);
        // aggregate/population current
        const popRes = await outbreakAPI.population.getCurrent();
        const pop = (popRes?.data?.data || popRes?.data) as unknown as BackendPopulationResponse;
        const growth = pop?.growthRates || [];
        const density = pop?.density || [];

        // density-map geojson
        const mapRes = await outbreakAPI.population.getDensityMap();
        const map = (mapRes?.data?.data || mapRes?.data) as unknown as DensityMap;

        if (mounted) {
          setGrowthData(growth);
          setDensityData(density);
          setDensityMap(map);
        }
      } catch (e: any) {
        if (mounted) setError(e?.message || "Failed to load population data");
      } finally {
        if (mounted) setLoading(false);
      }
    }
    void run();
    return () => {
      mounted = false;
    };
  }, [region]);

  const stats: PopulationStats = useMemo(() => {
    const avgDensity = Number(
      (densityData.reduce((s, d) => s + (d.value || 0), 0) / (densityData.length || 1)).toFixed(2)
    );
    const top = [...growthData].sort((a, b) => (b.value ?? 0) - (a.value ?? 0))[0]?.region;
    return { avgDensity: isFinite(avgDensity) ? avgDensity : 0, topGrowthRegion: top };
  }, [growthData, densityData]);

  return { growthData, densityData, densityMap, stats, loading, error } as const;
}