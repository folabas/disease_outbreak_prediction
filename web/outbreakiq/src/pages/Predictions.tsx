import { useState, useEffect } from "react";
import { useDashboardStore } from "../store/useDashboardStore";
import Loader from "../Components/Loader";

const Predictions = () => {
  const [selectedRegion, setSelectedRegion] = useState("All Regions");
  const [timeRange, setTimeRange] = useState("7d");
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Simulate data loading when region or time range changes
    setIsLoading(true);
    const timer = setTimeout(() => {
      setIsLoading(false);
    }, 1500);
    return () => clearTimeout(timer);
  }, [selectedRegion, timeRange]);

  // Mock data - replace with actual data from your store
  const stats = [
    {
      name: "Risk Level",
      value: "High",
      change: "+2.5%",
      changeType: "increase",
    },
    {
      name: "Affected Areas",
      value: "12",
      change: "+4",
      changeType: "increase",
    },
    {
      name: "Population at Risk",
      value: "2.1M",
      change: "+12%",
      changeType: "increase",
    },
    {
      name: "Prediction Confidence",
      value: "89%",
      change: "+1.2%",
      changeType: "increase",
    },
  ];

  if (isLoading) {
    return <Loader />;
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow">
        <div className="py-6 px-4 sm:px-6 lg:px-8">
          <h1 className="text-2xl font-semibold text-gray-900">
            Outbreak Predictions Dashboard
          </h1>
        </div>
      </div>

      {/* Filters */}
      <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col space-y-3 sm:flex-row sm:space-y-0 sm:space-x-4">
          <select
            title="selectedregion"
            value={selectedRegion}
            onChange={(e) => setSelectedRegion(e.target.value)}
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
        </div>
      </div>

      {/* Stats Grid */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
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

        {/* Map and Charts Section */}
        <div className="mt-8 grid grid-cols-1 gap-8 lg:grid-cols-2">
          {/* Risk Map */}
          <div className="bg-white rounded-lg shadow">
            <div className="p-6">
              <h3 className="text-lg font-medium text-gray-900">Risk Map</h3>
              <div className="mt-4 aspect-w-16 aspect-h-9 bg-gray-100 rounded-lg">
                {/* Add your map component here */}
                <div className="flex items-center justify-center h-full text-gray-500">
                  Map Placeholder
                </div>
              </div>
            </div>
          </div>

          {/* Trend Chart */}
          <div className="bg-white rounded-lg shadow">
            <div className="p-6">
              <h3 className="text-lg font-medium text-gray-900">
                Outbreak Trend
              </h3>
              <div className="mt-4 aspect-w-16 aspect-h-9 bg-gray-100 rounded-lg">
                {/* Add your chart component here */}
                <div className="flex items-center justify-center h-full text-gray-500">
                  Chart Placeholder
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Predictions;
