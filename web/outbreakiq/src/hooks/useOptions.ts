import { useEffect, useState } from "react";
import { outbreakAPI } from "../services/api";

type Options = {
  diseases: string[];
  regions: string[];
  years: (number | string)[];
  source?: string;
};

export function useOptions(params?: { source?: "auto" | "training" | "weather" | "predictions"; disease?: string }, trigger?: number) {
  const [options, setOptions] = useState<Options>({ diseases: [], regions: [], years: [] });
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | undefined>(undefined);

  useEffect(() => {
    let mounted = true;
    async function run() {
      try {
        setLoading(true);
        setError(undefined);
        const results = await Promise.allSettled([
          outbreakAPI.metadata.getOptions({ source: params?.source || "auto", disease: params?.disease }),
          outbreakAPI.metadata.getDiseases(),
          outbreakAPI.metadata.getRegions(),
        ]);

        const optRes = results[0].status === "fulfilled" ? results[0].value : undefined;
        const disRes = results[1].status === "fulfilled" ? results[1].value : undefined;
        const regRes = results[2].status === "fulfilled" ? results[2].value : undefined;

        const optBody = optRes?.data || {};
        const optData = optBody?.data || optBody;
        const optDiseases = Array.isArray(optData?.diseases) ? optData.diseases : [];
        const optRegions = Array.isArray(optData?.regions) ? optData.regions : [];
        const optYears = Array.isArray(optData?.years) ? optData.years : [];

        const disData = Array.isArray(disRes?.data?.data) ? disRes.data.data : [];
        const regData = Array.isArray(regRes?.data?.data) ? regRes.data.data : [];

        const diseases = disData.length ? disData : optDiseases;
        const regions = regData.length ? regData : optRegions;
        const years = optYears;

        if (mounted) setOptions({ diseases, regions, years, source: optBody?.source || optBody?.data?.source });
      } catch (e: any) {
        if (mounted) setError(e?.message || "Failed to load options");
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
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [params?.source, params?.disease, trigger]);

  return { options, loading, error } as const;
}