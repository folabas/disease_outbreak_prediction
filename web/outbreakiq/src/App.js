// NOTE: components folder is `Components` (capital C) in this repo
import { BrowserRouter as Router } from "react-router-dom";
import "./App.css";
// NOTE: project uses a `Components` folder with a capital C. Adjust imports to match filesystem.
import FAQ from "./Components/FAQ";
import Footer from "./Components/Footer";

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-[#F8F9FA] font-display text-[#212529]">
        {/* Hero Section with Nigeria Map Background */}
        <div className="relative min-h-[520px] flex items-center justify-center bg-cover bg-center bg-no-repeat">
          <div
            className="absolute inset-0 bg-no-repeat bg-center bg-contain opacity-5"
            style={{ backgroundImage: "url('/nigeria-map.svg')" }}
            aria-label="Faint vector map of Nigeria in the background"
          />
          <div className="relative z-10 text-center px-4 max-w-2xl mx-auto">
            <h1 className="text-4xl sm:text-5xl md:text-6xl font-black leading-tight tracking-tight mb-4">
              OutbreakIQ
            </h1>
            <h2 className="text-lg sm:text-xl md:text-2xl font-medium leading-normal mb-4">
              Predicting tomorrow's outbreaks, today.
            </h2>
            <p className="text-[#6C757D] text-base sm:text-lg font-normal leading-relaxed mb-8">
              Our platform uses advanced data analytics and AI to forecast
              malaria and cholera risks in Nigeria, empowering public health
              officials.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <button className="min-w-[160px] h-12 px-6 bg-[#212529] text-white font-bold rounded-lg">
                Start Prediction
              </button>
              <button className="min-w-[160px] h-12 px-6 bg-transparent text-[#212529] font-bold border-2 border-[#212529] rounded-lg">
                View Dashboard
              </button>
            </div>
          </div>
        </div>

        {/* Stats Section */}
        <div className="py-10">
          <div className="max-w-6xl mx-auto px-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
              <div className="flex flex-col items-center text-center p-6 bg-white rounded-lg border border-gray-200">
                <span className="material-symbols-outlined text-4xl text-[#6C757D]">
                  database
                </span>
                <p className="text-lg font-bold mt-2">10+ Years</p>
                <p className="text-[#6C757D]">of Data Analyzed</p>
              </div>
              <div className="flex flex-col items-center text-center p-6 bg-white rounded-lg border border-gray-200">
                <span className="material-symbols-outlined text-4xl text-[#6C757D]">
                  model_training
                </span>
                <p className="text-lg font-bold mt-2">AI-Powered</p>
                <p className="text-[#6C757D]">Predictions</p>
              </div>
              <div className="flex flex-col items-center text-center p-6 bg-white rounded-lg border border-gray-200">
                <span className="material-symbols-outlined text-4xl text-[#6C757D]">
                  verified
                </span>
                <p className="text-lg font-bold mt-2">High Accuracy</p>
                <p className="text-[#6C757D]">Prediction Impact</p>
              </div>
            </div>
          </div>
        </div>

        {/* FAQ Section */}
        <FAQ />

        {/* Footer */}
        <Footer />
      </div>
    </Router>
  );
}

export default App;
