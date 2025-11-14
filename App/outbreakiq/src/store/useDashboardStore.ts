import { create } from "zustand";

type DashboardState = {
  region: string;
  setRegion: (r: string) => void;
};

export const useDashboardStore = create<DashboardState>((set) => ({
  region: "All",
  setRegion: (r: string) => set({ region: r }),
}));
