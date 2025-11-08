import { useEffect, useState } from "react";
import { MapContainer, TileLayer, Marker } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import Loader from "./Loader";
import { motion } from "framer-motion";
import Footer from "./Footer";
/*import { hospitalApi } from "../services/api";*/
import type { HospitalData } from "../services/types";

const Hospital: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [hospitalStats, setHospitalStats] = useState<HospitalData[]>([]);

  useEffect(() => {
    const fetchHospitalData = async () => {
      try {
        // TODO: Implement this API call
        // const response = await hospitalApi.getHospitalStats();
        // setHospitalStats(response.data.data);

        // For now, using setTimeout to simulate API call
        const t = setTimeout(() => setLoading(false), 1500);
        return () => clearTimeout(t);
      } catch (error) {
        console.error("Error fetching hospital data:", error);
        setLoading(false);
      }
    };

    fetchHospitalData();
  }, []);

  if (loading) return <Loader />;

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.6 }}
      className="space-y-6"
    >
      <div className="grid md:grid-cols-3 gap-6">
        <div className="md:col-span-2 bg-white rounded-lg shadow p-4">
          <h3 className="font-semibold mb-4">
            Healthcare Capacity & Facility Density
          </h3>
          <div className="grid md:grid-cols-3 gap-4">
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
            <div className="bg-slate-50 p-4 rounded">
              Population per Facility
              <br />
              <strong className="text-2xl">~16,500</strong>
            </div>
          </div>

          <div className="mt-4 rounded overflow-hidden h-80">
            <MapContainer
              center={[9.082, 8.6753]}
              zoom={6}
              className="h-80 w-full"
            >
              <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
              <Marker position={[9.082, 8.6753]} />
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
    </motion.div>
  );
};

export default Hospital;
