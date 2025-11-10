import { useState, useEffect } from "react";
import DataPageTemplate from "../Components/DataPageTemplate";
import Loader from "../Components/Loader";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ResponsiveContainer,
  AreaChart,
  Area,
} from "recharts";

const generateMockData = (days, tempBase, rainBase) =>
  Array.from({ length: days }, (_, i) => ({
    name: `Day ${i + 1}`,
    temp: Math.round(tempBase + Math.random() * 4 - 2),
    rain: Math.round(rainBase * Math.random() * 2 * 10) / 10,
  }));

const Climate = () => {
  const [loading, setLoading] = useState(true);
  const [region, setRegion] = useState("All Nigeria");
  const [dateRange, setDateRange] = useState("Last 30 Days");
  const [tempData, setTempData] = useState([]);
  const [rainData, setRainData] = useState([]);
  const [stats, setStats] = useState([]);

  useEffect(() => {
    const timer = setTimeout(() => setLoading(false), 1200);
    return () => clearTimeout(timer);
  }, []);

  useEffect(() => {
    const days =
      dateRange === "Last 7 Days" ? 7 : dateRange === "Last 30 Days" ? 30 : 90;

    const regionBaseline = {
      "All Nigeria": { temp: 32, rain: 4 },
      "North-East": { temp: 34, rain: 2 },
      "South-West": { temp: 30, rain: 6 },
      "North-Central": { temp: 31, rain: 5 },
    };

    const base = regionBaseline[region];
    const tempMock = generateMockData(days, base.temp, base.rain);
    const rainMock = generateMockData(days, base.temp, base.rain);

    setTempData(tempMock);
    setRainData(rainMock);

    setStats([
      {
        name: `Average Temperature (${days}d)`,
        value: `${base.temp.toFixed(1)}°C`,
        change: "+1.2%",
        positive: true,
      },
      {
        name: `Total Rainfall (${days}d)`,
        value: `${(base.rain * days).toFixed(1)} mm`,
        change: "-5.8%",
        positive: false,
      },
      {
        name: "Highest Temp Peak",
        value: `${(base.temp + 6).toFixed(1)}°C`,
        change: "+0.5%",
        positive: true,
      },
      {
        name: "Heaviest Rainfall Day",
        value: `${(base.rain * 4.5).toFixed(1)} mm`,
        change: "+12.1%",
        positive: true,
      },
    ]);
  }, [region, dateRange]);

  const filters = (
    <div className="flex flex-wrap gap-3 items-center">
      <select
        title="region"
        value={region}
        onChange={(e) => setRegion(e.target.value)}
        className="border rounded-md px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
      >
        <option>All Nigeria</option>
        <option>North-East</option>
        <option>South-West</option>
        <option>North-Central</option>
      </select>

      <select
        title="dateRange"
        value={dateRange}
        onChange={(e) => setDateRange(e.target.value)}
        className="border rounded-md px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
      >
        <option>Last 7 Days</option>
        <option>Last 30 Days</option>
        <option>Last 90 Days</option>
      </select>

      <button className="ml-auto bg-green-600 text-white px-4 py-2 rounded-md text-sm font-semibold hover:bg-green-700 flex items-center gap-2 transition">
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
        Export Data
      </button>
    </div>
  );

  if (loading) return <Loader />;

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      {/* Header Section (same style as Prediction) */}
      <header className="mb-8">
        <h1 className="text-3xl font-bold text-[#0d2544]">Climate Trends</h1>
        <p className="text-gray-600 text-sm mt-1">
          Analyze regional temperature and rainfall patterns across Nigeria.
        </p>
        <div className="mt-4">{filters}</div>
      </header>

      {/* Climate Overview */}
      <SectionHeader title="Climate Overview" />
      <div className="grid grid-cols-2 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {stats.map((stat) => (
          <div
            key={stat.name}
            className="bg-white rounded-xl shadow p-4 flex flex-col justify-between hover:shadow-md transition"
          >
            <p className="text-sm text-gray-500">{stat.name}</p>
            <h3 className="text-2xl font-bold text-gray-800 mt-1">
              {stat.value}
            </h3>
            <p
              className={`text-sm font-medium ${
                stat.positive ? "text-green-600" : "text-red-600"
              }`}
            >
              {stat.change}
            </p>
          </div>
        ))}
      </div>

      {/* Charts Section */}
      <SectionHeader title="Trends Over Time" />
      <div className="grid md:grid-cols-2 gap-6 mb-8">
        {/* Temperature Chart */}
        <div className="bg-white rounded-xl shadow p-6">
          <h3 className="font-semibold text-[#0d2544] mb-2">
            Temperature (°C) Over Time
          </h3>
          <p className="text-sm text-gray-500 mb-3">
            Avg. {stats[0]?.value}{" "}
            <span className="text-green-600">{stats[0]?.change}</span> (
            {dateRange})
          </p>
          <div className="w-full h-[240px]">
            <ResponsiveContainer>
              <LineChart data={tempData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Line
                  type="monotone"
                  dataKey="temp"
                  stroke="#2563eb"
                  strokeWidth={3}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Rainfall Chart */}
        <div className="bg-white rounded-xl shadow p-6">
          <h3 className="font-semibold text-[#0d2544] mb-2">
            Rainfall (mm) Over Time
          </h3>
          <p className="text-sm text-gray-500 mb-3">
            Total {stats[1]?.value}{" "}
            <span
              className={stats[1]?.positive ? "text-green-600" : "text-red-600"}
            >
              {stats[1]?.change}
            </span>{" "}
            ({dateRange})
          </p>
          <div className="w-full h-[240px]">
            <ResponsiveContainer>
              <AreaChart data={rainData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Area
                  type="monotone"
                  dataKey="rain"
                  stroke="#0ea5a4"
                  fill="#99f6e4"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Table Section */}
      <SectionHeader title="Detailed Weather Data" />
      <div className="bg-white rounded-xl shadow p-6 overflow-auto">
        <table className="min-w-full text-sm">
          <thead className="text-left text-gray-600 border-b">
            <tr>
              <th className="py-2">Date</th>
              <th className="py-2">Location</th>
              <th className="py-2">Temperature (°C)</th>
              <th className="py-2">Rainfall (mm)</th>
            </tr>
          </thead>
          <tbody>
            {tempData.slice(0, 5).map((d, i) => (
              <tr key={i} className="border-b hover:bg-gray-50">
                <td className="py-2">
                  {new Date(Date.now() - i * 86400000)
                    .toISOString()
                    .slice(0, 10)}
                </td>
                <td className="py-2">
                  {["Lagos", "Abuja", "Kano", "Port Harcourt", "Ibadan"][i]}
                </td>
                <td className="py-2">{d.temp}</td>
                <td className="py-2">{rainData[i]?.rain}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {/* Footer */}
      <footer className="pt-6 text-center text-gray-500 text-sm">
        © 2025 OutbreakIQ. All rights reserved.
      </footer>
    </div>
  );
};

// 🔸 Reusable Section Header (same style as Prediction)
const SectionHeader = ({ title }) => (
  <h2 className="text-lg font-semibold text-[#0d2544] mb-3 mt-6 border-l-4 border-green-600 pl-3">
    {title}
  </h2>
);

export default Climate;
