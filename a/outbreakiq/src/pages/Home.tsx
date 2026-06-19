import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { 
  FiGlobe as _FiGlobe, FiZap as _FiZap, FiTrendingUp as _FiTrendingUp, FiBarChart2 as _FiBarChart2, FiCalendar as _FiCalendar, FiMapPin as _FiMapPin, 
  FiArrowRight as _FiArrowRight, FiDatabase as _FiDatabase, FiCpu as _FiCpu, FiPieChart as _FiPieChart, FiActivity as _FiActivity, FiUsers as _FiUsers, FiBox as _FiBox
} from "react-icons/fi";

const FiGlobe = _FiGlobe as any;
const FiZap = _FiZap as any;
const FiTrendingUp = _FiTrendingUp as any;
const FiBarChart2 = _FiBarChart2 as any;
const FiCalendar = _FiCalendar as any;
const FiMapPin = _FiMapPin as any;
const FiArrowRight = _FiArrowRight as any;
const FiDatabase = _FiDatabase as any;
const FiCpu = _FiCpu as any;
const FiPieChart = _FiPieChart as any;
const FiActivity = _FiActivity as any;
const FiUsers = _FiUsers as any;
const FiBox = _FiBox as any;
import FAQ from "../Components/FAQ";
import Footer from "../Components/Footer";
import ScrollStack from "../Components/ScrollStack";

