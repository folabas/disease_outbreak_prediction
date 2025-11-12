import { useEffect, useState } from "react";
import { outbreakAPI } from "../services/api";
import type { HospitalData, GeoData } from "../services/types";

type FacilityTotals = {
  facilities: number;
  avgBedCapacity: number;
  bedsPer10k: number;
};

type CapacityPoint = { date: string; bedsAvailable: number };

export function useHospitals(region?: string) {
  const [totals, setTotals] = useState<FacilityTotals | undefined>(undefined);
  const [facilitiesGeo, setFacilitiesGeo] = useState<GeoData | undefined>(undefined);
  const [capacityTrends, setCapacityTrends] = useState<CapacityPoint[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | undefined>(undefined);

  useEffect(() => {
    let mounted = true;
    async function run() {
      try {
        setLoading(true);
        setError(undefined);

        // Facilities list (aggregate to totals)
        const hospRes = await outbreakAPI.healthcare.getFacilities();
        const list = (hospRes?.data?.data ?? []) as HospitalData[];
        const facilities = list.reduce(
          (sum, d) => sum + (d?.facilities?.total ?? 0),
          0
        );
        const avgBedCapacity =
          list.length > 0
            ? Number(
                (
                  list.reduce((s, d) => s + (d?.capacity?.beds ?? 0), 0) /
                  list.length
                ).toFixed(2)
              )
            : 0;
        const totalsAgg: FacilityTotals = {
          facilities,
          avgBedCapacity: isFinite(avgBedCapacity) ? avgBedCapacity : 0,
          bedsPer10k: 0, // Not available from current schema
        };

        // Facilities heatmap (GeoData)
        const heatmapRes = await outbreakAPI.geo.getHeatmap({
          dataType: "facilities",
          region: region || undefined,
        });
        const heatmap = (heatmapRes?.data?.data ?? {}) as GeoData;

        // Capacity trends require params
        const now = new Date();
        const endDate = now.toISOString();
        const start = new Date(now);
        start.setMonth(start.getMonth() - 6);
        const startDate = start.toISOString();
        const trendsRes = await outbreakAPI.healthcare.getCapacityTrends({
          region: (region || "All") as string,
          startDate,
          endDate,
        });
        const rawTrends = (trendsRes?.data?.data ?? []) as HospitalData[];
        const trends: CapacityPoint[] = rawTrends.map((d) => ({
          date: d?.lastUpdated ?? endDate,
          bedsAvailable: d?.capacity?.beds ?? 0,
        }));

        if (mounted) {
          setTotals(totalsAgg);
          setFacilitiesGeo(heatmap);
          setCapacityTrends(trends);
        }
      } catch (e: any) {
        if (mounted) setError(e?.message || "Failed to load hospital data");
      } finally {
        if (mounted) setLoading(false);
      }
    }
    void run();
    return () => {
      mounted = false;
    };
  }, [region]);

  return { totals, facilitiesGeo, capacityTrends, loading, error } as const;
}