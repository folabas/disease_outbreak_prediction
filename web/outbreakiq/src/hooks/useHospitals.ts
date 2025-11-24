import { useEffect, useState } from "react";
import { outbreakAPI } from "../services/api";
import type { GeoData, HospitalData } from "../services/types";

type FacilityTotals = {
  facilities: number;
  avgBedCapacity: number;
  bedsPer10k: number;
};

type CapacityPoint = { date: string; bedsAvailable: number };

interface HospitalResponseData {
  region?: string;
  totals?: {
    facilities?: number;
    avgBedCapacity?: number;
    bedsPer10k?: number;
  };
  facilitiesGeo?: GeoData;
}

interface CapacityTrendsResponse {
  region?: string;
  trends?: Array<{
    date?: string;
    bedOccupancy?: number;
  }>;
}

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

        const hospRes = region
          ? await outbreakAPI.healthcare.getByRegion(region)
          : await outbreakAPI.healthcare.getFacilities();
        const hospPayload = (hospRes?.data?.data ?? hospRes?.data) as HospitalData | HospitalResponseData | undefined;

        // Handle both single HospitalData and array responses
        const hospData = Array.isArray(hospPayload)
          ? (hospPayload[0] as unknown as HospitalResponseData)
          : (hospPayload as HospitalResponseData);

        const totalsAgg: FacilityTotals = {
          facilities: Number(hospData?.totals?.facilities ?? hospData?.facilities?.total ?? 0),
          avgBedCapacity: Number(hospData?.totals?.avgBedCapacity ?? hospData?.capacity?.beds ?? 0),
          bedsPer10k: Number(hospData?.totals?.bedsPer10k ?? 0),
        };
        const heatmap = hospData?.facilitiesGeo as GeoData | undefined;

        // Capacity trends require params
        const now = new Date();
        const endDate = now.toISOString();
        const start = new Date(now);
        start.setMonth(start.getMonth() - 6);
        const startDate = start.toISOString();
        const trendsRes = await outbreakAPI.healthcare.getCapacityTrends({
          region: region || "All",
          startDate,
          endDate,
        });
        const tPayload = (trendsRes?.data?.data ?? trendsRes?.data) as CapacityTrendsResponse | undefined;
        const rawTrends = tPayload?.trends ?? [];
        // Normalize dates and validate data
        const { normalizeDate, sortByDate } = await import("../utils/dateUtils");
        const trends: CapacityPoint[] = (Array.isArray(rawTrends) ? rawTrends : [])
          .map((d: any) => ({
            date: normalizeDate(d?.date || d?.name || endDate),
            bedsAvailable: typeof d?.bedsAvailable === "number" ? d.bedsAvailable : 0,
          }))
          .filter((d) => d.date); // Filter out invalid dates
        // Sort by date
        const sortedTrends = sortByDate(trends);

        if (mounted) {
          setTotals(totalsAgg);
          setFacilitiesGeo(heatmap);
          setCapacityTrends(sortedTrends);
        }
      } catch (e: unknown) {
        const errorMessage = e instanceof Error ? e.message : "Failed to load hospital data";
        if (mounted) setError(errorMessage);
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