const Home = () => {
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const timer = setTimeout(() => setLoading(false), 2000);
    return () => clearTimeout(timer);
  }, []);

  if (loading) return <HomeSkeleton />;

  return (
    <div className="min-h-screen bg-[#0D2544] ">
      {/* Centered Hero Section with Full Bleed Background */}
      <div className="relative min-h-screen lg:min-h-[90vh] flex items-center justify-center overflow-hidden bg-[#0D2544]">
        {/* Background Image & Overlay */}
        <div className="absolute inset-0 z-0">
          <img
            src="/New Backdrop.png"
            alt="Disease Outbreak Prevention"
            className="w-full h-full object-cover object-center opacity-40"
          />
          <div className="absolute inset-0 bg-gradient-to-b from-[#0d2544]/80 via-[#0d2544]/60 to-[#0D2544]"></div>
          {/* Grey Background Grid */}
          <div className="absolute inset-0 opacity-20 pointer-events-none" style={{ backgroundImage: 'linear-gradient(to right, #808080 1px, transparent 1px), linear-gradient(to bottom, #808080 1px, transparent 1px)', backgroundSize: '60px 60px' }}></div>
        </div>

        {/* Hero Content */}
        <div className="relative z-10 w-full max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 text-center pt-32 pb-24 lg:pt-40 lg:pb-32">
          <h1 className="text-5xl md:text-7xl lg:text-8xl tracking-tight font-black text-white py-6 drop-shadow-lg">
            Outbreak<span className="text-green-600">IQ</span>
          </h1>
          <h2 className="text-2xl md:text-3xl lg:text-4xl font-bold text-gray-200 mb-6 drop-shadow-md">
            Predicting tomorrow's outbreaks, today.
          </h2>
          <p className="mt-4 text-base sm:text-lg md:text-xl text-gray-300 max-w-3xl mx-auto leading-relaxed">
            OutbreakIQ uses advanced data analytics and AI to forecast
            disease outbreak risks (cholera, malaria, ebola, COVID-19) in Nigeria, empowering public health
            officials with actionable insights for proactive interventions.
          </p>

          <div className="mt-10 flex flex-col sm:flex-row justify-center items-center gap-4 sm:gap-6">
            <Link
              to="/predictions"
              className="w-full sm:w-auto flex items-center justify-center px-10 py-4 text-lg font-bold rounded-full text-white bg-green-600 hover:bg-green-500 hover:-translate-y-1 transition-all duration-300 shadow-[0_0_20px_rgba(22,163,74,0.4)]"
            >
              Start Predictions <FiArrowRight className="ml-2" />
            </Link>
            <Link
              to="/insights"
              className="w-full sm:w-auto flex items-center justify-center px-10 py-4 border-2 border-gray-400 text-lg font-bold rounded-full text-white hover:border-green-600 hover:text-green-600 transition-colors duration-300 backdrop-blur-sm bg-black/20"
            >
              View Insights
            </Link>
          </div>
        </div>
      </div>

      {/* Feature Cards Section (Empowering Nigeria) */}
      <div className="py-20 lg:py-32 bg-gray-50 relative overflow-hidden">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
            {/* Left side text */}
            <div className="text-center lg:text-left">
              <h2 className="text-4xl md:text-5xl font-black text-[#0d2544] mb-6">
                Empowering Nigeria with Predictive Health Insights
              </h2>
              <p className="text-lg text-gray-600 font-medium leading-relaxed mb-10">
                OutbreakIQ uses advanced data analytics and AI to forecast disease outbreak risks
                in Nigeria. Our platform empowers public health officials with actionable insights for proactive interventions.
              </p>
              <div className="text-green-600 opacity-20 hidden lg:block">
                <FiGlobe className="w-48 h-48 animate-pulse" />
              </div>
            </div>
            
            {/* Right side cards (Scroll Stack for Mobile) */}
            <ScrollStack 
              desktopClasses="md:grid md:grid-cols-2 md:gap-6 md:overflow-visible md:pb-0 md:mx-0 md:px-0"
              childClasses="md:w-auto md:pr-0"
            >
              <FeatureCard
                icon={<FiZap />}
                title="Real-time Monitoring"
                text="Track disease outbreaks and health metrics in real-time across regions."
              />
              <FeatureCard
                icon={<FiTrendingUp />}
                title="Predictive Analytics"
                text="AI-powered predictions to identify potential outbreak hotspots before they occur."
              />
              <FeatureCard
                icon={<FiBarChart2 />}
                title="Data Insights"
                text="Comprehensive analytics and visualizations for informed decision-making."
              />
              <div className="grid grid-rows-2 gap-4 h-full">
                <FeatureCard
                  icon={<FiCalendar />}
                  title="10+ years"
                  text="of data analysed"
                  compact
                />
                <FeatureCard
                  icon={<FiMapPin />}
                  title="Key Regions"
                  text="Covered across Nigeria"
                  compact
                />
              </div>
            </ScrollStack>
          </div>
        </div>
      </div>

      {/* How It Works Section */}
      <div className="py-20 bg-white border-b border-gray-100">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-black text-[#0d2544]">How It Works</h2>
            <p className="mt-4 text-lg text-gray-500 max-w-2xl mx-auto">From raw data to actionable intelligence in three simple steps.</p>
          </div>
          
          {/* Scroll Stack for Mobile */}
          <ScrollStack 
            desktopClasses="md:grid md:grid-cols-3 md:gap-10 md:overflow-visible md:pb-0 md:mx-0 md:px-0 text-center relative z-10"
            childClasses="md:w-auto md:pr-0"
          >
              <div className="p-8 rounded-3xl bg-gray-50 border border-gray-100 shadow-xl h-full">
                <div className="w-16 h-16 mx-auto text-blue-600 flex items-center justify-center mb-6">
                  <FiDatabase className="w-10 h-10" />
                </div>
                <h3 className="text-2xl font-bold text-gray-900 mb-3">1. Data Aggregation</h3>
                <p className="text-gray-600 text-lg">We continuously collect epidemiological, environmental, and demographic data from trusted sources across Nigeria.</p>
              </div>
              <div className="p-8 rounded-3xl bg-gray-50 border border-gray-100 shadow-xl h-full">
                <div className="w-16 h-16 mx-auto text-green-600 flex items-center justify-center mb-6">
                  <FiCpu className="w-10 h-10" />
                </div>
                <h3 className="text-2xl font-bold text-gray-900 mb-3">2. AI Processing</h3>
                <p className="text-gray-600 text-lg">Our machine learning models analyze historical patterns and current variables to calculate outbreak probabilities.</p>
              </div>
              <div className="p-8 rounded-3xl bg-gray-50 border border-gray-100 shadow-xl h-full">
                <div className="w-16 h-16 mx-auto text-purple-600 flex items-center justify-center mb-6">
                  <FiPieChart className="w-10 h-10" />
                </div>
                <h3 className="text-2xl font-bold text-gray-900 mb-3">3. Actionable Insights</h3>
                <p className="text-gray-600 text-lg">Health officials receive clear, visualized forecasts to proactively allocate resources and deploy interventions.</p>
              </div>
          </ScrollStack>
        </div>
      </div>

      {/* New & Upcoming Features Section */}
      <div className="py-20 bg-[#f4f7f6]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-black text-[#0d2544]">Platform Capabilities</h2>
            <p className="mt-4 text-lg text-gray-500 max-w-2xl mx-auto">Expanding our toolkit to tackle public health challenges head-on.</p>
          </div>
          
          {/* Scroll Stack for Mobile */}
          <ScrollStack 
            desktopClasses="md:grid md:grid-cols-3 md:gap-8 md:overflow-visible md:pb-0 md:mx-0 md:px-0"
            childClasses="md:w-auto md:pr-0"
          >
               <div className="bg-white p-8 rounded-2xl shadow-xl border border-gray-100 h-full">
                  <div className="text-orange-500 mb-6"><FiActivity className="w-10 h-10" /></div>
                  <h3 className="text-xl font-bold text-gray-900 mb-3">Crowdsourced Reporting <span className="block mt-2 sm:inline sm:mt-0 text-xs bg-green-100 text-green-800 px-2 py-1 rounded-full w-max">Coming Soon</span></h3>
                  <p className="text-gray-600 text-lg">Empowering local clinic workers to report unusual symptom clusters for real-time early warnings.</p>
               </div>
               <div className="bg-white p-8 rounded-2xl shadow-xl border border-gray-100 h-full">
                  <div className="text-indigo-500 mb-6"><FiUsers className="w-10 h-10" /></div>
                  <h3 className="text-xl font-bold text-gray-900 mb-3">Vulnerability Heatmaps <span className="block mt-2 sm:inline sm:mt-0 text-xs bg-green-100 text-green-800 px-2 py-1 rounded-full w-max">Coming Soon</span></h3>
                  <p className="text-gray-600 text-lg">Overlaying predictions with social vulnerability data (clean water access, population density) to prioritize care.</p>
               </div>
               <div className="bg-white p-8 rounded-2xl shadow-xl border border-gray-100 h-full">
                  <div className="text-rose-500 mb-6"><FiBox className="w-10 h-10" /></div>
                  <h3 className="text-xl font-bold text-gray-900 mb-3">Resource Allocation <span className="block mt-2 sm:inline sm:mt-0 text-xs bg-green-100 text-green-800 px-2 py-1 rounded-full w-max">Coming Soon</span></h3>
                  <p className="text-gray-600 text-lg">Estimating required medical supplies (vaccines, beds) based on the predicted severity of an outbreak.</p>
               </div>
          </ScrollStack>
        </div>
      </div>

      {/* CTA Section */}
      <div className="bg-green-600">
        <div className="max-w-7xl mx-auto py-16 px-4 sm:px-6 lg:py-20 lg:px-8 lg:flex lg:items-center lg:justify-between">
          <h2 className="text-3xl font-black tracking-tight text-white sm:text-4xl text-center lg:text-left">
            <span className="block">Ready to make data-driven decisions?</span>
            <span className="block text-green-100 font-medium text-2xl mt-2">Explore outbreak predictions today.</span>
          </h2>
          <div className="mt-8 flex justify-center lg:mt-0 lg:flex-shrink-0">
            <Link
              to="/predictions"
              className="inline-flex items-center justify-center px-10 py-5 border border-transparent text-xl font-bold rounded-full text-green-700 bg-white hover:bg-gray-50 transition-colors shadow-xl"
            >
              Start Exploring
            </Link>
          </div>
        </div>
      </div>

      {/* FAQ Section */}
      <FAQ />
      <Footer />

      {/* Global Style for hiding scrollbar but allowing scroll */}
      <style>{`
        .hide-scrollbar::-webkit-scrollbar {
          display: none;
        }
        .hide-scrollbar {
          -ms-overflow-style: none;
          scrollbar-width: none;
        }
      `}</style>
    </div>
  );
};

