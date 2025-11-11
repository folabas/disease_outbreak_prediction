import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import FAQ from "../Components/FAQ";
import Footer from "../Components/Footer";

const Home = () => {
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const timer = setTimeout(() => setLoading(false), 2000);
    return () => clearTimeout(timer);
  }, []);

  if (loading) return <HomeSkeleton />;

  return (
    <div className="min-h-screen bg-[#0D2544]">
      {/* Hero Section */}
      <div className="relative overflow-hidden bg-[#0D2544]">
        <div className="max-w-7xl mx-auto">
          <div className="relative z-10 pb-8 sm:pb-16 md:pb-20 lg:w-full lg:pb-28 xl:pb-32">
            <div className="pt-10 mx-auto max-w-7xl px-4 sm:pt-12 sm:px-6 md:pt-16 lg:pt-20 lg:px-8 xl:pt-28">
              <div className="sm:text-center lg:text-left">
                <h1 className="text-4xl font-black text-white sm:text-5xl lg:text-7xl py-8">
                  Outbreak<span className="text-green-700">IQ</span>
                </h1>
                <h2 className="text-xl font-bold text-gray-300 sm:text-2xl">
                  Predicting tomorrow's outbreaks, today.
                </h2>
                <p className="mt-3 text-base text-gray-400 sm:mt-5 sm:text-lg sm:max-w-xl sm:mx-auto md:mt-5 md:text-xl lg:mx-0">
                  OutbreakIQ uses advanced data analytics and AI to forecast
                  malaria and cholera risks in Nigeria, empowering public health
                  officials with actionable insights for proactive
                  interventions.
                </p>

                <div className="mt-5 sm:mt-8 sm:flex sm:justify-center lg:justify-start">
                  <div className="rounded-md shadow">
                    <Link
                      to="/predictions"
                      className="w-full flex items-center justify-center px-8 py-3 border border-transparent text-base font-medium rounded-md text-white bg-green-700 hover:bg-transparent hover:text-green-700 hover:border-green-700 md:py-4 md:text-lg md:px-10"
                    >
                      Start Predictions
                    </Link>
                  </div>
                  <div className="mt-3 sm:mt-0 sm:ml-3">
                    <Link
                      to="/insights"
                      className="w-full flex items-center justify-center px-8 py-3 border border-green-700 text-base font-medium rounded-md text-green-700 hover:bg-green-700 hover:text-blue-100 md:py-4 md:text-lg md:px-10"
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
        <div className="hidden lg:block lg:absolute lg:inset-y-0 lg:right-0 lg:w-1/2 bg-[#0d2544]">
          <div className="relative h-full">
            <img
              src="/New Backdrop.png"
              alt="Disease Outbreak Prevention"
              className="absolute inset-0 w-full h-full object-cover object-center"
            />
            <div className="absolute inset-0 bg-gradient-to-b from-[#0d2544] to-transparent"></div>
          </div>
        </div>
      </div>

      {/* Feature Cards Section */}
      <div className="py-16 px-4 lg:px-20 bg-gray-300 font-bold">
        <div className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
          <div>
            <h2 className="text-3xl font-bold text-[#0d2544] mb-4">
              Empowering Nigeria with Predictive Health Insights
            </h2>
            <p className="text-lg text-gray-500 mt-8">
              OutbreakIQ uses advanced data analytics and AI to forecast Malaria
              and Cholera risks in Nigeria. Our platform empowers public health
              officials with actionable insights for proactive interventions.
            </p>
            <h1 className="text-9xl py-5 mx-28">🌍</h1>
          </div>

          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-1">
            {/* Cards */}
            <FeatureCard
              icon="⚡"
              title="Real-time Monitoring"
              text="Track disease outbreaks and health metrics in real-time across regions."
            />
            <FeatureCard
              icon="📈"
              title="Predictive Analytics"
              text="AI-powered predictions to identify potential outbreak hotspots before they occur."
            />
            <FeatureCard
              icon="📊"
              title="Data Insights"
              text="Comprehensive analytics and visualizations for informed decision-making."
            />
            <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-2">
              <FeatureCard
                icon="📆"
                title="10+ years"
                text="of data analysed"
              />
              <FeatureCard
                icon="📍"
                title="Covering Key Regions"
                text="Across Nigeria"
              />
            </div>
          </div>
        </div>
      </div>

      {/* FAQ Section */}
      <FAQ />
      <Footer />
    </div>
  );
};

/* Feature Card Component */
const FeatureCard = ({ icon, title, text }) => (
  <div className="bg-gray-200 overflow-hidden shadow rounded-lg border border-green-700">
    <div className="p-4">
      <div className="flex items-center">
        <div className="flex-shrink-0 text-3xl text-green-700">{icon}</div>
        <div className="ml-5">
          <h3 className="text-lg font-medium text-gray-900">{title}</h3>
          <p className="mt-2 text-sm text-gray-500">{text}</p>
        </div>
      </div>
    </div>
  </div>
);

/* 🔹 Skeleton Loader Component */
const HomeSkeleton = () => (
  <div className="min-h-screen bg-[#0D2544] text-white">
    {/* Hero Skeleton */}
    <div className="max-w-7xl mx-auto px-6 pt-20">
      <div className="space-y-5">
        <div className="h-12 bg-gray-700 rounded w-2/3"></div>
        <div className="h-6 bg-gray-600 rounded w-1/2"></div>
        <div className="h-4 bg-gray-600 rounded w-5/6"></div>
        <div className="h-4 bg-gray-600 rounded w-3/4"></div>
        <div className="flex gap-3 pt-6">
          <div className="h-10 bg-green-700 rounded-md w-40"></div>
          <div className="h-10 bg-gray-500 rounded-md w-40"></div>
        </div>
      </div>
    </div>

    {/* Hero Image Placeholder */}
    <div className="hidden lg:block absolute right-0 top-0 w-1/2 h-[600px] bg-gray-800 opacity-40"></div>

    {/* Features Section Skeleton */}
    <div className="py-16 px-4 lg:px-20 bg-gray-300 text-gray-900 mt-10">
      <div className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-2 gap-12">
        <div className="space-y-5">
          <div className="h-10 bg-gray-400 rounded w-2/3"></div>
          <div className="h-4 bg-gray-400 rounded w-5/6"></div>
          <div className="h-4 bg-gray-400 rounded w-4/5"></div>
          <div className="h-40 bg-gray-200 rounded mt-10"></div>
        </div>

        <div className="space-y-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="h-24 bg-gray-200 rounded-lg shadow"></div>
          ))}
        </div>
      </div>
    </div>

    {/* FAQ + Footer placeholders */}
    <div className="bg-gray-100 py-10 px-6">
      <div className="h-6 bg-gray-300 rounded w-1/3 mx-auto mb-4"></div>
      <div className="h-4 bg-gray-300 rounded w-2/3 mx-auto mb-2"></div>
      <div className="h-4 bg-gray-300 rounded w-1/2 mx-auto"></div>
    </div>

    <div className="bg-gray-200 py-6 text-center">
      <div className="h-4 bg-gray-400 rounded w-1/4 mx-auto"></div>
    </div>
  </div>
);

export default Home;
