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
import { MapContainer, TileLayer } from "react-leaflet";
import Loader from "../Components/Loader";
import { usePageAnimations } from "../hooks/usePageAnimations";


const Dashboard = () => {
  const [disease, setDisease] = useState("");
  const [region, setRegion] = useState("");
  const [year, setYear] = useState("");
  const [rainfall, setRainfall] = useState();
  const [temperature, setTemperature] = useState();
  const [isLoading, setIsLoading] = useState(true);
  const [riskResult, setRiskResult] = useState({
    level: " ",
    confidence: 0,
  });

  useEffect(() => {
    // Simulate loading time for dashboard
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

  const predictRisk = () => {
    const RainNorm = Math.min(Math.max(rainfall / 2000, 0), 1);
    const TempNorm = Math.min(Math.max((temperature - 10)/30, 0), 1);
    
    const Result = ( (0.6 * RainNorm) + (0.4 * TempNorm ));  
    if (Result <= 20){
      setRiskResult({ level: "High", confidence: 35.5 });
    }
    else if (Result >20 && Result <= 50){
      setRiskResult({ level: "Mid", confidence: 65.5 });
    }
    else{
      setRiskResult({ level: "Low" , confidence: 86 });
    }
    console.log("Prediction Successful")
  };

  if (isLoading) {
    return <Loader />;
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      {/* 🔹 Main Header */}
      <header className="mb-8">
        <h1 className="text-3xl font-bold text-[#0d2544]">
          Prediction Dashboard
        </h1>
        <p className="text-gray-600 text-sm mt-1">
          Monitor, analyze, and predict outbreak risks across Nigeria.
        </p>

        <div className="flex flex-wrap gap-3 mt-4">
          <select
            title="disease"
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
            title="region"
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
            title="year"
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

      {/* 🔹 Overview Section */}
      <SectionHeader title="Overview Metrics" />
      <div className="grid grid-cols-2 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <StatCard title="Average Rainfall" value="1200 mm" />
        <StatCard title="Average Temperature" value="28°C" />
        <StatCard title="Population Density" value="212/km²" />
        <StatCard title="Hospital Capacity" value="5 beds/10k" />
      </div>

      {/* 🔹 Map & Chart Section */}
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
            </MapContainer>
          </div>
        </div>

        {/* Predicted vs Actual Chart */}
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

      {/* 🔹 Insights Section */}
      <SectionHeader title="Outbreak Insights" />
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        <div className="lg:col-span-2 bg-white rounded-xl shadow p-4">
          <h2 className="font-semibold mb-3 text-[#0d2544]">Insight Summary</h2>
          <p className="text-gray-700 text-sm leading-relaxed">
            Based on current climate and population data, there is a moderately
            elevated risk of a Cholera outbreak in the North-Eastern regions
            over the next quarter. Increased rainfall and high population
            density are the primary contributing factors. Proactive measures in
            sanitation and public health awareness are recommended to mitigate
            potential spread.
          </p>
        </div>

        <div className="bg-white rounded-xl shadow p-4 flex flex-col items-center justify-center">
          <h2 className="font-semibold mb-3 text-[#0d2544]">
            Key Risk Factors
          </h2>
          <img
            src="/Risk Factors.jpeg"
            alt="Risk Factors Chart"
            className="rounded-lg"
          />
        </div>
      </div>

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
              <div>
                <label className="text-sm text-gray-600">Region</label>
                <select
                  title="region"
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

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-sm text-gray-600">
                  Avg. Rainfall (mm)
                </label>
                <input
                  placeholder="1200"
                  type="number"
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
                  placeholder="28"
                  type="number"
                  value={temperature}
                  onChange={(e) => setTemperature(e.target.value)}
                  className="w-full border rounded-md px-3 py-2 mt-1"
                />
              </div>
            </div>

            <button
              onClick={predictRisk}
              className="w-full mt-4 bg-green-700 text-white font-semibold py-2 rounded-md hover:bg-green-600 transition"
            >
              Predict Risk
            </button>
          </div>
        </div>

        {/* Prediction Result */}
        <div className="bg-white rounded-xl shadow p-6">
          <h2 className="font-semibold mb-4 text-[#0d2544]">
            Prediction Result
          </h2>
          <div className="text-center">
            <p className="text-gray-500 text-sm mb-1">Predicted Risk Level</p>
            <h3
              className={`text-3xl font-bold ${
                riskResult.level === "High" 
                ? "text-red-600" 
                : riskResult.level === "Mid" 
                ? "text-yellow-300" 
                : riskResult.level === "Low" 
                ? "text-green-700"
                : " "
              }`}
            >
              {riskResult.level}
            </h3>
            <p className="mt-2 text-gray-600 text-sm">
              Confidence Score:{" "}
              <span className="font-semibold">{riskResult.confidence}%</span>
            </p>
          </div>

          <div className="mt-5">
            <h4 className="font-semibold text-gray-800 text-sm mb-2">
              Preventive Recommendations:
            </h4>
            <ul className="list-disc list-inside text-gray-600 text-sm space-y-1">
              <li>Deploy rapid response teams to high-risk areas.</li>
              <li>Increase public awareness campaigns on hygiene.</li>
              <li>Stockpile necessary medical supplies.</li>
            </ul>
          </div>
        </div>
      </div>
      {/* Footer */}
      <footer className="pt-6 text-center text-gray-500 text-sm">
        © 2025 OutbreakIQ. All rights reserved.
      </footer>
    </div>
  );
};

/* 🔸 Reusable Components */
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

export default Dashboard;