/* Feature Card Component */
type FeatureCardProps = {
  icon: React.ReactNode;
  title: string;
  text: string;
  compact?: boolean;
};

const FeatureCard: React.FC<FeatureCardProps> = ({ icon, title, text, compact = false }) => (
  <div className="bg-white overflow-hidden shadow-xl hover:shadow-2xl transition-shadow duration-300 rounded-2xl border border-gray-100 h-full flex flex-col justify-center">
    <div className={`p-6 ${compact ? 'py-4' : ''} flex flex-col items-center text-center h-full`}>
      {/* Background removed, only text color kept */}
      <div className={`text-green-600 mb-4 ${compact ? 'text-3xl' : 'text-5xl'}`}>
        {icon}
      </div>
      <h3 className={`font-bold text-gray-900 mb-2 ${compact ? 'text-lg' : 'text-2xl'}`}>{title}</h3>
      <p className="text-base text-gray-500 leading-relaxed">{text}</p>
    </div>
  </div>
);

/* 🔹 Skeleton Loader Component */
const HomeSkeleton = () => (
  <div className="min-h-screen bg-[#0D2544] text-white flex flex-col">
    {/* Centered Hero Skeleton */}
    <div className="flex-1 flex flex-col items-center justify-center text-center pt-20 pb-16 px-6 relative z-10">
      <div className="space-y-6 w-full max-w-4xl flex flex-col items-center">
        <div className="h-20 bg-gray-700 rounded-xl w-3/4 animate-pulse"></div>
        <div className="h-10 bg-gray-600 rounded-lg w-2/3 animate-pulse"></div>
        <div className="h-6 bg-gray-600 rounded w-full max-w-2xl animate-pulse"></div>
        <div className="h-6 bg-gray-600 rounded w-4/5 animate-pulse"></div>
        
        <div className="flex flex-col sm:flex-row gap-4 pt-10 w-full justify-center">
          <div className="h-14 bg-green-600/50 rounded-full w-full sm:w-56 animate-pulse"></div>
          <div className="h-14 border-2 border-gray-500 rounded-full w-full sm:w-56 animate-pulse"></div>
        </div>
      </div>
    </div>

    {/* Horizontal Scroll Features Skeleton */}
    <div className="py-20 bg-gray-50 w-full">
      <div className="max-w-7xl mx-auto px-4">
        <div className="h-12 bg-gray-300 rounded-lg w-64 mx-auto mb-6 animate-pulse"></div>
        <div className="h-6 bg-gray-300 rounded w-full max-w-md mx-auto mb-12 animate-pulse"></div>
        <div className="flex gap-4 overflow-x-hidden pb-4">
           {Array.from({ length: 4 }).map((_, i) => (
             <div key={i} className="h-64 w-[85vw] sm:w-72 bg-gray-200 rounded-2xl flex-shrink-0 animate-pulse"></div>
           ))}
        </div>
      </div>
    </div>
  </div>
);

export default Home;
