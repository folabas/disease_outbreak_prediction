import { useEffect, useState } from "react";
import { outbreakAPI } from "../services/api";

type FreshnessInfo = {
  last_modified?: string;
  age_days?: number;
  is_fresh?: boolean;
  version?: number;
};

type Options = {
  diseases: string[];
  regions: string[];
  years: (number | string)[];
  source?: string;
  status?: string;
  freshness?: FreshnessInfo | null;
};

type OptionsParams = {
  source?: "auto" | "training" | "live";
  disease?: string;
};

export function useOptions(params?: OptionsParams, trigger?: number) {
  const [options, setOptions] = useState<Options>({ diseases: [], regions: [], years: [] });
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | undefined>(undefined);

  useEffect(() => {
    let mounted = true;

    async function run() {
      try {
        setLoading(true);
        setError(undefined);

        const res = await outbreakAPI.metadata.getOptions({
          source: (params?.source ?? "auto") as any,
          disease: params?.disease,
        });

        const body = res?.data ?? {};
        const payload = body?.data ?? body;

        const diseases = Array.isArray(payload?.diseases) ? payload.diseases : [];
        const regions = Array.isArray(payload?.regions) ? payload.regions : [];
        const years = Array.isArray(payload?.years) ? payload.years : [];

        if (mounted) {
          setOptions({
            diseases,
            regions,
            years,
            source: payload?.source ?? params?.source ?? "auto",
            status: body?.status ?? payload?.status,
            freshness: payload?.freshness ?? null,
          });
        }
      } catch (e: any) {
        if (mounted) {
          setError(e?.message || "Failed to load options");
        }
      } finally {
        if (mounted) {
          setLoading(false);
        }
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