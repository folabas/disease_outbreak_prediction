import { useEffect, useState } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import Loader from "./Loader";
import { motion } from "framer-motion";
import Footer from "./Footer";

const growthData = [
  { region: "North West", value: 4.2 },
  { region: "South West", value: 3.8 },
  { region: "North Central", value: 3.1 },
  { region: "South South", value: 2.8 },
  { region: "North East", value: 2.4 },
  { region: "South East", value: 2.1 },
];

const Population = () => {
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const t = setTimeout(() => setLoading(false), 1500);
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
      <div className="grid md:grid-cols-3 gap-6">
        <div className="md:col-span-2 bg-white rounded-lg shadow p-4">
          <h3 className="font-semibold mb-3">Population Growth by Region</h3>
          <div className="w-full h-[240px]">
            <ResponsiveContainer>
              <BarChart data={growthData} layout="vertical">
                <XAxis type="number" hide />
                <YAxis dataKey="region" type="category" />
                <Tooltip />
                <Bar dataKey="value" fill="#2563eb" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-4">
          <h3 className="font-semibold mb-3">Population Density Heatmap</h3>
          <div className="h-48 bg-slate-100 rounded" />
        </div>
      </div>
      <Footer />
    </motion.div>
  );
};

export default Population;
