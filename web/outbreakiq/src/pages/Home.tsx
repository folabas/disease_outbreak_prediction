import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import Loader from "../Components/Loader";
import FAQ from "../Components/FAQ";

const Home = () => {
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const timer = setTimeout(() => {
      setLoading(false);
    }, 2000);

    return () => clearTimeout(timer);
  }, []);

  return loading ? (
    <Loader />
  ) : (
    <div className="min-h-screen">
      {/* Hero Section */}
      <div className="relative overflow-hidden">
        <div className="max-w-7xl mx-auto">
          <div className="relative z-10 pb-8 sm:pb-16 md:pb-20 lg:w-full lg:pb-28 xl:pb-32">
            <div className="pt-10 mx-auto max-w-7xl px-4 sm:pt-12 sm:px-6 md:pt-16 lg:pt-20 lg:px-8 xl:pt-28">
              <div className="sm:text-center lg:text-left">
                <h1 className="text-4xl tracking-tight font-extrabold text-gray-900 sm:text-5xl md:text-6xl">
                  <span className="block">Predict and Prevent</span>
                  <span className="block text-blue-600">Disease Outbreaks</span>
                </h1>
                <p className="mt-3 text-base text-gray-500 sm:mt-5 sm:text-lg sm:max-w-xl sm:mx-auto md:mt-5 md:text-xl lg:mx-0">
                  Advanced AI-powered disease outbreak prediction and monitoring
                  system. Stay ahead of potential health crises with real-time
                  data analysis and actionable insights.
                </p>
                <div className="mt-5 sm:mt-8 sm:flex sm:justify-center lg:justify-start">
                  <div className="rounded-md shadow">
                    <Link
                      to="/predictions"
                      className="w-full flex items-center justify-center px-8 py-3 border border-transparent text-base font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 md:py-4 md:text-lg md:px-10"
                    >
                      View Predictions
                    </Link>
                  </div>
                  <div className="mt-3 sm:mt-0 sm:ml-3">
                    <Link
                      to="/insights"
                      className="w-full flex items-center justify-center px-8 py-3 border border-transparent text-base font-medium rounded-md text-blue-700 bg-blue-100 hover:bg-blue-200 md:py-4 md:text-lg md:px-10"
                    >
                      View Insights
                    </Link>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Hero Image */}
        <div className="hidden lg:block lg:absolute lg:inset-y-0 lg:right-0 lg:w-1/2">
          <div className="relative h-full">
            <div className="absolute inset-0 bg-gradient-to-br from-blue-50 to-indigo-100 opacity-70"></div>
            <img
              src="/flier.png"
              alt="Disease Outbreak Prevention"
              className="absolute inset-0 w-full h-full object-cover object-center"
            />
            <div className="absolute inset-0 bg-gradient-to-r from-white via-white/80 to-transparent"></div>
          </div>
        </div>
      </div>

      {/* Feature Cards Section */}
      <div className="py-12 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="mt-10">
            <div className="grid grid-cols-1 gap-8 sm:grid-cols-2 lg:grid-cols-3">
              {/* Card 1 */}
              <div className="bg-white overflow-hidden shadow rounded-lg border border-gray-200">
                <div className="p-5">
                  <div className="flex items-center">
                    <div className="flex-shrink-0">
                      <svg
                        className="h-6 w-6 text-blue-600"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth="2"
                          d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
                        />
                      </svg>
                    </div>
                    <div className="ml-5">
                      <h3 className="text-lg font-medium text-gray-900">
                        Real-time Monitoring
                      </h3>
                      <p className="mt-2 text-sm text-gray-500">
                        Track disease outbreaks and health metrics in real-time
                        across different regions.
                      </p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Card 2 */}
              <div className="bg-white overflow-hidden shadow rounded-lg border border-gray-200">
                <div className="p-5">
                  <div className="flex items-center">
                    <div className="flex-shrink-0">
                      <svg
                        className="h-6 w-6 text-blue-600"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth="2"
                          d="M13 10V3L4 14h7v7l9-11h-7z"
                        />
                      </svg>
                    </div>
                    <div className="ml-5">
                      <h3 className="text-lg font-medium text-gray-900">
                        Predictive Analytics
                      </h3>
                      <p className="mt-2 text-sm text-gray-500">
                        AI-powered predictions to identify potential outbreak
                        hotspots before they occur.
                      </p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Card 3 */}
              <div className="bg-white overflow-hidden shadow rounded-lg border border-gray-200">
                <div className="p-5">
                  <div className="flex items-center">
                    <div className="flex-shrink-0">
                      <svg
                        className="h-6 w-6 text-blue-600"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth="2"
                          d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                        />
                      </svg>
                    </div>
                    <div className="ml-5">
                      <h3 className="text-lg font-medium text-gray-900">
                        Data Insights
                      </h3>
                      <p className="mt-2 text-sm text-gray-500">
                        Comprehensive analytics and visualizations for informed
                        decision-making.
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* FAQ Section */}
        <FAQ />
    </div>
  );
};

export default Home;
