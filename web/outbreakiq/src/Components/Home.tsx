import { useEffect, useState, useRef } from "react";
import { Link } from "react-router-dom";
import Loader from "./Loader";
import { motion } from "framer-motion";
import gsap from "gsap";
import Footer from "./Footer";
import FAQ from "./FAQ";

const Home: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const titleRef = useRef<HTMLHeadingElement | null>(null);

  useEffect(() => {
    const t = setTimeout(() => setLoading(false), 1500);
    return () => clearTimeout(t);
  }, []);

  useEffect(() => {
    if (!loading && titleRef.current) {
      gsap.from(titleRef.current, { y: 20, opacity: 0, duration: 0.8 });
    }
  }, [loading]);

  if (loading) return <Loader />;

  return (
    <div className="space-y-12">
      <section
        className="grid md:grid-cols-2 gap-8 items-center"
        data-aos="fade-up"
      >
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
        >
          <div>
            <h2
              ref={titleRef}
              className="text-5xl font-extrabold text-slate-900 hero-title"
            >
              OutbreakIQ
            </h2>
            <p className="mt-4 text-lg text-slate-600">
              Predicting tomorrow's outbreaks, today. OutbreakIQ uses advanced
              data analytics and AI to forecast malaria and cholera risks in
              Nigeria, empowering public health officials with actionable
              insights for proactive interventions.
            </p>

            <div className="mt-6 flex flex-wrap gap-4">
              <Link
                to="/predictions"
                className="bg-emerald-400 text-slate-900 px-5 py-3 rounded-md font-semibold"
              >
                Start Prediction
              </Link>
              <Link
                to="/predictions"
                className="border border-slate-300 text-slate-900 px-5 py-3 rounded-md"
              >
                View Dashboard
              </Link>
            </div>
          </div>
        </motion.div>

        <div
          className="hidden md:block bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 rounded-lg h-80"
          data-aos="zoom-in"
        />
      </section>

      <section className="grid md:grid-cols-3 gap-6" data-aos="fade-up">
        <div className="bg-white shadow rounded-lg p-6">
          <h3 className="font-bold">10+ years</h3>
          <p className="text-sm text-slate-500">of data analyzed</p>
        </div>
        <div className="bg-white shadow rounded-lg p-6">
          <h3 className="font-bold">AI-powered</h3>
          <p className="text-sm text-slate-500">predictions</p>
        </div>
        <div className="bg-white shadow rounded-lg p-6">
          <h3 className="font-bold">Covering key regions</h3>
          <p className="text-sm text-slate-500">across Nigeria</p>
        </div>
      </section>
      <FAQ />
      <Footer />
    </div>
  );
};

export default Home;
