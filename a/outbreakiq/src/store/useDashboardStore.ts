import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { Disease } from "../services/types";

// Valid disease list matching backend ALLOWED_DISEASES
const ALLOWED_DISEASES: Disease[] = ["cholera", "malaria", "ebola", "covid"];

function validateDisease(d: string): Disease {
  const normalized = d.toLowerCase();
  if (ALLOWED_DISEASES.includes(normalized as Disease)) {
    return normalized as Disease;
  }
  return "cholera"; // Default fallback
}

function normalizeRegion(r: string): string {
  const normalized = r.trim();
  // Normalize common variations
  if (["All Nigeria", "All Regions", "all", "All"].includes(normalized)) {
    return "All";
  }
  return normalized;
}

type DashboardState = {
  region: string;
  disease: Disease;
  setRegion: (r: string) => void;
  setDisease: (d: Disease) => void;
  syncFromUrl: () => void;
  syncToUrl: () => void;
};

export const useDashboardStore = create<DashboardState>()(
  persist(
    (set, get) => {
      // Initialize from URL params if available
      const initFromUrl = () => {
        if (typeof window !== "undefined") {
          const params = new URLSearchParams(window.location.search);
          const urlDisease = params.get("disease");
          const urlRegion = params.get("region");
          
          if (urlDisease) {
            const validated = validateDisease(urlDisease);
            set({ disease: validated });
          }
          if (urlRegion) {
            const normalized = normalizeRegion(urlRegion);
            set({ region: normalized });
          }
        }
      };

      // Initialize on store creation
      initFromUrl();

      return {
        region: "All",
        disease: "cholera",
        setRegion: (r: string) => {
          const normalized = normalizeRegion(r);
          set({ region: normalized });
          // Only sync to URL if we're on a route that uses filters (not on home page)
          if (typeof window !== "undefined" && window.location.pathname !== "/") {
            const params = new URLSearchParams(window.location.search);
            params.set("region", normalized);
            window.history.replaceState({}, "", `${window.location.pathname}?${params.toString()}`);
          }
        },
        setDisease: (d: Disease) => {
          const validated = validateDisease(d);
          set({ disease: validated });
          // Only sync to URL if we're on a route that uses filters (not on home page)
          if (typeof window !== "undefined" && window.location.pathname !== "/") {
            const params = new URLSearchParams(window.location.search);
            params.set("disease", validated);
            window.history.replaceState({}, "", `${window.location.pathname}?${params.toString()}`);
          }
        },
        syncFromUrl: () => {
          initFromUrl();
        },
        syncToUrl: () => {
          // Only sync to URL if we're on a route that uses filters (not on home page)
          const state = get();
          if (typeof window !== "undefined" && window.location.pathname !== "/") {
            const params = new URLSearchParams(window.location.search);
            params.set("disease", state.disease);
            params.set("region", state.region);
            window.history.replaceState({}, "", `${window.location.pathname}?${params.toString()}`);
          }
        },
      };
    },
    {
      name: "outbreak-dashboard-storage",
      partialize: (state) => ({ disease: state.disease, region: state.region }),
    }
  )
);
