import { useState } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";
import { MapContainer, TileLayer, GeoJSON } from "react-leaflet";
import Loader from "../Components/Loader";
import { usePredictions } from "../hooks/usePredictions";
import { useInsights } from "../hooks/useInsights";
import { useOptions } from "../hooks/useOptions";
import { useRecommendations } from "../hooks/useRecommendations";
import { usePredictedActual } from "../hooks/usePredictedActual";
import { useHeatmap } from "../hooks/useHeatmap";
import { useHotspots } from "../hooks/useHotspots";
import type { Disease } from "../services/types";


const Dashboard = () => {
  // UI focuses exclusively on COVID-19 for MVP; backend remains flexible for future diseases.
  const [disease, setDisease] = useState("COVID-19");
  const [region, setRegion] = useState("All");
  const [year, setYear] = useState("2024");
  const [rainfall, setRainfall] = useState<number>(1250);
  const [temperature, setTemperature] = useState<number>(29);

  // Normalize UI disease label to API union type (fallback to "cholera")
  const dl = "covid-19";
  const diseaseApi: Disease = "covid-19";

  // Hook: predictions (series, risk, stats)
  const [reload, setReload] = useState(0);
  const { series: predSeries, risk, stats, loading, error } = usePredictions(diseaseApi, region, reload);
  // Hook: insights (notes for summary)
  const { notes: insightNotes, loading: insightsLoading, error: insightsError } = useInsights(diseaseApi, region, reload);
  // Hook: dynamic options for selects
  const { options: metaOptions, loading: optionsLoading, error: optionsError } = useOptions({ source: "auto" });
  // Hook: recommendations list
  const { recommendations, loading: recsLoading, error: recsError } = useRecommendations({ disease: dl, region, year: Number(year) }, reload);
  // Hook: merged predicted vs actual series
  const { series, liveOnly, loading: paLoading, error: paError } = usePredictedActual({ disease: dl, region }, reload);
  // Hooks: map overlays
  const { geojson: heatmap, loading: heatLoading } = useHeatmap(region, dl, reload);
  const { features: hotspots, loading: hotLoading } = useHotspots(diseaseApi, Number(year), reload);
  const [showHeatmap, setShowHeatmap] = useState(true);
  const [showHotspots, setShowHotspots] = useState(true);

  // Remove simulated loading; rely on hook's loading state.

  const predictRisk = () => {
    // Manually trigger refetch without changing selection
    setReload((x) => x + 1);
  };

  const isPredicting = loading;
  const hasPrediction = reload > 0;

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      {/* 🔹 Main Header */}
      <header className="mb-8">
        <h1 className="text-3xl font-bold text-[#0d2544]">
          COVID-19 Outbreak Prediction System
        </h1>
        <p className="text-gray-600 text-sm mt-1">
          Monitor, analyze, and predict outbreak risks across Nigeria.
        </p>

        
      </header>

      {hasPrediction && (
        <>
          <SectionHeader title="Overview Metrics" />
          <div className="grid grid-cols-2 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
            <StatCard title="Latest Confirmed Cases" value={String(stats.latest ?? 0)} />
            <StatCard title="Average Weekly Cases" value={String(stats.average ?? 0)} />
          </div>
        </>
      )}

      {hasPrediction && (
        <>
      <SectionHeader title="Outbreak Visualization" />
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        {/* Map */}
        <div className="lg:col-span-2 bg-white rounded-xl shadow p-4">
          <h2 className="font-semibold mb-3 text-[#0d2544]">
            Nigeria Outbreak Risk Map
          </h2>
          <div className="h-[320px] rounded-lg overflow-hidden">
            <MapContainer
              center={[9.082, 8.6753]}
              zoom={6}
              className="h-full w-full"
            >
              <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
              {showHeatmap && heatmap && (
                <GeoJSON data={heatmap as any} />
              )}
              {showHotspots && Array.isArray(hotspots) && hotspots.length > 0 && (
                <GeoJSON data={{ type: "FeatureCollection", features: hotspots } as any} />
              )}
            </MapContainer>
            <div className="mt-2 flex gap-3 text-xs text-gray-600">
              <label className="flex items-center gap-1">
                <input type="checkbox" checked={showHeatmap} onChange={(e) => setShowHeatmap(e.target.checked)} />
                Heatmap
              </label>
              <label className="flex items-center gap-1">
                <input type="checkbox" checked={showHotspots} onChange={(e) => setShowHotspots(e.target.checked)} />
                Hotspots
              </label>
            </div>
          </div>
        </div>

        {/* Predicted vs Actual Chart */}
        <div className="bg-white rounded-xl shadow p-4">
          <h2 className="font-semibold mb-3 text-[#0d2544]">
            Predicted vs Actual Cases
          </h2>
          <div className="flex items-center gap-3 mb-2">
            {liveOnly && (
              <span className="px-2 py-1 text-xs bg-yellow-100 text-yellow-700 rounded">Live only</span>
            )}
            {paLoading && <span className="text-xs text-gray-500">Loading chart…</span>}
            {paError && <span className="text-xs text-red-600">{paError}</span>}
          </div>
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={series}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip />
              <Line type="monotone" dataKey="actual" stroke="#e53e3e" strokeWidth={3} name="Actual" />
              <Line type="monotone" dataKey="predicted" stroke="#2f855a" strokeWidth={3} name="Predicted" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
        </>
      )}

      {hasPrediction && (
        <>
      <SectionHeader title="Outbreak Insights" />
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        <div className="lg:col-span-2 bg-white rounded-xl shadow p-4">
          <h2 className="font-semibold mb-3 text-[#0d2544]">Insight Summary</h2>
          {insightsLoading ? (
            <p className="text-gray-500 text-sm">Loading insights…</p>
          ) : insightsError ? (
            <p className="text-red-600 text-sm">Failed to load insights: {insightsError}</p>
          ) : Array.isArray(insightNotes) && insightNotes.length > 0 ? (
            <ul className="list-disc list-inside text-gray-700 text-sm space-y-1">
              {insightNotes.map((n, i) => (
                <li key={i}>{n}</li>
              ))}
            </ul>
          ) : (
            <p className="text-gray-600 text-sm">No insights available for the current selection.</p>
          )}
        </div>

        <div className="bg-white rounded-xl shadow p-4 flex flex-col items-center justify-center">
          <h2 className="font-semibold mb-3 text-[#0d2544]">Risk Summary</h2>
          <p className="text-sm text-gray-600">Predicted Risk Level</p>
          <h3 className={`text-2xl font-bold ${
            (risk?.level || "Unknown") === "High" ? "text-red-600" : "text-yellow-500"
          }`}>{risk?.level || "Unknown"}</h3>
          <p className="mt-2 text-gray-600 text-sm">Confidence: <span className="font-semibold">{risk ? risk.confidence : 0}%</span></p>
        </div>
      </div>
        </>
      )}

      {/* 🔹 Prediction Section */}
      <SectionHeader title="Run New Prediction" />
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Prediction Form */}
        <div className="bg-white rounded-xl shadow p-6">
          <h2 className="font-semibold mb-4 text-[#0d2544]">
            Run a New Prediction
          </h2>
          <div className="space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-sm text-gray-600">Disease</label>
                <select
                  title="disease"
                  value={disease}
                  onChange={() => {}}
                  disabled
                  className="w-full border rounded-md px-3 py-2 mt-1 bg-gray-100 text-gray-600"
                >
                  <option>COVID-19</option>
                </select>
              </div>
              <div>
                <label className="text-sm text-gray-600">Region</label>
                <select
                  title="region"
                  value={region}
                  onChange={(e) => setRegion(e.target.value)}
                  className="w-full border rounded-md px-3 py-2 mt-1"
                >
                  {(metaOptions.regions?.length ? metaOptions.regions : ["All","Lagos","Kano","Rivers"]).map((r) => (
                    <option key={r}>{r}</option>
                  ))}
                  {!metaOptions.regions?.length && <option disabled>Loading…</option>}
                </select>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-sm text-gray-600">
                  Avg. Rainfall (mm)
                </label>
                <input
                  placeholder="1250"
                  type="number"
                  value={rainfall}
                  onChange={(e) => setRainfall(Number(e.target.value))}
                  className="w-full border rounded-md px-3 py-2 mt-1"
                />
              </div>
              <div>
                <label className="text-sm text-gray-600">
                  Avg. Temperature (°C)
                </label>
                <input
                  placeholder="25"
                  type="number"
                  value={temperature}
                  onChange={(e) => setTemperature(Number(e.target.value))}
                  className="w-full border rounded-md px-3 py-2 mt-1"
                />
              </div>
            </div>

            <button
              onClick={predictRisk}
              disabled={isPredicting}
              className={`w-full mt-4 ${isPredicting ? "bg-green-400" : "bg-green-700 hover:bg-green-600"} text-white font-semibold py-2 rounded-md transition disabled:opacity-70`}
            >
              {isPredicting ? "Calculating…" : "Predict Risk"}
            </button>
            {error && (
              <p className="mt-2 text-sm text-red-600">{error}</p>
            )}
          </div>
        </div>

        {/* Prediction Result */}
        {hasPrediction && (
        <div className="bg-white rounded-xl shadow p-6">
          <h2 className="font-semibold mb-4 text-[#0d2544]">
            Prediction Result
          </h2>
          <div className="text-center">
            <p className="text-gray-500 text-sm mb-1">Predicted Risk Level</p>
            <h3
              className={`text-3xl font-bold ${
                (risk?.level || "Unknown") === "High" ? "text-red-600" : "text-yellow-500"
              }`}
            >
              {risk?.level || "Unknown"}
            </h3>
            <p className="mt-2 text-gray-600 text-sm">
              Confidence Score:{" "}
              <span className="font-semibold">{risk ? risk.confidence : 0}%</span>
            </p>
          </div>

          <div className="mt-5">
            <h4 className="font-semibold text-gray-800 text-sm mb-2">
              Preventive Recommendations:
            </h4>
            {recsLoading ? (
              <p className="text-gray-500 text-sm">Loading recommendations…</p>
            ) : recsError ? (
              <p className="text-red-600 text-sm">Failed to load: {recsError}</p>
            ) : recommendations.length ? (
              <ul className="list-disc list-inside text-gray-600 text-sm space-y-1">
                {recommendations.map((rec, i) => (
                  <li key={i}>{rec}</li>
                ))}
              </ul>
            ) : (
              <p className="text-gray-600 text-sm">No recommendations available for current selection.</p>
            )}
          </div>
        </div>
        )}
      </div>
      {/* Footer */}
      <footer className="pt-6 text-center text-gray-500 text-sm">
        © 2025 OutbreakIQ. All rights reserved.
      </footer>
    </div>
  );
};

/* 🔸 Reusable Components */

type StatCardProps = { title: string; value: string };
const StatCard = ({ title, value }: StatCardProps) => (
  <div className="bg-white rounded-xl shadow p-4">
    <p className="text-sm text-gray-500">{title}</p>
    <h3 className="text-2xl font-bold text-gray-800 mt-1">{value}</h3>
  </div>
);

type SectionHeaderProps = { title: string };
const SectionHeader = ({ title }: SectionHeaderProps) => (
  <h2 className="text-lg font-semibold text-[#0d2544] mb-3 mt-6 border-l-4 border-green-600 pl-3">
    {title}
  </h2>
);

export default Dashboard;
