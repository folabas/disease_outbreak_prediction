import { useState, useEffect } from "react";
import DataPageTemplate from "../Components/DataPageTemplate";
import Loader from "../Components/Loader";

const Climate = () => {
  const [timeRange, setTimeRange] = useState("7d");
  const [region, setRegion] = useState("All");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const timer = setTimeout(() => {
      setLoading(false);
    }, 2000);

    return () => clearTimeout(timer);
  }, []);

  const filters = (
    <>
      <select
        title="region"
        value={region}
        onChange={(e) => setRegion(e.target.value)}
        className="form-select block w-full sm:w-48 rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
      >
        <option>All Regions</option>
        <option>North</option>
        <option>South</option>
        <option>East</option>
        <option>West</option>
      </select>

      <div className="inline-flex rounded-md shadow-sm">
        {["24h", "7d", "30d", "90d"].map((range) => (
          <button
            key={range}
            onClick={() => setTimeRange(range)}
            className={`px-4 py-2 text-sm font-medium ${
              timeRange === range
                ? "bg-blue-600 text-white"
                : "bg-white text-gray-700 hover:bg-gray-50"
            } ${
              range === "24h"
                ? "rounded-l-md"
                : range === "90d"
                ? "rounded-r-md"
                : ""
            } border border-gray-300`}
          >
            {range}
          </button>
        ))}
      </div>
    </>
  );

  const stats = [
    {
      name: "Average Temperature",
      value: "32°C",
      change: "+2.5°C",
      changeType: "increase",
    },
    {
      name: "Rainfall",
      value: "120mm",
      change: "-15mm",
      changeType: "decrease",
    },
    { name: "Humidity", value: "65%", change: "+5%", changeType: "increase" },
  ];

  return loading ? (
    <Loader />
  ) : (
    <DataPageTemplate
      title="Climate Data Analysis"
      description="Monitor and analyze climate patterns and their impact on disease outbreaks."
      filters={filters}
    >
      {/* Stats Grid */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3 mb-6">
        {stats.map((stat) => (
          <div
            key={stat.name}
            className="bg-white overflow-hidden shadow rounded-lg"
          >
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-1">
                  <p className="text-sm font-medium text-gray-500 truncate">
                    {stat.name}
                  </p>
                  <p className="mt-1 text-3xl font-semibold text-gray-900">
                    {stat.value}
                  </p>
                </div>
                <div
                  className={`flex items-center ${
                    stat.changeType === "increase"
                      ? "text-green-600"
                      : "text-red-600"
                  }`}
                >
                  {stat.changeType === "increase" ? (
                    <svg
                      className="w-5 h-5"
                      fill="currentColor"
                      viewBox="0 0 20 20"
                    >
                      <path
                        fillRule="evenodd"
                        d="M5.293 9.707a1 1 0 010-1.414l4-4a1 1 0 011.414 0l4 4a1 1 0 01-1.414 1.414L11 7.414V15a1 1 0 11-2 0V7.414L6.707 9.707a1 1 0 01-1.414 0z"
                        clipRule="evenodd"
                      />
                    </svg>
                  ) : (
                    <svg
                      className="w-5 h-5"
                      fill="currentColor"
                      viewBox="0 0 20 20"
                    >
                      <path
                        fillRule="evenodd"
                        d="M14.707 10.293a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 111.414-1.414L9 12.586V5a1 1 0 012 0v7.586l2.293-2.293a1 1 0 011.414 0z"
                        clipRule="evenodd"
                      />
                    </svg>
                  )}
                  <span className="ml-1 text-sm font-medium">
                    {stat.change}
                  </span>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 gap-6">
        {/* Temperature Chart */}
        <div className="bg-white shadow rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">
            Temperature Trends
          </h3>
          <div className="aspect-w-16 aspect-h-9 bg-gray-100 rounded-lg">
            {/* Add temperature chart component here */}
            <div className="flex items-center justify-center h-full text-gray-500">
              Temperature Chart Placeholder
            </div>
          </div>
        </div>

        {/* Rainfall Chart */}
        <div className="bg-white shadow rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">
            Rainfall Analysis
          </h3>
          <div className="aspect-w-16 aspect-h-9 bg-gray-100 rounded-lg">
            {/* Add rainfall chart component here */}
            <div className="flex items-center justify-center h-full text-gray-500">
              Rainfall Chart Placeholder
            </div>
          </div>
        </div>

        {/* Climate Map */}
        <div className="bg-white shadow rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">
            Regional Climate Map
          </h3>
          <div className="aspect-w-16 aspect-h-9 bg-gray-100 rounded-lg">
            {/* Add climate map component here */}
            <div className="flex items-center justify-center h-full text-gray-500">
              Climate Map Placeholder
            </div>
          </div>
        </div>
      </div>
    </DataPageTemplate>
  );
};

export default Climate;
