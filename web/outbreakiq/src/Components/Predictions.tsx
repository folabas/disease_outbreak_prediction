import React, { useEffect, useState } from "react";
import { MapContainer, TileLayer, Marker, Popup } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";
import Loader from "./Loader";
import { motion } from "framer-motion";

const sampleData = [
  { name: "Jan", value: 40 },
  { name: "Feb", value: 50 },
  { name: "Mar", value: 60 },
  { name: "Apr", value: 80 },
  { name: "May", value: 120 },
  { name: "Jun", value: 140 },
];

const Predictions: React.FC = () => {
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
      className="grid lg:grid-cols-3 gap-6"
      data-aos="fade-up"
    >
      <div className="lg:col-span-2 space-y-6">
        <div className="bg-white rounded-lg shadow p-4">
          <h3 className="font-semibold mb-2">Nigeria Outbreak Risk Map</h3>
          <div className="h-80 rounded">
            <MapContainer
              center={[9.082, 8.6753]}
              zoom={6}
              className="h-80 rounded"
            >
              <TileLayer
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                attribution="&copy; OpenStreetMap contributors"
              />
              <Marker position={[9.082, 8.6753]}>
                <Popup>Sample marker</Popup>
              </Marker>
            </MapContainer>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-4">
          <h3 className="font-semibold mb-2">Predicted vs Actual Cases</h3>
          <div className="w-full h-[220px]">
            <ResponsiveContainer>
              <LineChart data={sampleData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Line
                  type="monotone"
                  dataKey="value"
                  stroke="#10b981"
                  strokeWidth={3}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      <aside className="space-y-6">
        <div className="bg-white rounded-lg shadow p-4">
          <h4 className="font-semibold">Key Stats</h4>
          <div className="mt-3 space-y-3 text-slate-700">
            <div>
              Average Rainfall: <strong>1200 mm</strong>
            </div>
            <div>
              Avg Temperature: <strong>28°C</strong>
            </div>
            <div>
              Population Density: <strong>212/km²</strong>
            </div>
            <div>
              Hospital Capacity: <strong>5 beds/10k</strong>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-4">
          <h4 className="font-semibold">Prediction Result</h4>
          <div className="mt-4 text-center">
            <div className="text-2xl font-bold text-amber-600">High</div>
            <div className="text-sm text-slate-500 mt-2">Confidence: 88%</div>
          </div>
        </div>
      </aside>
    </motion.div>
  );
};

export default Predictions;
