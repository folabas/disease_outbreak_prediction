import { useEffect, useState } from "react";
import { MapContainer, TileLayer, CircleMarker, Popup } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import Loader from "../Components/Loader";
import { motion } from "framer-motion";
import { usePageAnimations } from "../hooks/usePageAnimations";

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

const facilityTypes = [
  { type: "Teaching Hospital", count: 340 },
  { type: "General Hospital", count: 520 },
  { type: "Primary Health Clinic", count: 680 },
  { type: "Laboratory", count: 240 },
  { type: "Specialist Center", count: 180 },
];

const trendData = [
  { year: 2020, facilities: 28000, beds: 70000 },
  { year: 2021, facilities: 30000, beds: 76000 },
  { year: 2022, facilities: 32000, beds: 82000 },
  { year: 2023, facilities: 34000, beds: 87000 },
  { year: 2024, facilities: 35500, beds: 91000 },
  { year: 2025, facilities: 36500, beds: 95000 },
  { year: 2026, facilities: 38000, beds: 99000 },
];

const typeColors = {
  "Teaching Hospital": "#1e3a8a",
  "General Hospital": "#2563eb",
  "Primary Health Clinic": "#3b82f6",
  Laboratory: "#10b981",
  "Specialist Center": "#f59e0b",
};

/* ---------- Component ---------- */
const Hospital = () => {
  const [loading, setLoading] = useState(true);
  const [state, setState] = useState("All States");
  const [facilityType, setFacilityType] = useState("All Types");
  const [metric, setMetric] = useState("Number of Beds");
  const [filteredData, setFilteredData] = useState(allFacilities);
  const [insight, setInsight] = useState("");

  useEffect(() => {
    const timer = setTimeout(() => setLoading(false), 900);
    return () => clearTimeout(timer);
  }, []);

  useEffect(() => {
    let filtered = [...allFacilities];
    if (state !== "All States")
      filtered = filtered.filter((f) => f.state === state);
    if (facilityType !== "All Types")
      filtered = filtered.filter((f) => f.type === facilityType);
    setFilteredData(filtered);

    const regionText = state === "All States" ? "nationally" : `in ${state}`;
    const typeText =
      facilityType === "All Types"
        ? "across all facility types"
        : `focused on ${facilityType.toLowerCase()}s`;

    setInsight(
      `There are ${filtered.length} facilities ${regionText}, ${typeText}. ${
        filtered.length > 3
          ? "Major states show capacity expansion with steady bed growth."
          : "Facility density is limited in this selection; consider targeted investments."
      }`
    );
  }, [state, facilityType]);

  if (loading) return <Loader />;

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
                <option>Lagos</option>
                <option>FCT</option>
                <option>Kano</option>
                <option>Oyo</option>
                <option>Rivers</option>
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
        <StatCard title="Total Healthcare Facilities" value="34,592" />
        <StatCard title="Total Hospital Beds" value="87,104" />
        <StatCard title="Avg. Facilities per 100k Pop." value="16.2" />
        <StatCard title="Avg. Bed Capacity" value="82" />
        <StatCard title="Staff-to-Bed Ratio" value="1.6:1" />
        <StatCard title="Facility Occupancy Rate" value="74%" />
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
              {filteredData.map((h, i) => (
                <CircleMarker
                  key={i}
                  center={h.coordinates}
                  radius={8}
                  fillOpacity={0.9}
                  stroke={false}
                  pathOptions={{
                    color: typeColors[h.type] || "#2563eb",
                    fillColor: typeColors[h.type] || "#2563eb",
                  }}
                >
                  <Popup className="text-sm">
                    <b>{h.name}</b>
                    <br />
                    {h.type}
                    <br />
                    Beds: {h.beds || "N/A"}
                    <br />
                    Staff: {h.staff}
                  </Popup>
                </CircleMarker>
              ))}
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
                data={facilityTypes}
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
                  {facilityTypes.map((_, i) => (
                    <Cell key={i} fill={barColors[i % barColors.length]} />
                  ))}
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
const StatCard = ({ title, value }) => (
  <div className="bg-white rounded-xl shadow p-4 flex flex-col justify-between hover:shadow-md transition">
    <p className="text-sm text-gray-500">{title}</p>
    <h3 className="text-2xl font-bold text-gray-800 mt-1">{value}</h3>
  </div>
);

const SectionHeader = ({ title }) => (
  <h2 className="text-lg font-semibold text-[#0d2544] mb-3 mt-6 border-l-4 border-green-600 pl-3">
    {title}
  </h2>
);

export default Hospital;
