import { useEffect, useState } from "react";
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
import html2canvas from "html2canvas";
import jsPDF from "jspdf";

/* ---------- Mock Data ---------- */
const featureData = [
  { name: "Rainfall Patterns", value: 92 },
  { name: "Population Density", value: 85 },
  { name: "Healthcare Access", value: 78 },
  { name: "Avg. Temperature", value: 65 },
  { name: "Sanitation Index", value: 59 },
];

const confidenceData = [
  { name: "Cholera", value: 30 },
  { name: "Malaria", value: 25 },
  { name: "Lassa Fever", value: 20 },
  { name: "COVID-19", value: 15 },
  { name: "Others", value: 10 },
];

const COLORS = ["#15803d", "#2563eb", "#60a5fa", "#93c5fd", "#e5e7eb"];

const retrainingLogs = [
  {
    date: "Oct 28, 2025",
    event: "Model retrained with 2023 outbreak data from NCDC",
    details: "Added Lassa Fever 2023 data and recalibrated rainfall index.",
  },
  {
    date: "Oct 25, 2025",
    event: "Parameter optimization completed",
    details:
      "Adjusted learning rate and neural attention weights for regional balance.",
  },
  {
    date: "Oct 20, 2025",
    event: "Feature expansion",
    details:
      "Included healthcare accessibility index and sanitation data from WHO.",
  },
  {
    date: "Nov 13, 2025",
    event: "Model deployed to OutbreakIQ dashboard",
    details: "Enabled public prediction and API integration.",
  },
  {
    date: "Oct 10, 2025",
    event: "Data cleaning and preprocessing",
    details:
      "Removed incomplete datasets and normalized features for stability.",
  },
];

