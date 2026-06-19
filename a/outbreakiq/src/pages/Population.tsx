import { useEffect, useState, useRef } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
  LineChart,
  Line,
  CartesianGrid,
} from "recharts";
import Loader from "../Components/Loader";
import { MapContainer, TileLayer, GeoJSON, useMap } from "react-leaflet";
import L, { Map as LeafletMap, Layer } from "leaflet";
import type { Feature, Geometry } from "geojson";
import { motion } from "framer-motion";
import "leaflet/dist/leaflet.css";
import { usePageAnimations } from "../hooks/usePageAnimations";
import { usePopulation } from "../hooks/usePopulation";
import { useOptions } from "../hooks/useOptions";
import { useDashboardStore } from "../store/useDashboardStore";
import { exportToCSV, formatDateForFilename } from "../utils/exportUtils";

type GrowthEntry = { region: string; value: number };

const trendData = [
  { year: 2020, population: 200 },
  { year: 2021, population: 206 },
  { year: 2022, population: 210 },
  { year: 2023, population: 213 },
  { year: 2024, population: 218 },
  { year: 2025, population: 223 },
  { year: 2026, population: 229 }, // forecast
];

const Population = () => {
  const { region: globalRegion, setRegion: setGlobalRegion } = useDashboardStore();
  // Filters
  const [region, setRegion] = useState(globalRegion === "All" ? "All Nigeria" : globalRegion);
  const [dateRange, setDateRange] = useState("Last 12 Months");

  // Sync with global state
  useEffect(() => {
    const normalized = region === "All Nigeria" ? "All" : region;
    if (normalized !== globalRegion) {
      setGlobalRegion(normalized);
    }
  }, [region, globalRegion, setGlobalRegion]);
  const [growthData, setGrowthData] = useState<GrowthEntry[]>([]);
  const [geoData, setGeoData] = useState<any>(null);
  const [densityColors, setDensityColors] = useState<Record<string, string>>({});
  const [stats, setStats] = useState({
    total: "—",
    density: "0/km²",
    growthRegion: "",
  });
  const mapRef = useRef<LeafletMap | null>(null);

  // Hook: population aggregates and density map
  function toWeekString(d: Date): string {
    const dt = new Date(Date.UTC(d.getFullYear(), d.getMonth(), d.getDate()));
    const dayNum = dt.getUTCDay() || 7;
    dt.setUTCDate(dt.getUTCDate() + 4 - dayNum);
    const yearStart = new Date(Date.UTC(dt.getUTCFullYear(), 0, 1));
    const weekNo = Math.ceil(((dt.getTime() - yearStart.getTime()) / 86400000 + 1) / 7);
    const y = dt.getUTCFullYear();
    return `${y}-W${String(weekNo).padStart(2, "0")}`;
  }
  const months = dateRange === "Last 6 Months" ? 6 : dateRange === "Last 12 Months" ? 12 : 24;
  const now = new Date();
  const start = new Date(now);
  start.setMonth(start.getMonth() - months);
  const startStr = toWeekString(start);
  const endStr = toWeekString(now);

  const { growthData: gSeries, densityData: dSeries, densityMap, stats: pStats, totalPopulation: popTotal, loading, error } = usePopulation(region, { startDate: startStr, endDate: endStr });
  const { options } = useOptions({ source: "auto" });

  // Set geo data from hook
  useEffect(() => {
    if (densityMap) setGeoData(densityMap as any);
  }, [densityMap]);

  // Update local series/colors/stats when hook data changes
  useEffect(() => {
    // Growth series for bar chart - validate data structure
    const validatedGrowth = (gSeries || [])
      .map((item: any) => ({
        region: String(item?.region || item?.name || ""),
        value: typeof item?.value === "number" ? item.value : 0,
      }))
      .filter((item) => item.region); // Filter out invalid entries
    setGrowthData(validatedGrowth);

    // Stats from hook
    setStats((prev) => ({
      ...prev,
      total: popTotal !== null && popTotal > 0 ? popTotal.toLocaleString() : "—",
      density: `${(pStats?.avgDensity ?? 0).toFixed(2)}/km²`,
      growthRegion: pStats?.topGrowthRegion ? `${pStats.topGrowthRegion}` : prev.growthRegion,
    }));

    // Build density color mapping from density series
    const colors = (dSeries || []).reduce((acc: Record<string, string>, d: any) => {
      const region = String(d?.region || d?.name || "").toLowerCase();
      const v = typeof d?.value === "number" ? d.value : 0;
      const shade = v > 400 ? "#1e3a8a" : v > 300 ? "#2563eb" : v > 200 ? "#60a5fa" : "#bfdbfe";
      if (region) {
        acc[region] = shade;
      }
      return acc;
    }, {} as Record<string, string>);
    setDensityColors(colors);
  }, [gSeries, dSeries, pStats, popTotal]);

  // Remove placeholder totals; await backend totals when available.

  // Map region focus
  type MapZoomProps = { region: string };
  const MapZoomHandler = ({ region }: MapZoomProps) => {
    const map = useMap();
    useEffect(() => {
      if (!geoData) return;
      if (["All Regions", "All Nigeria"].includes(region)) {
        map.setView([9.082, 8.6753], 6);
        return;
      }

      // Filter the region (try canonical `region` field; fallback to `NAME_1`)
      const layer = L.geoJSON(geoData as any, {
        filter: (f: any) => {
          const r = (f.properties?.region || f.properties?.NAME_1 || "").toLowerCase();
          return r.includes(region.toLowerCase());
        },
      });
      const bounds = layer.getBounds();
      if (bounds.isValid()) map.fitBounds(bounds, { padding: [30, 30] });
    }, [region, geoData]);
    return null;
  };

  if (loading) return <Loader />;

  const barColors = [
    "#1e3a8a",
    "#2563eb",
    "#3b82f6",
    "#60a5fa",
    "#93c5fd",
    "#bfdbfe",
  ];

  const onEachFeature = (feature: Feature<Geometry, any>, layer: Layer) => {
    const label = (feature.properties?.region || feature.properties?.NAME_1 || "").toLowerCase();
    const color = densityColors[label] || "#93c5fd";
    if ((layer as any)?.setStyle) {
      (layer as any).setStyle({
        fillColor: color,
        fillOpacity: 0.8,
        color: "#fff",
        weight: 1,
      });
    }
    (layer as any).bindTooltip(
      `${feature.properties?.NAME_1 || feature.properties?.region}<br/>Density: ${feature.properties?.density ?? "n/a"
      }`,
      { direction: "center", sticky: true }
    );
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.6 }}
      className="min-h-screen bg-gray-50 p-6"
    >
      {/* Header */}
      <header className="mb-8">
        <h1 className="text-3xl font-bold text-[#0d2544]">
          Population Analytics
        </h1>
        <p className="text-gray-600 text-sm mt-1">
          Analyze population growth, density, and demographic patterns across Nigeria.
        </p>

        {/* Filters */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mt-4">
          <div className="flex flex-wrap gap-3">
            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-700">Date Range:</span>
              <select
                value={dateRange}
                onChange={(e) => setDateRange(e.target.value)}
                className="border rounded-md px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option>Last 6 Months</option>
                <option>Last 12 Months</option>
                <option>Last 24 Months</option>
              </select>
            </div>

            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-700">Region:</span>
              <select
                value={region}
                onChange={(e) => setRegion(e.target.value)}
                className="border rounded-md px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option>All Nigeria</option>
                {(options?.regions || []).map((r) => {
                  if (r === "All") return null;
                  return <option key={r}>{r}</option>;
                })}
              </select>
            </div>
          </div>

          <div className="flex gap-2 w-full sm:w-auto justify-end">
            <button
              onClick={() => {
                const exportData = [
                  ...growthData.map((d: GrowthEntry) => ({ region: d.region, metric: "Growth Rate", value: d.value })),
                  ...dSeries.map((d: GrowthEntry) => ({ region: d.region, metric: "Density", value: d.value })),
                ];
                exportToCSV(exportData, `population_${region}_${formatDateForFilename()}.csv`);
              }}
              className="bg-white border text-gray-700 px-4 py-2 rounded-md text-sm font-semibold hover:bg-gray-100 flex items-center gap-2 transition"
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4v16m8-8H4" />
              </svg>
              Export
            </button>
          </div>
        </div>
      </header>

      {/* Removed AI Insight to avoid hardcoded content */}

      {/* Stats Overview */}
      <SectionHeader title="Population Overview" />
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 mb-6">
        <StatCard title="Total Population" value={stats.total} />
        <StatCard title="Average Density" value={stats.density} />
        <StatCard title="Highest Growth Region" value={stats.growthRegion} />
        <StatCard title="Urban Population" value="52%" />
        <StatCard title="Rural Population" value="48%" />
        <StatCard title="Gender Ratio (M/F)" value="49% / 51%" />
      </div>

      {/* Charts */}
      <SectionHeader title="Population Analysis" />
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        {/* Heatmap — larger */}
        <div className="md:col-span-2 bg-white rounded-2xl shadow-xl border border-gray-100 p-6 flex flex-col">
          <h3 className="font-semibold text-[#0d2544] mb-3">Population Density Heatmap</h3>
          <div className="flex-1 rounded-lg overflow-hidden">
            <MapContainer
              center={[9.082, 8.6753]}
              zoom={6}
              scrollWheelZoom={false}
              className="h-[300px] w-full rounded"
              ref={mapRef}
            >
              <TileLayer
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"

              />
              {geoData && <GeoJSON data={geoData} onEachFeature={onEachFeature} />}
              <MapZoomHandler region={region} />
            </MapContainer>
          </div>
          <div className="mt-3 flex justify-between text-xs text-gray-600">
            <span>Low Density</span>
            <div className="w-32 h-2 bg-gradient-to-r from-gray-200 via-blue-400 to-blue-700 rounded-full" />
            <span>High Density</span>
          </div>
        </div>

        {/* Bar Chart */}
        <div className="bg-white rounded-2xl shadow-xl border border-gray-100 p-6">
          <h3 className="font-semibold text-[#0d2544] mb-3">Population Growth by Region</h3>
          <div className="w-full h-[300px]">
            <ResponsiveContainer>
              <BarChart
                data={growthData}
                layout="vertical"
                margin={{ top: 10, right: 20, bottom: 10, left: 60 }}
              >
                <XAxis type="number" hide />
                <YAxis dataKey="region" type="category" tick={{ fill: "#334155", fontSize: 13 }} width={100} />
                <Tooltip />
                <Bar dataKey="value" radius={[6, 6, 6, 6]}>
                  {growthData.map((_, i) => (
                    <Cell key={i} fill={barColors[i % barColors.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Trend Chart */}
      <SectionHeader title="Historical & Forecast Trends" />
      <div className="bg-white rounded-2xl shadow-xl border border-gray-100 p-6 mb-8">
        <h3 className="font-semibold text-[#0d2544] mb-3">
          Total Population Over Time
        </h3>
        <ResponsiveContainer height={300}>
          <LineChart data={trendData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="year" />
            <YAxis />
            <Tooltip />
            <Line
              type="monotone"
              dataKey="population"
              stroke="#2563eb"
              strokeWidth={3}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Density Map Legend */}
      <SectionHeader title="Population Density Legend" />
      <div className="bg-white rounded-2xl shadow-xl border border-gray-100 p-6 mb-8">
        <div className="flex items-center gap-4 text-sm">
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-[#bfdbfe] border border-gray-300"></div>
            <span>&lt; 200/km²</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-[#60a5fa] border border-gray-300"></div>
            <span>200-300/km²</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-[#2563eb] border border-gray-300"></div>
            <span>300-400/km²</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-[#1e3a8a] border border-gray-300"></div>
            <span>&gt; 400/km²</span>
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="pt-6 pb-6 flex flex-col items-center gap-2 text-gray-500 text-sm">
        <p>© {new Date().getFullYear()} OutbreakIQ. All rights reserved.</p>
        <p className="text-gray-400 text-xs font-medium">
          Sponsored by <span className="text-[#0d2544] font-bold">Waltik Labs</span>
        </p>
      </footer>
    </motion.div>
  );
};

/* 🔸 Reusable Components */
type StatCardProps = { title: string; value: string };
const StatCard = ({ title, value }: StatCardProps) => (
  <div className="bg-white rounded-2xl shadow-xl border border-gray-100 p-4 flex flex-col justify-between hover:shadow-md transition">
    <p className="text-sm text-gray-500">{title}</p>
    <h3 className="text-2xl font-bold text-gray-800 mt-1">{value}</h3>
  </div>
);

type SectionHeaderProps = { title: string };
const SectionHeader = ({ title }: SectionHeaderProps) => (
  <h2 className="text-lg font-semibold text-[#0d2544] mb-3 mt-6 border-l-4 border-green-600 pl-3">
    {title}
  </h2>
);

export default Population;
