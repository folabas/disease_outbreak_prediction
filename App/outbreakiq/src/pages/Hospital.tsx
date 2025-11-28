import { useEffect, useState } from "react";
import { MapContainer, TileLayer, CircleMarker, Popup } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import Loader from "../Components/Loader";
import { motion } from "framer-motion";
import { usePageAnimations } from "../hooks/usePageAnimations";
import { useHospitals } from "../hooks/useHospitals";
import { useDashboardStore } from "../store/useDashboardStore";
import { useOptions } from "../hooks/useOptions";

import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Cell,
  LineChart,
  Line,
} from "recharts";

<<<<<<< HEAD:App/outbreakiq/src/pages/Hospital.tsx
/* ---------- Mock data ---------- */
const allFacilities = [
  {
    name: "Lagos University Teaching Hospital",
    type: "Teaching Hospital",
    state: "Lagos",
    lga: "Surulere",
    beds: 761,
    staff: 1200,
    coordinates: [6.5149, 3.3676],
  },
  {
    name: "National Hospital Abuja",
    type: "General Hospital",
    state: "FCT",
    lga: "Central Business District",
    beds: 450,
    staff: 980,
    coordinates: [9.0578, 7.4951],
  },
  {
    name: "Kano General Clinic",
    type: "Primary Health Clinic",
    state: "Kano",
    lga: "Nassarawa",
    beds: 50,
    staff: 45,
    coordinates: [12.0022, 8.5919],
  },
  {
    name: "Ibadan Medical Laboratory",
    type: "Laboratory",
    state: "Oyo",
    lga: "Ibadan North",
    beds: 0,
    staff: 25,
    coordinates: [7.3878, 3.8964],
  },
  {
    name: "Port Harcourt Specialist Center",
    type: "Specialist Center",
    state: "Rivers",
    lga: "Obio/Akpor",
    beds: 300,
    staff: 600,
    coordinates: [4.8156, 7.0498],
  },
  
];
=======
/* ---------- Derived types ---------- */
type FacilityRow = {
  name: string;
  type: string;
  state: string;
  lga: string;
  beds: number | string;
  staff: number | string;
  coordinates: [number, number];
};
>>>>>>> linking-api-and-cleaning:web/outbreakiq/src/pages/Hospital.tsx

const typeColors: Record<string, string> = {
  "Teaching Hospital": "#1e3a8a",
  "General Hospital": "#2563eb",
  "Primary Health Clinic": "#3b82f6",
  Laboratory: "#10b981",
  "Specialist Center": "#f59e0b",
};

const trendData = [
  { year: 2020, facilities: 28000, beds: 70000 },
  { year: 2021, facilities: 30000, beds: 76000 },
  { year: 2022, facilities: 32000, beds: 82000 },
  { year: 2023, facilities: 34000, beds: 87000 },
  { year: 2024, facilities: 35500, beds: 91000 },
  { year: 2025, facilities: 36500, beds: 95000 },
  { year: 2026, facilities: 38000, beds: 99000 },
];

