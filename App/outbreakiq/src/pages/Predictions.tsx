import { useState, useEffect } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";
import { MapContainer, TileLayer, CircleMarker, Circle } from "react-leaflet";
import { motion } from "framer-motion";
import Loader from "../Components/Loader";

/* -----------------------------------------
   PREDICTIONS PAGE
------------------------------------------ */
const Predictions = () => {
  const [disease, setDisease] = useState("Cholera"); // FIXED DEFAULT
  const [region, setRegion] = useState("All");
  const [year, setYear] = useState("2025");
  const [rainfall, setRainfall] = useState("");
  const [temperature, setTemperature] = useState("");
  const [isLoading, setIsLoading] = useState(true);

  const [riskResult, setRiskResult] = useState({
    level: "",
    explanation: "",
    recommendations: [],
    confidence: 0,
  });

  const [mapColor, setMapColor] = useState("transparent");
  const [heatIntensity, setHeatIntensity] = useState(0.2);

  /* Loading */
  useEffect(() => {
    setIsLoading(true);
    const timer = setTimeout(() => setIsLoading(false), 1500);
    return () => clearTimeout(timer);
  }, []);

  const sampleData = [
    { name: "Jan", value: 40 },
    { name: "Feb", value: 50 },
    { name: "Mar", value: 60 },
    { name: "Apr", value: 80 },
    { name: "May", value: 120 },
    { name: "Jun", value: 140 },
  ];

  /* Color helpers */
  const colorForLevel = (lvl) => {
    if (!lvl) return "gray";
    if (lvl === "High") return "#e53e3e";
    if (lvl === "Medium") return "#d69e2e";
    if (lvl === "Low") return "#2f855a";
    return "gray";
  };

  const confidenceForLevel = (lvl) => {
    if (lvl === "High") return 86;
    if (lvl === "Medium") return 65.5;
    if (lvl === "Low") return 35.5;
    return 0;
  };

  /* Heatmap points across Nigeria */
  const heatPoints = [
    { id: "northwest", coords: [12.0, 8.5] },
    { id: "northeast", coords: [11.5, 12.0] },
    { id: "northcentral", coords: [9.5, 8.5] },
    { id: "west", coords: [7.5, 4.0] },
    { id: "southwest", coords: [6.5, 3.333] },
    { id: "southeast", coords: [6.0, 8.0] },
    { id: "southsouth", coords: [5.0, 6.833] },
    { id: "lagos", coords: [6.5244, 3.3792] },
    { id: "rivers", coords: [4.8156, 7.0498] },
    { id: "kano", coords: [12.0022, 8.5919] },
    { id: "abuja", coords: [9.0765, 7.3986] },
  ];

  /* -----------------------------------------
     FILE-BASED PREDICTION LOGIC
  ------------------------------------------ */
  const predictRisk = () => {
    const rain = Number(rainfall);
    const temp = Number(temperature);

    if (isNaN(rain) || isNaN(temp)) {
      alert("Enter valid rainfall & temperature values.");
      return;
    }

    let level = "";
    let explanation = "";
    let recommendations = [];

    /* ----------------- CHOLERA ----------------- */
    if (disease === "Cholera") {
      if (rain < 600 && temp < 28) {
        level = "Low";
        explanation =
          "Low rainfall and cooler temperatures reduce water contamination.";
        recommendations = [
          "Maintain basic water sanitation.",
          "Cover wells and boreholes.",
          "Monitor water sources closely.",
        ];
      } else if (rain >= 600 && rain <= 1500 && temp >= 28 && temp <= 30) {
        level = "Medium";
        explanation =
          "Moderate rainfall supports contamination but not extreme flooding.";
        recommendations = [
          "Increase chlorination.",
          "Improve drainage.",
          "Hygiene awareness campaigns.",
        ];
      } else if (rain > 1500 && temp > 30) {
        level = "High";
        explanation =
          "Heavy rainfall + warm temperatures increase Vibrio growth.";
        recommendations = [
          "Deploy water purification.",
          "Avoid untreated water.",
          "Increase diagnostic testing.",
        ];
      }
    }

    /* ----------------- MALARIA ----------------- */
    if (disease === "Malaria") {
      if (rain < 400 || temp < 20 || temp > 34) {
        level = "Low";
        explanation = "Climate unsuitable for mosquito breeding.";
        recommendations = [
          "Clear standing water.",
          "Maintain basic mosquito control.",
        ];
      } else if (rain >= 400 && rain <= 1200 && temp >= 20 && temp <= 28) {
        level = "Medium";
        explanation = "Climate supports moderate mosquito reproduction.";
        recommendations = [
          "IRS spraying programs.",
          "Use mosquito nets.",
          "Remove stagnant water.",
        ];
      } else if (rain > 1200 && temp >= 28 && temp <= 32) {
        level = "High";
        explanation = "Optimal mosquito breeding conditions.";
        recommendations = [
          "Mass distribution of nets.",
          "Environmental cleanup.",
          "Antimalarial availability.",
        ];
      }
    }

    /* ----------------- LASSA ----------------- */
    if (disease === "Lassa Fever") {
      if (rain < 300 || temp < 24 || temp > 34) {
        level = "Low";
        explanation = "Rodent population low due to unsuitable climate.";
        recommendations = ["Seal houses.", "Use rodent-proof food containers."];
      } else if (rain >= 300 && rain <= 1000 && temp >= 24 && temp <= 30) {
        level = "Medium";
        explanation = "Climate supports moderate rodent activity.";
        recommendations = [
          "Improve sanitation.",
          "Educate households.",
          "Proper food storage.",
        ];
      } else if (rain > 1000 && rain <= 1500 && temp >= 30 && temp <= 33) {
        level = "High";
        explanation = "High rodent activity increases transmission risk.";
        recommendations = [
          "Strengthen rodent control.",
          "Improve waste management.",
          "Prepare hospitals.",
        ];
      }
    }

    /* ----------------- EBOLA ----------------- */
    if (disease === "Ebola") {
      if (rain < 600 || temp < 24 || temp > 33) {
        level = "Low";
        explanation = "Climate not ideal for bat reservoir activity.";
        recommendations = ["Maintain surveillance.", "Border health checks."];
      } else if (rain >= 600 && rain <= 1500 && temp >= 24 && temp <= 30) {
        level = "Medium";
        explanation = "Moderate bat-human ecological suitability.";
        recommendations = [
          "Educate communities on bushmeat risks.",
          "Improve PPE availability.",
        ];
      } else if (rain > 1500 && temp >= 27 && temp <= 30) {
        level = "High";
        explanation = "High bat reservoir suitability.";
        recommendations = [
          "Limit bushmeat hunting.",
          "Strengthen emergency response.",
          "Ensure PPE for health workers.",
        ];
      }
    }

    /* ----------------- COVID ----------------- */
    if (disease === "Covid 19") {
      if (temp > 32) {
        level = "Low";
        explanation =
          "Hot temperatures slightly reduce viral survival outdoors.";
        recommendations = ["Maintain hygiene.", "Improve ventilation."];
      } else if (temp >= 24 && temp <= 32) {
        level = "Medium";
        explanation = "Climate supports respiratory virus transmission.";
        recommendations = [
          "Ventilate indoor spaces.",
          "Encourage hand hygiene.",
        ];
      } else if (temp < 24) {
        level = "High";
        explanation =
          "Cool temperatures increase viral stability and indoor crowding.";
        recommendations = [
          "Limit indoor gatherings.",
          "Encourage mask use.",
          "Boost vaccination campaigns.",
        ];
      }
    }

    /* -----------------------------------------
       FALLBACK (Option A):
       If no rule matched, default to MEDIUM
    ------------------------------------------ */
    if (!level) {
      level = "Medium";
      explanation =
        "Climate conditions produce mixed signals. Monitor closely.";
      recommendations = [
        "Increase local surveillance.",
        "Promote hygiene awareness.",
        "Monitor climate data regularly.",
      ];
    }

    /* Apply Colors + Heat */
    const confidence = confidenceForLevel(level);
    const color = colorForLevel(level);

    const intensityMap = { Low: 0.25, Medium: 0.6, High: 1.0 };
    const intensity = intensityMap[level] ?? 0.6;

    setRiskResult({ level, explanation, recommendations, confidence });
    setMapColor(color);
    setHeatIntensity(intensity);
  };

  if (isLoading) return <Loader />;

  /* -----------------------------------------
     JSX Interface (unchanged UI, added effects only)
  ------------------------------------------ */
  return (
    <div className="min-h-screen bg-gray-50 p-6">
      {/* Header */}
      <header className="mb-8">
        <h1 className="text-3xl font-bold text-[#0d2544]">
          Prediction Dashboard
        </h1>
        <p className="text-gray-600 text-sm mt-1">
          Monitor, analyze, and predict outbreak risks across Nigeria.
        </p>

        <div className="flex flex-wrap gap-3 mt-4">
          <select
            value={disease}
            onChange={(e) => setDisease(e.target.value)}
            className="border rounded-md px-3 py-2 text-sm"
          >
            <option>Cholera</option>
            <option>Malaria</option>
            <option>Lassa Fever</option>
            <option>Ebola</option>
            <option>Covid 19</option>
          </select>

          <select
            value={region}
            onChange={(e) => setRegion(e.target.value)}
            className="border rounded-md px-3 py-2 text-sm"
          >
            <option>All</option>
            <option>North-East</option>
            <option>North-West</option>
            <option>North-Central</option>
            <option>South-East</option>
            <option>South-West</option>
            <option>South-South</option>
          </select>

          <select
            value={year}
            onChange={(e) => setYear(e.target.value)}
            className="border rounded-md px-3 py-2 text-sm"
          >
            <option>2023</option>
            <option>2024</option>
            <option>2025</option>
          </select>
        </div>
      </header>

      {/* Metrics */}
      <SectionHeader title="Overview Metrics" />
      <div className="grid grid-cols-2 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <StatCard title="Average Rainfall" value="1200 mm" />
        <StatCard title="Average Temperature" value="28°C" />
        <StatCard title="Population Density" value="212/km²" />
        <StatCard title="Hospital Capacity" value="5 beds/10k" />
      </div>

      {/* Map + Chart */}
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

              {/* Full-country tint (Option A) */}
              <Circle
                center={[9.082, 8.6753]}
                radius={1000000}
                pathOptions={{
                  color: mapColor,
                  fillColor: mapColor,
                  fillOpacity: 0.06 * heatIntensity + 0.04,
                  weight: 0,
                }}
              />

              {/* Heatmap simulation */}
              {heatPoints.map((p, i) => (
                <CircleMarker
                  key={p.id}
                  center={p.coords}
                  radius={6 + heatIntensity * 10}
                  pathOptions={{
                    color: mapColor,
                    fillColor: mapColor,
                    fillOpacity: 0.2 * heatIntensity + 0.05,
                    weight: 0,
                  }}
                />
              ))}
            </MapContainer>
          </div>
        </div>

        {/* Chart */}
        <div className="bg-white rounded-xl shadow p-4">
          <h2 className="font-semibold mb-3 text-[#0d2544]">
            Predicted vs Actual Cases
          </h2>
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={sampleData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Line
                type="monotone"
                dataKey="value"
                stroke="#2f855a"
                strokeWidth={3}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Insights */}
      <SectionHeader title="Outbreak Insights" />
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        <div className="lg:col-span-2 bg-white rounded-xl shadow p-4">
          <h2 className="font-semibold mb-3 text-[#0d2544]">Insight Summary</h2>
          <p className="text-gray-700 text-sm mb-3">
            For climate and disease relationships, environmental factors
            affect risk levels. Higher rainfall and temperatures often correlate
            with increased outbreak risks for vector-borne and waterborne
            diseases. Regions with dense populations and limited healthcare
            infrastructure face higher risk levels. <br />
           <br /> Based on current climate and population data, there is a moderately
            elevated risk of a Cholera outbreak in the North-Eastern regions
            over the next quarter. Increased rainfall and high population
            density are the primary contributing factors. Proactive measures in
            sanitation and public health awareness are recommended to mitigate
            potential spread.
          </p>
        </div>

        <div className="bg-white rounded-xl shadow p-4 flex flex-col items-center">
          <h2 className="font-semibold mb-3 text-[#0d2544]">
            Key Risk Factors
          </h2>
          <img
            src="/Risk Factors.jpeg"
            alt="Risk Factors"
            className="rounded-lg"
          />
        </div>
      </div>

      {/* Prediction Form + Results */}
      <SectionHeader title="Run New Prediction" />
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* FORM */}
        <div className="bg-white rounded-xl shadow p-6">
          <h2 className="font-semibold mb-4 text-[#0d2544]">
            Run a New Prediction
          </h2>

          <div className="space-y-3">
            <div className="grid grid-cols-2 gap-3">
              {/* Disease */}
              <div>
                <label className="text-sm text-gray-600">Disease</label>
                <select
                  name="disease"
                  value={disease}
                  onChange={(e) => setDisease(e.target.value)}
                  className="w-full border rounded-md px-3 py-2 mt-1"
                >
                  <option>Cholera</option>
                  <option>Malaria</option>
                  <option>Lassa Fever</option>
                  <option>Ebola</option>
                  <option>Covid 19</option>
                </select>
              </div>

              {/* Region */}
              <div>
                <label className="text-sm text-gray-600">Region</label>
                <select
                  name="region"
                  value={region}
                  onChange={(e) => setRegion(e.target.value)}
                  className="w-full border rounded-md px-3 py-2 mt-1"
                >
                  <option>All</option>
                  <option>North-East</option>
                  <option>North-West</option>
                  <option>North-Central</option>
                  <option>South-East</option>
                  <option>South-West</option>
                  <option>South-South</option>
                </select>
              </div>
            </div>

            {/* Rainfall / Temperature */}
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-sm text-gray-600">
                  Avg. Rainfall (mm)
                </label>
                <input
                  type="number"
                  placeholder="1200"
                  value={rainfall}
                  onChange={(e) => setRainfall(e.target.value)}
                  className="w-full border rounded-md px-3 py-2 mt-1"
                />
              </div>

              <div>
                <label className="text-sm text-gray-600">
                  Avg. Temperature (°C)
                </label>
                <input
                  type="number"
                  placeholder="28"
                  value={temperature}
                  onChange={(e) => setTemperature(e.target.value)}
                  className="w-full border rounded-md px-3 py-2 mt-1"
                />
              </div>
            </div>

            <button
              onClick={predictRisk}
              className="w-full mt-4 bg-green-700 text-white font-semibold py-2 rounded-md hover:bg-green-600"
            >
              Predict Risk
            </button>
          </div>
        </div>

        {/* RESULT CARD (animated) */}
        <motion.div
          key={riskResult.level + riskResult.confidence}
          initial={{ opacity: 0, scale: 0.95, y: 8 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          transition={{ type: "spring", stiffness: 180, damping: 18 }}
          className="bg-white rounded-xl shadow p-6"
        >
          <h2 className="font-semibold mb-4 text-[#0d2544]">
            Prediction Result
          </h2>

          <div className="text-center">
            <p className="text-gray-500 text-sm mb-1">Predicted Risk Level</p>
            <h3
              className={`text-3xl font-bold ${
                riskResult.level === "High"
                  ? "text-red-600"
                  : riskResult.level === "Medium"
                  ? "text-yellow-400"
                  : riskResult.level === "Low"
                  ? "text-green-700"
                  : ""
              }`}
            >
              {riskResult.level || "—"}
            </h3>

            <p className="mt-2 text-gray-600 text-sm">
              Confidence Score: {riskResult.confidence}%
            </p>

            <p className="mt-3 text-gray-700 text-sm italic">
              {riskResult.explanation}
            </p>
          </div>

          {/* Recommendations */}
          <div className="mt-5">
            <h4 className="font-semibold text-gray-800 text-sm mb-2">
              Preventive Recommendations:
            </h4>
            <ul className="list-disc list-inside text-gray-600 text-sm space-y-1">
              {riskResult.recommendations.length ? (
                riskResult.recommendations.map((rec, index) => (
                  <li key={index}>{rec}</li>
                ))
              ) : (
                <li>Run a prediction to see recommendations.</li>
              )}
            </ul>
          </div>
        </motion.div>
      </div>

      <footer className="pt-6 text-center text-gray-500 text-sm">
        © 2025 OutbreakIQ. All rights reserved.
      </footer>
    </div>
  );
};

/* -----------------------------------------
   REUSABLE COMPONENTS
------------------------------------------ */
const StatCard = ({ title, value }) => (
  <div className="bg-white rounded-xl shadow p-4">
    <p className="text-sm text-gray-500">{title}</p>
    <h3 className="text-2xl font-bold text-gray-800 mt-1">{value}</h3>
  </div>
);

const SectionHeader = ({ title }) => (
  <h2 className="text-lg font-semibold text-[#0d2544] mb-3 mt-6 border-l-4 border-green-600 pl-3">
    {title}
  </h2>
);

export default Predictions;
