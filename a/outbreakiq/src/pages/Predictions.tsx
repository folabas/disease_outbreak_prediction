import { useEffect, useMemo, useState } from "react";
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
import { useModelMetrics } from "../hooks/useModelMetrics";
import { useReports } from "../hooks/useReports";
import { useDiseaseAlerts } from "../hooks/useDiseaseAlerts";
import { useDashboardStore } from "../store/useDashboardStore";
import { validateYear } from "../utils/validation";
import type { Disease } from "../services/types";


const Dashboard = () => {
  const { disease: globalDisease, region: globalRegion, setDisease: setGlobalDisease, setRegion: setGlobalRegion } = useDashboardStore();
  const fallbackDiseases: Disease[] = ["cholera", "malaria", "ebola", "covid"];
  const [disease, setDisease] = useState<Disease>(globalDisease);
  const [region, setRegion] = useState(globalRegion);
  const [year, setYear] = useState<string>(String(new Date().getFullYear()));
  const [rainfall, setRainfall] = useState<number>(1250);
  const [temperature, setTemperature] = useState<number>(29);
  const [yearError, setYearError] = useState<string | null>(null);
  
  // Validate year on change
  useEffect(() => {
    if (year) {
      const validated = validateYear(year);
      if (validated === null) {
        setYearError(`Year must be between 2006 and ${new Date().getFullYear() + 1}`);
      } else {
        setYearError(null);
      }
    }
  }, [year]);
  
  // Sync local state with global state
  useEffect(() => {
    setGlobalDisease(disease);
  }, [disease, setGlobalDisease]);
  
  useEffect(() => {
    setGlobalRegion(region);
  }, [region, setGlobalRegion]);

  // Hook: dynamic options for selects (always load)
  const { options: metaOptions, loading: optionsLoading, error: optionsError } = useOptions({ source: "auto", disease });
  
  // Prediction state - only load when user clicks "Predict"
  const [shouldPredict, setShouldPredict] = useState(false);
  const [hasPrediction, setHasPrediction] = useState(false);
  const [isPredicting, setIsPredicting] = useState(false);
  
  // Hook: predictions (series, risk, stats) - only when shouldPredict is true
  const { series: predSeries, risk, stats, loading: predLoading, error: predError } = usePredictions(
    disease, 
    region, 
    shouldPredict ? 1 : undefined
  );
  // Hook: insights (notes for summary) - only when shouldPredict is true
  const { notes: insightNotes, loading: insightsLoading, error: insightsError, metrics: insightMetrics } = useInsights(
    disease, 
    region, 
    shouldPredict ? 1 : undefined
  );
  // Hook: recommendations list - only when shouldPredict is true
  const { recommendations, loading: recsLoading, error: recsError } = useRecommendations(
    { disease, region, year: Number(year) }, 
    shouldPredict ? 1 : undefined
  );
  // Hook: merged predicted vs actual series - only when shouldPredict is true
  const { series, liveOnly, loading: paLoading, error: paError } = usePredictedActual(
    { disease, region }, 
    shouldPredict ? 1 : undefined
  );
  // Hooks: map overlays - always load
  const { geojson: heatmap, loading: heatLoading } = useHeatmap(region, disease, 1);
  const { features: hotspots, loading: hotLoading } = useHotspots(disease, Number(year), 1);
  // Metrics (model vs regression vs alert) - always load
  const { data: metricsData, loading: metricsLoading, error: metricsError } = useModelMetrics({ disease });
  // Disease alerts - always load
  const { alerts: diseaseAlerts, loading: alertsLoading, error: alertsError } = useDiseaseAlerts(disease, region);
  
  // Validate alerts data structure
  const validAlerts = useMemo(() => {
    return (diseaseAlerts || []).filter((alert) => 
      alert && 
      alert.id && 
      alert.disease && 
      alert.region && 
      alert.severity && 
      ["warning", "alert", "emergency"].includes(alert.severity)
    );
  }, [diseaseAlerts]);
  // Reporting & downloads - always load
  const { artifacts, health, loading: reportsLoading, error: reportsError, refreshing, refreshOutput, refreshReports } = useReports(1);
  const [showHeatmap, setShowHeatmap] = useState(true);
  const [showHotspots, setShowHotspots] = useState(true);
  const [downloadError, setDownloadError] = useState<string | undefined>(undefined);
  
  // Track when prediction completes
  useEffect(() => {
    if (shouldPredict && !predLoading && !insightsLoading) {
      setIsPredicting(false);
      setHasPrediction(true);
    }
  }, [shouldPredict, predLoading, insightsLoading]);

  const diseaseOptions = useMemo<Disease[]>(() => {
    if (metaOptions.diseases?.length) {
      const normalized = metaOptions.diseases
        .map((d) => d.toLowerCase())
        .filter((d): d is Disease => fallbackDiseases.includes(d as Disease));
      return normalized.length ? normalized : fallbackDiseases;
    }
    return fallbackDiseases;
  }, [metaOptions.diseases]);

  useEffect(() => {
    if (diseaseOptions.length && !diseaseOptions.includes(disease)) {
      setDisease(diseaseOptions[0]);
    }
  }, [diseaseOptions, disease]);

  const regionOptions = useMemo(() => {
    const base = metaOptions.regions?.length ? metaOptions.regions : ["All"];
    return base.includes("All") ? base : ["All", ...base];
  }, [metaOptions.regions]);

  const yearOptions = useMemo(() => {
    if (metaOptions.years?.length) {
      return metaOptions.years.map((y) => String(y));
    }
    return [year];
  }, [metaOptions.years, year]);

  const predictRisk = () => {
    // Manually trigger prediction
    setIsPredicting(true);
    setHasPrediction(false);
    setShouldPredict(true);
  };

  // Use state variables for prediction status (not hook loading states)
  // isPredicting and hasPrediction are already defined above

  const formatNumber = (val?: number | null, digits = 2) =>
    typeof val === "number" && isFinite(val) ? val.toFixed(digits) : "—";
  const formatPercent = (val?: number | null, digits = 1) =>
    typeof val === "number" && isFinite(val) ? `${(val * 100).toFixed(digits)}%` : "—";
  const formatBytes = (size?: number) => {
    if (!size && size !== 0) return "—";
    if (size === 0) return "0 B";
    const units = ["B", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(size) / Math.log(1024));
    return `${(size / Math.pow(1024, i)).toFixed(1)} ${units[i]}`;
  };

  const lstmMetrics = metricsData?.model;
  const regressionMetrics = metricsData?.regression;
  const alertMetrics = metricsData?.alert;

  const compareRows = [
    { label: "MAE", lstm: formatNumber(lstmMetrics?.mae), baseline: formatNumber(regressionMetrics?.mae) },
    { label: "RMSE", lstm: formatNumber(lstmMetrics?.rmse), baseline: "—" },
    { label: "R²", lstm: formatNumber(lstmMetrics?.r2, 3), baseline: "—" },
  ];

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      {/* 🔹 Main Header */}
      <header className="mb-8">
        <div className="flex justify-between items-start">
          <div>
            <h1 className="text-3xl font-bold text-[#0d2544]">
              Outbreak Prediction System
            </h1>
            <p className="text-gray-600 text-sm mt-1">
              Monitor, analyze, and predict outbreak risks across Nigeria.
            </p>
          </div>
          {!predLoading && predSeries.length > 0 && (
            <div className="text-xs text-gray-500 text-right">
              <div>Last updated: {new Date().toLocaleTimeString()}</div>
              <div className="mt-1">
                Data points: {predSeries.length}
              </div>
            </div>
          )}
        </div>
        <div className="mt-4 grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="text-sm text-gray-600">Disease</label>
            <select
              value={disease}
              onChange={(e) => setDisease(e.target.value as Disease)}
              className="w-full border rounded-md px-3 py-2 mt-1 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              {diseaseOptions.map((d) => (
                <option key={d} value={d}>
                  {d.replace("-", " ").toUpperCase()}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="text-sm text-gray-600">Region</label>
            <select
              value={region === "All" ? "All Nigeria" : region}
              onChange={(e) => {
                const normalized = e.target.value === "All Nigeria" ? "All" : e.target.value;
                setRegion(normalized);
              }}
              className="w-full border rounded-md px-3 py-2 mt-1 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option>All Nigeria</option>
              {regionOptions.filter((r) => r !== "All").map((r) => (
                <option key={r} value={r}>
                  {r}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="text-sm text-gray-600">Year</label>
            <select
              value={year}
              onChange={(e) => setYear(e.target.value)}
              className="w-full border rounded-md px-3 py-2 mt-1"
            >
              {yearOptions.map((y) => (
                <option key={y} value={y}>
                  {y}
                </option>
              ))}
            </select>
          </div>
          <div className="flex items-end">
            <button
              onClick={predictRisk}
              disabled={isPredicting || !!yearError}
              className={`w-full ${isPredicting || yearError ? "bg-gray-400" : "bg-green-700 hover:bg-green-600"} text-white font-semibold py-2 rounded-md transition disabled:opacity-70`}
            >
              {isPredicting ? "Refreshing…" : yearError ? "Fix Year Input" : "Run Prediction"}
            </button>
          </div>
        </div>
        {optionsLoading && <p className="text-xs text-gray-500 mt-2">Loading metadata…</p>}
        {optionsError && <p className="text-xs text-red-500 mt-2">{optionsError}</p>}
      </header>

      {hasPrediction && (
        <>
          <SectionHeader title="Overview Metrics" />
          <div className="grid grid-cols-2 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
            <StatCard title="Latest Confirmed Cases" value={String(stats.latest ?? 0)} />
            <StatCard title="Average Weekly Cases" value={String(stats.average ?? 0)} />
            <StatCard title="Risk Level" value={risk?.level || "Unknown"} />
            <StatCard title="Confidence" value={`${risk ? risk.confidence : 0}%`} />
          </div>
        </>
      )}

      <SectionHeader title="Reporting & Downloads" />
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        <div className="lg:col-span-2 bg-white rounded-xl shadow p-4">
          <div className="flex items-center justify-between mb-3">
            <h2 className="font-semibold text-[#0d2544]">Model Artifacts</h2>
            <button
              onClick={refreshReports}
              disabled={refreshing}
              className={`text-sm px-3 py-1 rounded ${refreshing ? "bg-gray-300" : "bg-green-600 text-white"}`}
            >
              {refreshing ? "Refreshing…" : "Refresh Reports"}
            </button>
          </div>
          {reportsLoading ? (
            <p className="text-sm text-gray-500">Loading artifacts…</p>
          ) : reportsError ? (
            <p className="text-sm text-red-600">{reportsError}</p>
          ) : artifacts.length ? (
            <div className="overflow-x-auto">
              <table className="min-w-full text-sm">
                <thead>
                  <tr className="text-left text-gray-500">
                    <th className="py-2">Name</th>
                    <th className="py-2">Updated</th>
                    <th className="py-2">Size</th>
                    <th className="py-2" />
                  </tr>
                </thead>
                <tbody>
                  {artifacts.map((artifact) => (
                    <tr key={artifact.path} className="border-t">
                      <td className="py-2 pr-4">{artifact.name}</td>
                      <td className="py-2 pr-4 text-gray-600">
                        {artifact.updated_at ? new Date(artifact.updated_at * 1000).toLocaleString() : "—"}
                      </td>
                      <td className="py-2 pr-4 text-gray-600">{formatBytes(artifact.size_bytes)}</td>
                      <td className="py-2">
                        {artifact.exists ? (
                          <a
                            href={artifact.download_url}
                            className="text-green-700 hover:underline text-sm"
                            target="_blank"
                            rel="noreferrer"
                            onClick={(e) => {
                              // Handle download errors
                              fetch(artifact.download_url)
                                .then((res) => {
                                  if (!res.ok) {
                                    setDownloadError(`Failed to download ${artifact.name}: ${res.statusText}`);
                                    e.preventDefault();
                                  } else {
                                    setDownloadError(undefined);
                                  }
                                })
                                .catch((err) => {
                                  setDownloadError(`Failed to download ${artifact.name}: ${err.message}`);
                                  e.preventDefault();
                                });
                            }}
                          >
                            Download
                          </a>
                        ) : (
                          <span className="text-xs text-gray-400">Unavailable</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="text-sm text-gray-500">No generated artifacts yet.</p>
          )}
          {refreshOutput && (
            <pre className="mt-3 text-xs bg-gray-50 border border-gray-200 rounded p-2 whitespace-pre-wrap">
              {refreshOutput}
            </pre>
          )}
          {downloadError && (
            <div className="mt-3 text-xs bg-red-50 border border-red-200 rounded p-2 text-red-700">
              {downloadError}
            </div>
          )}
        </div>

        <div className="bg-white rounded-xl shadow p-4">
          <h2 className="font-semibold mb-3 text-[#0d2544]">Pipeline Health</h2>
          {reportsLoading ? (
            <p className="text-sm text-gray-500">Loading…</p>
          ) : (
            <div className="text-sm text-gray-700 space-y-2">
              <p>
                <span className="font-semibold">Status:</span> {health?.status ?? "Unknown"}
              </p>
              <p>
                <span className="font-semibold">Rows Used:</span> {health?.rows_used_for_eval ?? "—"}
              </p>
              <p>
                <span className="font-semibold">Overall MAE:</span> {formatNumber(health?.overall_mae)}
              </p>
              <p>
                <span className="font-semibold">Diseases:</span> {Array.isArray(health?.diseases) ? health?.diseases?.join(", ") : "—"}
              </p>
              <p className="text-xs text-gray-500">
                Last Updated: {health?.timestamp ? new Date(Number(health.timestamp) * 1000).toLocaleString() : "Unknown"}
              </p>
            </div>
          )}
        </div>
      </div>

      <SectionHeader title="Model Performance" />
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-8">
        <div className="bg-white rounded-xl shadow p-4">
          <h2 className="font-semibold mb-3 text-[#0d2544]">LSTM Validation</h2>
          {metricsLoading ? (
            <p className="text-sm text-gray-500">Loading metrics…</p>
          ) : metricsError ? (
            <p className="text-sm text-red-600">{metricsError}</p>
          ) : (
            <div className="grid grid-cols-3 gap-3">
              <StatCard title="MAE" value={formatNumber(lstmMetrics?.mae)} />
              <StatCard title="RMSE" value={formatNumber(lstmMetrics?.rmse)} />
              <StatCard title="R²" value={formatNumber(lstmMetrics?.r2, 3)} />
            </div>
          )}
        </div>
        <div className="bg-white rounded-xl shadow p-4">
          <h2 className="font-semibold mb-3 text-[#0d2544]">RandomForest Baseline</h2>
          {metricsLoading ? (
            <p className="text-sm text-gray-500">Loading metrics…</p>
          ) : (
            <div className="grid grid-cols-2 gap-3">
              <StatCard title="MAE" value={formatNumber(regressionMetrics?.mae)} />
              <StatCard title="Overall MAE" value={formatNumber(regressionMetrics?.overall_mae)} />
            </div>
          )}
        </div>
        <div className="bg-white rounded-xl shadow p-4">
          <h2 className="font-semibold mb-3 text-[#0d2544]">Alert Classification</h2>
          {metricsLoading ? (
            <p className="text-sm text-gray-500">Loading metrics…</p>
          ) : (
            <div className="grid grid-cols-3 gap-3">
              <StatCard title="Precision" value={formatPercent(alertMetrics?.precision)} />
              <StatCard title="Recall" value={formatPercent(alertMetrics?.recall)} />
              <StatCard title="F1" value={formatPercent(alertMetrics?.f1)} />
            </div>
          )}
        </div>
      </div>

      <div className="bg-white rounded-xl shadow p-4 mb-8">
        <h2 className="font-semibold mb-3 text-[#0d2544]">Compare Models</h2>
        <div className="overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead>
              <tr className="text-left text-gray-500">
                <th className="py-2">Metric</th>
                <th className="py-2">LSTM</th>
                <th className="py-2">RandomForest</th>
              </tr>
            </thead>
            <tbody>
              {compareRows.map((row) => (
                <tr key={row.label} className="border-t">
                  <td className="py-2 font-medium">{row.label}</td>
                  <td className="py-2">{row.lstm}</td>
                  <td className="py-2">{row.baseline}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

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
            {!heatLoading && !heatmap && (
              <div className="text-xs text-gray-500 mt-2">Heatmap unavailable — displaying base map only.</div>
            )}
            {!hotLoading && showHotspots && (!hotspots || hotspots.length === 0) && (
              <div className="text-xs text-gray-500">Hotspot data unavailable for this selection.</div>
            )}
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

      {/* Alert Probabilities Section */}
      {hasPrediction && (
        <>
      <SectionHeader title="Alert Probabilities by Region" />
      <div className="bg-white rounded-xl shadow p-4 mb-8">
        {alertsLoading ? (
          <p className="text-sm text-gray-500">Loading alerts…</p>
        ) : alertsError ? (
          <p className="text-sm text-red-600">Failed to load alerts: {alertsError}</p>
        ) : diseaseAlerts.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="text-left text-gray-500 border-b">
                  <th className="py-2">Region</th>
                  <th className="py-2">Severity</th>
                  <th className="py-2">Cases</th>
                  <th className="py-2">Trend</th>
                  <th className="py-2">Description</th>
                  <th className="py-2">Timestamp</th>
                </tr>
              </thead>
              <tbody>
                {validAlerts.map((alert) => (
                  <tr key={alert.id} className="border-t hover:bg-gray-50">
                    <td className="py-2 font-medium">{alert.region}</td>
                    <td className="py-2">
                      <span className={`px-2 py-1 rounded text-xs font-semibold ${
                        alert.severity === "emergency" ? "bg-red-100 text-red-700" :
                        alert.severity === "alert" ? "bg-orange-100 text-orange-700" :
                        "bg-yellow-100 text-yellow-700"
                      }`}>
                        {alert.severity.toUpperCase()}
                      </span>
                    </td>
                    <td className="py-2">{alert.details.cases}</td>
                    <td className="py-2">
                      <span className={`px-2 py-1 rounded text-xs ${
                        alert.details.trend === "increasing" ? "text-red-600" :
                        alert.details.trend === "decreasing" ? "text-green-600" :
                        "text-gray-600"
                      }`}>
                        {alert.details.trend}
                      </span>
                    </td>
                    <td className="py-2 text-gray-600">{alert.details.description}</td>
                    <td className="py-2 text-gray-500 text-xs">
                      {new Date(alert.timestamp).toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-sm text-gray-600">No active alerts for {disease} in {region}.</p>
        )}
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
                <label className="text-sm text-gray-600">
                  Year
                </label>
                <input
                  placeholder={String(new Date().getFullYear())}
                  type="number"
                  min="2006"
                  max={String(new Date().getFullYear() + 1)}
                  value={year}
                  onChange={(e) => {
                    const val = e.target.value;
                    setYear(val);
                    const validated = validateYear(val);
                    if (validated === null && val !== "") {
                      setYearError(`Year must be between 2006 and ${new Date().getFullYear() + 1}`);
                    } else {
                      setYearError(null);
                    }
                  }}
                  className={`w-full border rounded-md px-3 py-2 mt-1 ${yearError ? "border-red-500" : ""}`}
                />
                {yearError && <p className="text-xs text-red-600 mt-1">{yearError}</p>}
              </div>
              <div>
                <label className="text-sm text-gray-600">
                  Avg. Rainfall (mm)
                  <span className="text-xs text-gray-400 ml-1">(read-only)</span>
                </label>
                <input
                  placeholder="1250"
                  type="number"
                  min="0"
                  max="5000"
                  value={rainfall}
                  readOnly
                  className="w-full border rounded-md px-3 py-2 mt-1 bg-gray-50 cursor-not-allowed"
                  title="Climate data is automatically fetched from weather services. Manual input not available."
                />
              </div>
              <div>
                <label className="text-sm text-gray-600">
                  Avg. Temperature (°C)
                  <span className="text-xs text-gray-400 ml-1">(read-only)</span>
                </label>
                <input
                  placeholder="25"
                  type="number"
                  min="-10"
                  max="50"
                  value={temperature}
                  readOnly
                  className="w-full border rounded-md px-3 py-2 mt-1 bg-gray-50 cursor-not-allowed"
                  title="Climate data is automatically fetched from weather services. Manual input not available."
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
            {predError && (
              <p className="mt-2 text-sm text-red-600">{predError}</p>
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
