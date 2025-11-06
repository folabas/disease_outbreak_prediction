import React from "react";
import { Routes, Route, Link } from "react-router-dom";
import Home from "./Components/Home";
import Predictions from "./Components/Predictions";
import Climate from "./Components/Climate";
import Population from "./Components/Population";
import Hospital from "./Components/Hospital";
import Insights from "./Components/Insights";
// icons available via react-icons when needed

const App: React.FC = () => {
  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <header className="bg-gradient-to-r from-slate-900 via-slate-800 to-slate-900 text-white">
        <div className="max-w-7xl mx-auto px-4 py-6 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="bg-emerald-400 w-10 h-10 rounded-md flex items-center justify-center font-bold">
              IQ
            </div>
            <h1 className="text-2xl font-extrabold tracking-tight">
              OutbreakIQ
            </h1>
          </div>
          <nav className="hidden md:flex items-center space-x-6">
            <Link to="/" className="hover:underline">
              Home
            </Link>
            <Link to="/predictions" className="hover:underline">
              Dashboard
            </Link>
            <Link to="/climate" className="hover:underline">
              Climate
            </Link>
            <Link to="/population" className="hover:underline">
              Population
            </Link>
            <Link to="/hospital" className="hover:underline">
              Hospital
            </Link>
            <Link to="/insights" className="hover:underline">
              Model
            </Link>
          </nav>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-8">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/predictions" element={<Predictions />} />
          <Route path="/climate" element={<Climate />} />
          <Route path="/population" element={<Population />} />
          <Route path="/hospital" element={<Hospital />} />
          <Route path="/insights" element={<Insights />} />
        </Routes>
      </main>
    </div>
  );
};

export default App;
