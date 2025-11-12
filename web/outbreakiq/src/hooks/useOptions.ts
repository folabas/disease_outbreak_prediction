import { useEffect, useState } from "react";
import { outbreakAPI } from "../services/api";

type Options = {
  diseases: string[];
  regions: string[];
  years: (number | string)[];
  source?: string;
};

export function useOptions(params?: { source?: "auto" | "training" | "weather" | "predictions"; disease?: string }) {
  const [options, setOptions] = useState<Options>({ diseases: [], regions: [], years: [] });
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | undefined>(undefined);

  useEffect(() => {
    let mounted = true;
    async function run() {
      try {
        setLoading(true);
        setError(undefined);
        const res = await outbreakAPI.metadata.getOptions({ source: params?.source || "auto", disease: params?.disease });
        const body = res?.data || {};
        const data = body?.data || body; // support both envelope and plain
        const diseases = Array.isArray(data?.diseases) ? data.diseases : [];
        const regions = Array.isArray(data?.regions) ? data.regions : [];
        const years = Array.isArray(data?.years) ? data.years : [];
        if (mounted) setOptions({ diseases, regions, years, source: body?.source || body?.data?.source });
      } catch (e: any) {
        if (mounted) setError(e?.message || "Failed to load options");
      } finally {
        if (mounted) setLoading(false);
      }
    }
    void run();
    return () => {
      mounted = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [params?.source, params?.disease]);

  return { options, loading, error } as const;
}