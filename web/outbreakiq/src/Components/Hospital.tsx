import React, { useEffect, useState } from "react";
import { MapContainer, TileLayer, Marker } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import Loader from "./Loader";
import { motion } from "framer-motion";

const Hospital: React.FC = () => {
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
      <div className="grid md:grid-cols-3 gap-6">
        <div className="md:col-span-2 bg-white rounded-lg shadow p-4">
          <h3 className="font-semibold mb-4">
            Healthcare Capacity & Facility Density
          </h3>
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-slate-50 p-4 rounded">
              Total Facilities
              <br />
              <strong className="text-2xl">12,450</strong>
            </div>
            <div className="bg-slate-50 p-4 rounded">
              Average Bed Capacity
              <br />
              <strong className="text-2xl">82</strong>
            </div>
          </div>

          <div className="mt-4 bg-white rounded shadow p-4">
            <MapContainer
              center={[9.082, 8.6753]}
              zoom={6}
              className="h-64 rounded"
            >
              <TileLayer
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                attribution="&copy; OpenStreetMap contributors"
              />
              <Marker position={[9.082, 8.6753]} />
            </MapContainer>
          </div>
        </div>

        <aside className="space-y-4">
          <div className="bg-white rounded-lg shadow p-4">
            Filters (state/LGA/type)
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            Capacity Level Slider
          </div>
        </aside>
      </div>
    </motion.div>
  );
};

export default Hospital;
import React from "react";
import { MapContainer, TileLayer } from "react-leaflet";
import "leaflet/dist/leaflet.css";

const Hospital: React.FC = () => {
  return (
    <div className="space-y-6">
      <div className="grid md:grid-cols-3 gap-6">
        <div className="md:col-span-2 bg-white rounded-lg shadow p-4">
          <h3 className="font-semibold mb-3">
            Healthcare Capacity & Facility Density
          </h3>
          <div className="grid md:grid-cols-3 gap-4">
            <div className="bg-slate-50 p-4 rounded">
              Total Facilities
              <br />
              <strong>12,450</strong>
            </div>
            <div className="bg-slate-50 p-4 rounded">
              Average Bed Capacity
              <br />
              <strong>82</strong>
            </div>
            <div className="bg-slate-50 p-4 rounded">
              Population per Facility
              <br />
              <strong>~16,500</strong>
            </div>
          </div>

          <div className="mt-4 rounded overflow-hidden h-80">
            <MapContainer
              center={[9.082, 8.6753]}
              zoom={6}
              className="h-80 w-full"
            >
              <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
            </MapContainer>
          </div>
        </div>

        <aside className="bg-white rounded-lg shadow p-4">
          <h4 className="font-semibold">Filters</h4>
          <div className="mt-4 space-y-3 text-sm text-slate-600">
            <div>State: All</div>
            <div>LGA: All</div>
            <div>Facility Type: All</div>
          </div>
        </aside>
      </div>
    </div>
  );
};

export default Hospital;
