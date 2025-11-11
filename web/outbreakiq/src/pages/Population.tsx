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
import { motion } from "framer-motion";
import "leaflet/dist/leaflet.css";

const regions = [
  "North West",
  "South West",
  "North Central",
  "South South",
  "North East",
  "South East",
];

const regionalGrowth = {
  "All Regions": [4.2, 3.8, 3.1, 2.8, 2.4, 2.1],
  North: [4.5, 3.9, 3.2, 2.8, 2.6, 2.0],
  South: [3.8, 3.6, 3.2, 3.0, 2.5, 2.3],
  East: [2.5, 2.4, 2.3, 2.1, 2.0, 1.9],
  West: [3.9, 3.5, 3.0, 2.9, 2.8, 2.6],
};

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
  const [loading, setLoading] = useState(true);
  const [region, setRegion] = useState("All Regions");
  const [dateRange, setDateRange] = useState("Last 12 Months");
  const [growthData, setGrowthData] = useState([]);
  const [geoData, setGeoData] = useState(null);
  const [densityColors, setDensityColors] = useState({});
  const [stats, setStats] = useState({
    total: "213,401,323",
    density: "231/km²",
    growthRegion: "Kano (+4.2%)",
  });
  const mapRef = useRef();

  // Fetch GeoJSON map data
  useEffect(() => {
    fetch("/nigeria-level1.geojson")
      .then((res) => res.json())
      .then((data) => setGeoData(data))
      .catch((err) => console.error("Error loading map:", err));
  }, []);

  // Page loading simulation
  useEffect(() => {
    const t = setTimeout(() => setLoading(false), 1200);
    return () => clearTimeout(t);
  }, []);

  // Update stats and chart when filters change
  useEffect(() => {
    const growthValues =
      regionalGrowth[region] || regionalGrowth["All Regions"];
    const updatedData = regions.map((r, i) => ({
      region: r,
      value: growthValues[i] + (Math.random() * 0.5 - 0.2),
    }));

    const topRegion = updatedData.sort((a, b) => b.value - a.value)[0];
    setGrowthData(updatedData);

    // Update stats
    setStats({
      total:
        dateRange === "Last 6 Months"
          ? "210,500,000"
          : dateRange === "Last 12 Months"
          ? "213,401,323"
          : "215,800,000",
      density:
        region === "North"
          ? "189/km²"
          : region === "South"
          ? "298/km²"
          : "231/km²",
      growthRegion: `${topRegion.region} (+${topRegion.value.toFixed(1)}%)`,
    });

    // Dynamic color intensity by growth value
    const densityLevels = regions.reduce((acc, reg, idx) => {
      const val = growthValues[idx];
      const shade =
        val > 4
          ? "#1e3a8a"
          : val > 3.5
          ? "#2563eb"
          : val > 3
          ? "#60a5fa"
          : "#bfdbfe";
      acc[reg.toLowerCase()] = shade;
      return acc;
    }, {});
    setDensityColors(densityLevels);
  }, [region, dateRange]);

  // Map region focus
  const MapZoomHandler = ({ region }) => {
    const map = useMap();
    useEffect(() => {
      if (!geoData) return;
      if (region === "All Regions") {
        map.setView([9.082, 8.6753], 6);
        return;
      }

      // Filter the region
      const layer = L.geoJSON(geoData, {
        filter: (f) => f.properties?.NAME_1?.toLowerCase().includes(region.toLowerCase()),
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

  const onEachFeature = (feature, layer) => {
    const name = feature.properties?.NAME_1?.toLowerCase();
    const color = densityColors[name] || "#93c5fd";
    layer.setStyle({
      fillColor: color,
      fillOpacity: 0.8,
      color: "#fff",
      weight: 1,
    });
    layer.bindTooltip(
      `${feature.properties.NAME_1}<br/>Population Growth: ${(Math.random() * 5 + 2).toFixed(1)}%`,
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
                <option>All Regions</option>
                <option>North</option>
                <option>South</option>
                <option>East</option>
                <option>West</option>
              </select>
            </div>
          </div>

          <div className="flex gap-2 w-full sm:w-auto justify-end">
            <button className="bg-white border text-gray-700 px-4 py-2 rounded-md text-sm font-semibold hover:bg-gray-100 flex items-center gap-2 transition">
              <svg xmlns="http://www.w3.org/2000/svg" className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4v16m8-8H4" />
              </svg>
              Export
            </button>

            <button className="bg-green-600 text-white px-4 py-2 rounded-md text-sm font-semibold hover:bg-green-700 flex items-center gap-2 transition">
              <svg xmlns="http://www.w3.org/2000/svg" className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 4a1 1 0 011-1h16a1 1 0 011 1v3H3V4zm0 5h18v11a1 1 0 01-1 1H4a1 1 0 01-1-1V9z" />
              </svg>
              Apply Filters
            </button>
          </div>
        </div>
      </header>

      {/* AI Insight */}
      <div className="bg-blue-50 border-l-4 border-green-600 p-4 rounded-md mb-8 text-sm text-gray-700 shadow-sm">
        💡 <b>Insight:</b> Northern regions continue to record the highest growth (4.2%) with increasing urban migration, 
        while southern regions show stabilized density due to improved infrastructure.
      </div>

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
        <div className="md:col-span-2 bg-white rounded-xl shadow p-6 flex flex-col">
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
        <div className="bg-white rounded-xl shadow p-6">
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
      <div className="bg-white rounded-xl shadow p-6 mb-8">
        <h3 className="font-semibold text-[#0d2544] mb-3">
          Total Population Over Time
        </h3>
        <ResponsiveContainer height={300}>
          <LineChart data={trendData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="year" />
            <YAxis />
            <Tooltip />
            <Line type="monotone" dataKey="population" stroke="#2563eb" strokeWidth={3} />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Footer */}
      <footer className="pt-6 text-center text-gray-500 text-sm">
        © 2025 OutbreakIQ. All rights reserved.
      </footer>
    </motion.div>
  );
};

/* 🔸 Reusable Components */
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

export default Population;