/* ---------- Component ---------- */
const Insights = () => {
  const [loading, setLoading] = useState(true);
  const [exportOpen, setExportOpen] = useState(false);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedLog, setSelectedLog] = useState(null);

  useEffect(() => {
    const t = setTimeout(() => setLoading(false), 1200);
    return () => clearTimeout(t);
  }, []);

  /* ---------------------------------------------------
     EXPORT FUNCTIONS
  ---------------------------------------------------- */
  const exportPDF = async () => {
    const element = document.querySelector(".export-area");
    if (!element) return alert("Export area not found!");

    const canvas = await html2canvas(element, { scale: 2 });
    const imgData = canvas.toDataURL("image/png");

    const pdf = new jsPDF("p", "mm", "a4");
    const width = pdf.internal.pageSize.getWidth();
    const height = (canvas.height * width) / canvas.width;

    pdf.addImage(imgData, "PNG", 0, 0, width, height);
    pdf.save("OutbreakIQ_Report.pdf");
  };

  const exportCSV = () => {
    const header = [
      "Metric,Value",
      "Model Accuracy,91%",
      "Precision,88%",
      "Recall,93%",
      "F1 Score,90%",
      "",
      "Feature,Importance Score",
    ];

    const features = featureData.map((f) => `${f.name},${f.value}`);
    const confidence = [
      "",
      "Disease,Confidence %",
      ...confidenceData.map((c) => `${c.name},${c.value}`),
    ];

    const logs = [
      "",
      "Date,Event,Details",
      ...retrainingLogs.map(
        (log) => `${log.date},"${log.event}","${log.details}"`
      ),
    ];

    const csvContent = [...header, ...features, ...confidence, ...logs].join(
      "\n"
    );

    const blob = new Blob([csvContent], {
      type: "text/csv;charset=utf-8;",
    });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = "OutbreakIQ_Report.csv";
    link.click();
  };

  const exportPNG = async () => {
    const element = document.querySelector(".export-area");
    if (!element) return alert("Export area not found!");

    const canvas = await html2canvas(element, { scale: 2 });
    const url = canvas.toDataURL("image/png");

    const link = document.createElement("a");
    link.href = url;
    link.download = "OutbreakIQ_Report.png";
    link.click();
  };

  /* ---------------------------------------------------
     RENDER
  ---------------------------------------------------- */
  if (loading) return <Loader />;

  return (
    <>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.6 }}
        className="min-h-screen bg-gray-50 p-6 export-area"
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
          <MetricCard label="Model Accuracy" value="91%" />
          <MetricCard label="Precision" value="88%" />
          <MetricCard label="Recall" value="93%" />
          <MetricCard label="F1-Score" value="90%" />
        </div>

        {/* Visualization */}
        <SectionHeader title="Performance Visualization" />
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="md:col-span-2 bg-white rounded-xl shadow p-6">
            <h3 className="font-semibold text-[#0d2544] mb-2">
              ROC Curve
              <span className="float-right text-sm text-gray-500">
                AUC: 0.94
              </span>
            </h3>
            <div className="h-[260px] flex items-center justify-center bg-black rounded-lg">
              <p className="text-white text-sm opacity-70">ROC Visualization</p>
            </div>
          </div>

          <div className="bg-white rounded-xl shadow p-6 relative">
            <h3 className="font-semibold text-[#0d2544] mb-3">Model Details</h3>

            <div className="text-sm text-gray-700 space-y-2 mb-5">
              <p>
                <b className="text-[#0d2544]">Model Version:</b> v1.0.1
              </p>
              <p>
                <b className="text-[#0d2544]">Last Retrained:</b> Nov 11, 2025
              </p>
              <p>
                <b className="text-[#0d2544]">Data Source:</b> NCDC & WHO
                Archives
              </p>
            </div>

            <div className="bg-blue-50 border-l-4 border-green-700 p-3 rounded-md mb-4">
              <h4 className="font-semibold text-[#0d2544] text-sm mb-1">
                Impact & Use Case
              </h4>
              <p className="text-xs text-gray-600">
                OutbreakIQ helps WHO, NCDC, and NGOs act faster by providing
                early warnings.
              </p>
            </div>

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
                    <li
                      onClick={exportPDF}
                      className="px-3 py-2 hover:bg-gray-100 cursor-pointer"
                    >
                      Download as PDF
                    </li>
                    <li
                      onClick={exportCSV}
                      className="px-3 py-2 hover:bg-gray-100 cursor-pointer"
                    >
                      Export CSV
                    </li>
                    <li
                      onClick={exportPNG}
                      className="px-3 py-2 hover:bg-gray-100 cursor-pointer"
                    >
                      Save as PNG
                    </li>
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
                <BarChart data={featureData} layout="vertical">
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
            <h3 className="font-semibold text-[#0d2544] mb-3">
              Model Confidence Breakdown
            </h3>
            <div className="flex-1 flex justify-center">
              <ResponsiveContainer width="100%" height={280}>
                <PieChart>
                  <Pie
                    data={confidenceData}
                    cx="50%"
                    cy="50%"
                    innerRadius={70}
                    outerRadius={100}
                    dataKey="value"
                    label={({ name, percent }) =>
                      `${name} ${(percent * 100).toFixed(0)}%`
                    }
                  >
                    {confidenceData.map((entry, index) => (
                      <Cell
                        key={`cell-${index}`}
                        fill={COLORS[index % COLORS.length]}
                      />
                    ))}
                  </Pie>
                  <Legend />
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>

        {/* Explanation Logs */}
        <SectionHeader title="Explanation Logs" />
        <div className="bg-white rounded-xl shadow p-6 mb-8">
          <p className="text-sm text-gray-600 mb-4">
            Historical retraining updates and parameter optimizations for
            transparency.
          </p>

          <button
            onClick={() => setIsModalOpen(true)}
            className="bg-green-700 text-white px-4 py-2 rounded-md text-sm font-semibold hover:bg-green-800 transition"
          >
            View Full Explanation Logs
          </button>
        </div>

        <footer className="pt-6 text-center text-gray-500 text-sm">
          © 2025 OutbreakIQ. All rights reserved.
        </footer>
      </motion.div>

      {/* ---------- Modal: All Logs ---------- */}
      <AnimatePresence>
        {isModalOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-40 px-4"
          >
            <motion.div
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.8, opacity: 0 }}
              transition={{ duration: 0.3 }}
              className="bg-white rounded-xl shadow-2xl w-full max-w-2xl p-6 relative max-h-[80vh] overflow-y-auto"
            >
              <button
                onClick={() => setIsModalOpen(false)}
                className="absolute top-3 right-3 text-gray-400 hover:text-gray-600"
              >
                ✕
              </button>

              <h2 className="text-xl font-semibold text-[#0d2544] mb-4">
                Explanation Logs
              </h2>

              <div className="divide-y">
                {retrainingLogs.map((log, index) => (
                  <div
                    key={index}
                    onClick={() => setSelectedLog(log)}
                    className="py-3 cursor-pointer hover:bg-gray-50 px-2 rounded-md"
                  >
                    <p className="font-semibold text-[#0d2544] text-sm">
                      {log.date} — {log.event}
                    </p>
                    <p className="text-xs text-gray-600 mt-1">{log.details}</p>
                  </div>
                ))}
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* ---------- Nested Modal: Individual Log ---------- */}
      <AnimatePresence>
        {selectedLog && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-[60] flex items-center justify-center bg-black bg-opacity-50 px-4"
          >
            <motion.div
              initial={{ scale: 0.8 }}
              animate={{ scale: 1 }}
              exit={{ scale: 0.8 }}
              transition={{ duration: 0.25 }}
              className="bg-white rounded-xl shadow-2xl w-full max-w-md p-6 relative"
            >
              <button
                onClick={() => setSelectedLog(null)}
                className="absolute top-3 right-3 text-gray-400 hover:text-gray-600"
              >
                ✕
              </button>
              <h3 className="text-lg font-semibold text-[#0d2544] mb-2">
                {selectedLog.event}
              </h3>
              <p className="text-sm text-gray-500 mb-1">
                <b>Date:</b> {selectedLog.date}
              </p>
              <p className="text-sm text-gray-700 leading-relaxed">
                {selectedLog.details}
              </p>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
};

/* ---------- Components ---------- */
const MetricCard = ({ label, value }) => (
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

const SectionHeader = ({ title }) => (
  <h2 className="text-lg font-semibold text-[#0d2544] mb-3 mt-6 border-l-4 border-green-700 pl-3">
    {title}
  </h2>
);

export default Insights;
