import { useEffect, useState } from "react";
import { outbreakAPI } from "../services/api";
import type { GeoData } from "../services/types";

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

        const hospRes = region ? await outbreakAPI.healthcare.getByRegion(region as string) : await outbreakAPI.healthcare.getFacilities();
        const hospPayload = (hospRes?.data ?? {}) as any;
        const hospData = (hospPayload?.data ?? hospPayload ?? {}) as any;
        const totalsAgg: FacilityTotals = {
          facilities: Number(hospData?.totals?.facilities ?? 0),
          avgBedCapacity: Number(hospData?.totals?.avgBedCapacity ?? 0),
          bedsPer10k: Number(hospData?.totals?.bedsPer10k ?? 0),
        };
        const heatmap = (hospData?.facilitiesGeo ?? {}) as GeoData;

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
        const tPayload = (trendsRes?.data ?? {}) as any;
        const rawTrends = ((tPayload?.data ?? tPayload ?? {}) as any)?.trends ?? [];
        const trends: CapacityPoint[] = (Array.isArray(rawTrends) ? rawTrends : []).map((d: any) => ({
          date: String(d?.date ?? endDate),
          bedsAvailable: Number(d?.bedOccupancy ?? 0),
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