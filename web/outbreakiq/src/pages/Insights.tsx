import { useState } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Legend,
} from "recharts";
import Loader from "../Components/Loader";
import { motion, AnimatePresence } from "framer-motion";
import Footer from "../Components/Footer";
import { useInsights } from "../hooks/useInsights";


const COLORS = ["#15803d", "#2563eb", "#60a5fa", "#93c5fd", "#e5e7eb"];

/* ---------- Component ---------- */
const Insights = () => {
  // UI insights focus on COVID-19 for MVP; backend provides metrics per disease.
  const { metrics, featureImportance, notes, loading, error } = useInsights("covid-19");
  const [exportOpen, setExportOpen] = useState(false);

  const formatPercent = (n?: number) => {
    if (typeof n !== "number") return "-";
    const v = n <= 1 ? n * 100 : n;
    return `${Math.round(v)}%`;
  };

  const featureDataFromHook = (featureImportance || []).map((fi: any) => {
    const name = fi?.feature ?? fi?.name ?? "Feature";
    const raw = fi?.importance ?? fi?.value ?? 0;
    const value = raw <= 1 ? Math.round(raw * 100) : Math.round(raw);
    return { name, value };
  });

  const featurePieData = (() => {
    const total = (featureDataFromHook || []).reduce((s, d) => s + (d.value || 0), 0);
    if (!total) return [] as { name: string; value: number }[];
    return featureDataFromHook.map((d) => ({ name: d.name, value: Number(((d.value / total) * 100).toFixed(1)) }));
  })();

  if (loading) return <Loader />;
  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 p-6">
        <SectionHeader title="Model Insights & Explanation" />
        <div className="bg-red-50 border-l-4 border-red-600 p-4 rounded-md text-sm text-red-700">
          Failed to load insights: {error}
        </div>
      </div>
    );
  }

  return (
    <>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.6 }}
        className="min-h-screen bg-gray-50 p-6"
      >
        {/* Header */}
        <header className="mb-6">
          <h1 className="text-3xl font-bold text-[#0d2544]">
            Model Insights & Explanation
          </h1>
          <p className="text-gray-600 text-sm mt-1">
            Transparent overview of our AI model’s performance, reliability, and
            methodology.
          </p>
        </header>

        {/* About Section */}
        <div className="bg-[#0d2544] text-white rounded-xl shadow p-6 mb-8">
          <h3 className="text-lg font-semibold mb-2">About Our AI Model</h3>
          <p className="text-sm text-gray-100 leading-relaxed">
            Our AI model was trained using 10 years of outbreak data across 36
            Nigerian states. This section provides transparency into its
            performance, reliability, and methodology.
          </p>
        </div>

        {/* Performance Metrics */}
        <SectionHeader title="Performance Metrics" />
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-8">
          <MetricCard label="Model Accuracy" value={formatPercent(metrics?.accuracy)} />
          <MetricCard label="Precision" value={formatPercent(metrics?.precision)} />
          <MetricCard label="Recall" value={formatPercent(metrics?.recall)} />
          <MetricCard label="F1-Score" value={formatPercent(metrics?.f1)} />
        </div>

        {/* Visualization */}
        <SectionHeader title="Performance Visualization" />
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="md:col-span-2 bg-white rounded-xl shadow p-6">
            <h3 className="font-semibold text-[#0d2544] mb-2">
              ROC Curve
              <span className="float-right text-sm text-gray-500">
                AUC: {typeof metrics?.auc === "number" ? metrics.auc.toFixed(2) : "-"}
              </span>
            </h3>
            <div className="h-[260px] flex items-center justify-center rounded-lg overflow-hidden bg-gray-50">
              <img
                src={`${import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1"}/analytics/roc?disease=covid-19`}
                alt="ROC Curve"
                className="w-full h-full object-contain"
                onError={(e) => {
                  (e.target as HTMLImageElement).style.display = "none";
                }}
              />
            </div>
          </div>
          <div className="bg-white rounded-xl shadow p-6 relative">
            <h3 className="font-semibold text-[#0d2544] mb-3">Export</h3>
            <div className="relative">
              <button
                onClick={() => setExportOpen(!exportOpen)}
                className="w-full bg-green-700 text-white py-2.5 rounded-md text-sm font-semibold hover:bg-green-800 transition flex items-center justify-center gap-2"
              >
                Export Report
              </button>
              {exportOpen && (
                <div className="absolute right-0 mt-2 w-40 bg-white border rounded-md shadow-lg z-10">
                  <ul className="text-sm text-gray-700">
                    <li className="px-3 py-2 hover:bg-gray-100 cursor-pointer">Download as PDF</li>
                    <li className="px-3 py-2 hover:bg-gray-100 cursor-pointer">Export CSV</li>
                    <li className="px-3 py-2 hover:bg-gray-100 cursor-pointer">Save as PNG</li>
                  </ul>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Feature Importance */}
        <SectionHeader title="Feature Importance & Confidence Breakdown" />
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          <div className="bg-white rounded-xl shadow p-6">
            <p className="text-sm text-gray-600 mb-4">
              This chart ranks influential features used for predictions.
            </p>
            <div className="w-full h-[300px]">
              <ResponsiveContainer>
                <BarChart data={featureDataFromHook} layout="vertical">
                  <XAxis type="number" hide />
                  <YAxis
                    dataKey="name"
                    type="category"
                    tick={{ fill: "#334155", fontSize: 13 }}
                    width={180}
                  />
                  <Tooltip />
                  <Bar dataKey="value" fill="#2563eb" radius={[6, 6, 6, 6]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
          <div className="bg-white rounded-xl shadow p-6 flex flex-col">
            <h3 className="font-semibold text-[#0d2544] mb-3">Feature Importance Distribution</h3>
            <div className="flex-1 flex justify-center">
              <ResponsiveContainer width="100%" height={280}>
                <PieChart>
                  <Pie
                    data={featurePieData}
                    cx="50%"
                    cy="50%"
                    innerRadius={70}
                    outerRadius={100}
                    dataKey="value"
                    label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  >
                    {(featurePieData || []).map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Legend />
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>

        {/* Explanation Notes */}
        <SectionHeader title="Explanation Notes" />
        <div className="bg-white rounded-xl shadow p-6 mb-8">
          {Array.isArray(notes) && notes.length > 0 ? (
            <ul className="list-disc list-inside text-sm text-gray-700 space-y-2">
              {notes.map((n, i) => (
                <li key={i}>{n}</li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-gray-600">No explanation notes available.</p>
          )}
        </div>

        <footer className="pt-6 text-center text-gray-500 text-sm">
          © 2025 OutbreakIQ. All rights reserved.
        </footer>
      </motion.div>

      {/* Removed modal-based logs in favor of backend-driven notes */}
    </>
  );
};

/* ---------- Components ---------- */
const MetricCard = ({ label, value }: { label: string; value: string }) => (
  <div className="bg-white rounded-xl shadow p-4 text-center hover:shadow-md transition">
    <p className="text-sm text-gray-500">{label}</p>
    <h3 className="text-3xl font-bold text-green-700 mt-1">{value}</h3>
    <div className="mt-2 w-full bg-gray-100 h-2 rounded-full overflow-hidden">
      <div
        className="bg-green-700 h-full rounded-full transition-all duration-700"
        style={{ width: value }}
      />
    </div>
  </div>
);

const SectionHeader = ({ title }: { title: string }) => (
  <h2 className="text-lg font-semibold text-[#0d2544] mb-3 mt-6 border-l-4 border-green-700 pl-3">
    {title}
  </h2>
);

export default Insights;