/* ---------- Component ---------- */
const Hospital = () => {
  const { region: globalRegion, setRegion: setGlobalRegion } = useDashboardStore();
  const [state, setState] = useState(globalRegion === "All" ? "All States" : globalRegion);
  const [facilityType, setFacilityType] = useState("All Types");
  const [metric, setMetric] = useState("Number of Beds");
  const [filteredData, setFilteredData] = useState<FacilityRow[]>([]);
  const [insight, setInsight] = useState("");
  const { totals, facilitiesGeo, capacityTrends, loading, error } = useHospitals(state === "All States" || state === "All" ? undefined : state);
  const { options } = useOptions({ source: "auto" });

  // Sync with global state
  useEffect(() => {
    const normalized = state === "All States" ? "All" : state;
    if (normalized !== globalRegion) {
      setGlobalRegion(normalized);
    }
  }, [state, globalRegion, setGlobalRegion]);

  useEffect(() => {
    const rows: FacilityRow[] = (((facilitiesGeo as any)?.features) || []).map((f: any) => {
      const props = f?.properties || {};
      const coords = f?.geometry?.coordinates || [];
      const [lon, lat] = Array.isArray(coords) && coords.length >= 2 ? [coords[0], coords[1]] : [0, 0];
      const hc = String(props?.healthcare || props?.amenity || "Hospital");
      const type = hc.charAt(0).toUpperCase() + hc.slice(1);
      return {
        name: String(props?.name || "Facility"),
        type,
        state: String(props?.region || "Unknown"),
        lga: String(props?.lga || props?.district || "-"),
        beds: props?.beds ?? "-",
        staff: props?.staff ?? "-",
        coordinates: [lat, lon],
      };
    });

    const norm = (s: string) => s.trim().toLowerCase();
    let filtered = rows;
    if (state !== "All States" && state !== "All") filtered = filtered.filter((f) => norm(f.state) === norm(state));
    if (facilityType !== "All Types") filtered = filtered.filter((f) => f.type === facilityType);
    setFilteredData(filtered);

    const regionText = state === "All States" || state === "All" ? "nationally" : `in ${state}`;
    const typeText = facilityType === "All Types" ? "across all facility types" : `focused on ${facilityType.toLowerCase()}s`;
    setInsight(`There are ${filtered.length} facilities ${regionText}, ${typeText}. ${filtered.length > 50 ? "High facility density in this selection." : "Facility density is limited in this selection."}`);
  }, [state, facilityType, facilitiesGeo]);

  if (loading) return <Loader />;

  // Calculate dynamic metrics
  const totalFacilities = filteredData.length;
  const totalBeds = filteredData.reduce((acc: number, curr: FacilityRow) => acc + (Number(curr.beds) || 0), 0);
  const totalStaff = filteredData.reduce((acc: number, curr: FacilityRow) => acc + (Number(curr.staff) || 0), 0);

  const avgBedCapacity = totalFacilities > 0 ? Math.round(totalBeds / totalFacilities) : 0;
  const staffToBedRatio = totalBeds > 0 ? (totalStaff / totalBeds).toFixed(1) : "0";

  // Calculate occupancy rate if capacity trends are available
  const latestTrend = capacityTrends && capacityTrends.length > 0 ? capacityTrends[capacityTrends.length - 1] : null;
  const availableBeds = latestTrend ? latestTrend.bedsAvailable : 0;
  const occupancyRate = (totalBeds > 0 && latestTrend)
    ? Math.round(((totalBeds - availableBeds) / totalBeds) * 100)
    : 74; // Fallback/Mock if no trend data

  const barColors = ["#1e3a8a", "#2563eb", "#3b82f6", "#60a5fa", "#93c5fd"];

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.45 }}
      className="min-h-screen bg-gray-50 p-6"
    >
      {/* Header */}
      <header className="mb-8">
        <h1 className="text-3xl font-bold text-[#0d2544]">
          Healthcare Capacity & Density
        </h1>
        <p className="text-gray-600 text-sm mt-1">
          Visualize healthcare capacity and facility density across Nigeria.
        </p>

        {/* Filters */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mt-4">
          <div className="flex flex-wrap gap-3">
            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-700">State:</span>
              <select
                value={state}
                onChange={(e) => setState(e.target.value)}
                className="border rounded-md px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option>All States</option>
                {(options?.regions || ["Lagos", "FCT", "Kano", "Oyo", "Rivers"]).filter((r) => r !== "All").map((r) => (
                  <option key={r}>{r}</option>
                ))}
              </select>
            </div>

            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-700">Facility Type:</span>
              <select
                value={facilityType}
                onChange={(e) => setFacilityType(e.target.value)}
                className="border rounded-md px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option>All Types</option>
                <option>Teaching Hospital</option>
                <option>General Hospital</option>
                <option>Primary Health Clinic</option>
                <option>Laboratory</option>
                <option>Specialist Center</option>
              </select>
            </div>

            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-700">Metric:</span>
              <select
                value={metric}
                onChange={(e) => setMetric(e.target.value)}
                className="border rounded-md px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option>Number of Beds</option>
                <option>Staff Count</option>
              </select>
            </div>
          </div>

          <button className="bg-green-700 text-white px-4 py-2 rounded-md text-sm font-semibold hover:bg-green-800 flex items-center gap-2 transition w-full sm:w-auto justify-center">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className="w-4 h-4"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth="2"
                d="M12 4v16m8-8H4"
              />
            </svg>
            Download Report
          </button>
        </div>
      </header>

      {/* Insight */}
      <div className="bg-blue-50 border-l-4 border-green-600 p-4 rounded-md mb-8 text-sm text-gray-700 shadow-sm">
        💡 <b>Insight:</b> {insight}
      </div>

      {/* Stats */}
      <SectionHeader title="Capacity Overview" />
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 mb-6">
        <StatCard title="Total Healthcare Facilities" value={totals ? String(totals.facilities) : String(totalFacilities)} />
        <StatCard title="Avg. Bed Capacity" value={String(avgBedCapacity)} />
        <StatCard title="Beds per 10k" value={totals ? String(totals.bedsPer10k) : "-"} />
        <StatCard title="Staff-to-Bed Ratio" value={`${staffToBedRatio}:1`} />
        <StatCard title="Facility Occupancy Rate" value={`${occupancyRate}%`} />
      </div>

      {/* Map + Charts */}
      <SectionHeader title="Geographical & Analytical Breakdown" />
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        {/* Map */}
        <div className="md:col-span-2 bg-white rounded-xl shadow p-6 flex flex-col">
          <h3 className="font-semibold text-[#0d2544] mb-3">
            Facility Distribution Map
          </h3>
          <div className="flex-1 rounded-lg overflow-hidden">
            <MapContainer
              center={[9.082, 8.6753]}
              zoom={6}
              scrollWheelZoom={false}
              className="h-[300px] w-full rounded"
            >
              <TileLayer
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                attribution="&copy; OpenStreetMap contributors"
              />
              {(((facilitiesGeo as any)?.features) || []).map((f: any, i: number) => {
                const coords = f?.geometry?.coordinates || [];
                const [lon, lat] = Array.isArray(coords) && coords.length >= 2 ? [coords[0], coords[1]] : [0, 0];
                const props = f?.properties || {};
                const label = props?.name || props?.region || "Facility";
                const ftype: string = String(props?.healthcare || props?.amenity || props?.type || "Facility");
                const beds = props?.capacity?.beds ?? props?.beds ?? "N/A";
                const staff = props?.capacity?.staff ?? props?.staff ?? "N/A";
                const color = typeColors[ftype] || "#2563eb";
                return (
                  <CircleMarker
                    key={i}
                    center={[lat, lon] as [number, number]}
                    radius={8}
                    fillOpacity={0.9}
                    stroke={false}
                    pathOptions={{ color, fillColor: color }}
                  >
                    <Popup className="text-sm">
                      <b>{label}</b>
                      <br />
                      {ftype}
                      <br />
                      Beds: {beds}
                      <br />
                      Staff: {staff}
                    </Popup>
                  </CircleMarker>
                );
              })}

            </MapContainer>
          </div>
        </div>

        {/* Bar Chart */}
        <div className="bg-white rounded-xl shadow p-6">
          <h3 className="font-semibold text-[#0d2544] mb-3">
            Facility Type Distribution
          </h3>
          <div className="w-full h-[300px]">
            <ResponsiveContainer>
              <BarChart
                data={(() => {
                  const counts: Record<string, number> = {};
                  (((facilitiesGeo as any)?.features) || []).forEach((f: any) => {
                    const t = String(f?.properties?.healthcare || f?.properties?.amenity || "Facility");
                    const type = t.charAt(0).toUpperCase() + t.slice(1);
                    counts[type] = (counts[type] || 0) + 1;
                  });
                  return Object.keys(counts).map((k) => ({ type: k, count: counts[k] }));
                })()}
                layout="vertical"
                margin={{ top: 10, right: 20, bottom: 10, left: 60 }}
              >
                <XAxis type="number" hide />
                <YAxis
                  dataKey="type"
                  type="category"
                  tick={{ fill: "#334155", fontSize: 13 }}
                  width={100}
                />
                <Tooltip />
                <Bar dataKey="count" radius={[6, 6, 6, 6]}>
                  {(() => {
                    const arr = (() => {
                      const counts: Record<string, number> = {};
                      (((facilitiesGeo as any)?.features) || []).forEach((f: any) => {
                        const t = String(f?.properties?.healthcare || f?.properties?.amenity || "Facility");
                        const type = t.charAt(0).toUpperCase() + t.slice(1);
                        counts[type] = (counts[type] || 0) + 1;
                      });
                      return Object.keys(counts).map((k) => ({ type: k, count: counts[k] }));
                    })();
                    return arr.map((_, i) => (
                      <Cell key={i} fill={barColors[i % barColors.length]} />
                    ));
                  })()}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Trend Chart */}
      <SectionHeader title="Healthcare Capacity Trends" />
      <div className="bg-white rounded-xl shadow p-6 mb-8">
        <h3 className="font-semibold text-[#0d2544] mb-3">
          Facility and Bed Growth (2020–2026)
        </h3>
        <ResponsiveContainer height={300}>
          <LineChart data={trendData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="year" />
            <YAxis />
            <Tooltip />
            <Line
              type="monotone"
              dataKey="facilities"
              stroke="#2563eb"
              strokeWidth={3}
            />
            <Line
              type="monotone"
              dataKey="beds"
              stroke="#10b981"
              strokeWidth={3}
              strokeDasharray="5 5"
            />
          </LineChart>
        </ResponsiveContainer>
        <p className="text-xs text-gray-500 mt-2 text-center">
          *Data from 2025 onwards is projected.
        </p>
      </div>

      {/* Facility Table */}
      <SectionHeader title="Facility Records" />
      <div className="bg-white rounded-xl shadow p-6 overflow-x-auto mb-8">
        <table className="min-w-full text-sm text-left text-gray-700">
          <thead className="bg-gray-100 text-gray-600">
            <tr>
              <th className="px-3 py-2">Facility Name</th>
              <th className="px-3 py-2">Type</th>
              <th className="px-3 py-2">State</th>
              <th className="px-3 py-2">LGA</th>
              <th className="px-3 py-2">Bed Capacity</th>
              <th className="px-3 py-2">Staff Count</th>
            </tr>
          </thead>
          <tbody>
            {filteredData.map((h, i) => (
              <tr key={i} className="border-t hover:bg-gray-50">
                <td className="px-3 py-3 font-medium">{h.name}</td>
                <td className="px-3 py-3">{h.type}</td>
                <td className="px-3 py-3">{h.state}</td>
                <td className="px-3 py-3">{h.lga}</td>
                <td className="px-3 py-3">{h.beds || "-"}</td>
                <td className="px-3 py-3">{h.staff}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Footer */}
      <footer className="pt-6 text-center text-gray-500 text-sm">
        © 2025 OutbreakIQ. All rights reserved.
      </footer>
    </motion.div>
  );
};

/* ---------- Reusable Components ---------- */
const StatCard = ({ title, value }: { title: string; value: string }) => (
  <div className="bg-white rounded-xl shadow p-4 flex flex-col justify-between hover:shadow-md transition">
    <p className="text-sm text-gray-500">{title}</p>
    <h3 className="text-2xl font-bold text-gray-800 mt-1">{value}</h3>
  </div>
);

const SectionHeader = ({ title }: { title: string }) => (
  <h2 className="text-lg font-semibold text-[#0d2544] mb-3 mt-6 border-l-4 border-green-600 pl-3">
    {title}
  </h2>
);

export default Hospital;
