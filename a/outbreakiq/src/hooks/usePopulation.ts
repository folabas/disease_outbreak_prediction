import { useEffect, useMemo, useState } from "react";
import { outbreakAPI } from "../services/api";

type GrowthEntry = { region: string; value: number };
type BackendPopulationResponse = {
  region?: string;
  totalPopulation?: number | null;
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

type PopulationHookReturn = {
  growthData: GrowthEntry[];
  densityData: GrowthEntry[];
  densityMap: DensityMap | undefined;
  stats: PopulationStats;
  totalPopulation: number | null;
  loading: boolean;
  error: string | undefined;
};

export function usePopulation(region?: string, params?: { startDate?: string; endDate?: string }) {
  const [growthData, setGrowthData] = useState<GrowthEntry[]>([]);
  const [densityData, setDensityData] = useState<GrowthEntry[]>([]);
  const [densityMap, setDensityMap] = useState<DensityMap | undefined>(undefined);
  const [totalPopulation, setTotalPopulation] = useState<number | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | undefined>(undefined);

  useEffect(() => {
    let mounted = true;
    async function run() {
      try {
        setLoading(true);
        setError(undefined);
        // aggregate/population current
        const popRes = await outbreakAPI.population.getCurrent({ region, startDate: params?.startDate, endDate: params?.endDate });
        const pop = (popRes?.data?.data || popRes?.data) as unknown as BackendPopulationResponse;
        const growth = pop?.growthRates || [];
        const density = pop?.density || [];
        const total = pop?.totalPopulation ?? null;

        // density-map geojson
        const mapRes = await outbreakAPI.population.getDensityMap();
        const map = (mapRes?.data?.data || mapRes?.data) as unknown as DensityMap;

        if (mounted) {
          setGrowthData(growth);
          setDensityData(density);
          setDensityMap(map);
          setTotalPopulation(total);
        }
      } catch (e: unknown) {
        const errorMessage = e instanceof Error ? e.message : "Failed to load population data";
        if (mounted) setError(errorMessage);
      } finally {
        if (mounted) setLoading(false);
      }
    }
    void run();
    return () => {
      mounted = false;
    };
  }, [region, params?.startDate, params?.endDate]);

  const stats: PopulationStats = useMemo(() => {
    const isAll = !region || ["all nigeria", "all regions"].includes(String(region).toLowerCase());
    const normalize = (name: string) => {
      const n = String(name || "").trim().toLowerCase();
      const cleaned = n.replace(/\s+state$/i, "").replace(/^state\s+/i, "");
      if (["fct", "fct abuja", "abuja", "federal capital territory"].includes(cleaned)) return "abuja";
      if (cleaned === "cross river state" || cleaned === "cross river") return "cross river";
      return cleaned;
    };
    let avgDensity = 0;
    if (isAll) {
      const val = densityData.reduce((s, d) => s + (d.value || 0), 0) / (densityData.length || 1);
      avgDensity = Number(val.toFixed(2));
    } else {
      const target = normalize(String(region));
      const match = densityData.find((d) => normalize(String(d.region)) === target);
      if (match && typeof match.value === "number") {
        avgDensity = Number((match.value).toFixed(2));
      } else {
        const val = densityData.reduce((s, d) => s + (d.value || 0), 0) / (densityData.length || 1);
        avgDensity = Number(val.toFixed(2));
      }
    }
    const top = [...growthData].sort((a, b) => (b.value ?? 0) - (a.value ?? 0))[0]?.region;
    return { avgDensity: isFinite(avgDensity) ? avgDensity : 0, topGrowthRegion: top };
  }, [growthData, densityData, region]);

  return { growthData, densityData, densityMap, stats, totalPopulation, loading, error } as const;
}