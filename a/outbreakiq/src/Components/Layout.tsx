import { useState, useEffect } from "react";
import { Outlet, useLocation } from "react-router-dom";
import Sidebar from "./Sidebar";
import Navbar from "../Components/Navbar";
import Footer from "./Footer";

const Layout = () => {
  const location = useLocation();
  const isHomePage = location.pathname === "/";
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [isMobile, setIsMobile] = useState(window.innerWidth < 1024);

  useEffect(() => {
    const handleResize = () => {
      setIsMobile(window.innerWidth < 1024);
      if (window.innerWidth >= 1024) {
        setIsMobileMenuOpen(false);
      }
    };

    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  const toggleMobileMenu = () => {
    setIsMobileMenuOpen(!isMobileMenuOpen);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {isHomePage ? (
        <div className="flex flex-col min-h-screen">
          <Navbar />
          <main>
            <Outlet />
          </main>
        </div>
      ) : (
        <div className="flex min-h-screen">
          <div className="fixed inset-y-0 left-0 z-40">
            {/* Sticky Pill Header for Mobile Subpages */}
            {isMobile && (
              <div className="fixed top-4 left-4 right-4 z-50 flex items-center justify-between bg-white/90 backdrop-blur-md px-5 py-3 rounded-full shadow-[0_4px_20px_rgb(0,0,0,0.08)] border border-gray-100 transition-all">
                <div className="flex items-center">
                  <img src="/Clean logo.png" alt="OutbreakIQ Logo" className="h-6 w-auto" />
                  <span className="text-lg font-bold tracking-tight text-[#0D2544] px-2">
                    Outbreak<span className="text-green-600">IQ</span>
                  </span>
                </div>
                <button
                  onClick={toggleMobileMenu}
                  className="p-1.5 rounded-full text-gray-700 hover:bg-gray-100 focus:outline-none transition-colors"
                  aria-label="Toggle menu"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    {isMobileMenuOpen ? (
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    ) : (
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                    )}
                  </svg>
                </button>
              </div>
            )}

            <Sidebar
              isOpen={!isMobile || isMobileMenuOpen}
              isMobile={isMobile}
              onClose={() => setIsMobileMenuOpen(false)}
            />

            {/* Mobile Menu Backdrop */}
            {isMobile && isMobileMenuOpen && (
              <div
                className="fixed inset-0 bg-black bg-opacity-50 z-30 backdrop-blur-sm"
                onClick={() => setIsMobileMenuOpen(false)}
                aria-hidden="true"
              />
            )}
          </div>

          {/* Main Content with proper sidebar spacing */}
          <div className="flex-1 flex flex-col min-h-screen md:ml-64">
            <main className="flex-1 px-4 pt-24 pb-8 md:px-6 lg:px-8 md:pt-8">
              <Outlet />
            </main>
          </div>
        </div>
      )}
    </div>
  );
};

export default Layout;
