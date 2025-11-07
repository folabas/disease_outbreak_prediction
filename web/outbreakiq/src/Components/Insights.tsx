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

const featureData = [
  { name: "Rainfall Patterns", value: 92 },
  { name: "Population Density", value: 85 },
  { name: "Healthcare Access", value: 78 },
  { name: "Avg. Temperature", value: 65 },
  { name: "Sanitation Index", value: 59 },
];

const Insights: React.FC = () => {
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
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-bold">Model Insights & Explanation</h2>
        <p className="mt-2 text-slate-600">
          Our AI model was trained using 10 years of outbreak data across 36
          Nigerian states. This section provides transparency into its
          performance and methodology.
        </p>
      </div>

      <div className="grid md:grid-cols-3 gap-6">
        <div className="bg-white rounded-lg shadow p-4">
          <h4 className="font-semibold">Performance Metrics</h4>
          <div className="mt-4 grid grid-cols-2 gap-4">
            <div className="p-3 bg-slate-50 rounded">
              Accuracy
              <br />
              <strong className="text-2xl text-emerald-600">91%</strong>
            </div>
            <div className="p-3 bg-slate-50 rounded">
              Precision
              <br />
              <strong className="text-2xl text-amber-500">88%</strong>
            </div>
            <div className="p-3 bg-slate-50 rounded">
              Recall
              <br />
              <strong className="text-2xl text-sky-500">93%</strong>
            </div>
            <div className="p-3 bg-slate-50 rounded">
              F1-Score
              <br />
              <strong className="text-2xl text-indigo-600">90%</strong>
            </div>
          </div>
        </div>

        <div className="md:col-span-2 bg-white rounded-lg shadow p-4">
          <h4 className="font-semibold mb-3">Feature Importance</h4>
          <div className="w-full h-[260px]">
            <ResponsiveContainer>
              <BarChart data={featureData} layout="vertical">
                <XAxis type="number" hide />
                <YAxis dataKey="name" type="category" width={180} />
                <Tooltip />
                <Bar dataKey="value" fill="#2563eb" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
      <Footer />
    </motion.div>
  );
};

export default Insights;
