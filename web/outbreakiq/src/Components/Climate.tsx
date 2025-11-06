import React, { useEffect, useState } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  AreaChart,
  Area,
} from "recharts";
import Loader from "./Loader";
import { motion } from "framer-motion";

const tempData = [
  { name: "Day 1", temp: 32 },
  { name: "Day 2", temp: 31 },
  { name: "Day 3", temp: 33 },
  { name: "Day 4", temp: 34 },
  { name: "Day 5", temp: 32 },
];

const rainData = [
  { name: "Day 1", rain: 5 },
  { name: "Day 2", rain: 0 },
  { name: "Day 3", rain: 12 },
  { name: "Day 4", rain: 8 },
  { name: "Day 5", rain: 0 },
];

const Climate: React.FC = () => {
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const t = setTimeout(() => setLoading(false), 3000);
    return () => clearTimeout(t);
  }, []);

  if (loading) return <Loader />;

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.6 }}
      className="space-y-6"
      data-aos="fade-up"
    >
      <div className="grid md:grid-cols-2 gap-6">
        <div className="bg-white shadow rounded-lg p-4">
          <h3 className="font-semibold mb-3">Temperature (°C) Over Time</h3>
          <div className="w-full h-[220px]">
            <ResponsiveContainer>
              <LineChart data={tempData}>
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Line
                  type="monotone"
                  dataKey="temp"
                  stroke="#2563eb"
                  strokeWidth={2}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="bg-white shadow rounded-lg p-4">
          <h3 className="font-semibold mb-3">Rainfall (mm) Over Time</h3>
          <div className="w-full h-[220px]">
            <ResponsiveContainer>
              <AreaChart data={rainData}>
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

      <div className="bg-white shadow rounded-lg p-4">
        <h3 className="font-semibold mb-2">Detailed Weather Data</h3>
        <div className="overflow-auto">
          <table className="min-w-full text-sm">
            <thead className="text-left text-slate-600">
              <tr>
                <th className="py-2">Date</th>
                <th className="py-2">Location</th>
                <th className="py-2">Temp (°C)</th>
                <th className="py-2">Rainfall (mm)</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td className="py-2">2023-10-26</td>
                <td className="py-2">Lagos</td>
                <td className="py-2">31.5</td>
                <td className="py-2">5.2</td>
              </tr>
              <tr>
                <td className="py-2">2023-10-25</td>
                <td className="py-2">Abuja</td>
                <td className="py-2">33.1</td>
                <td className="py-2">0</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </motion.div>
  );
};

export default Climate;
