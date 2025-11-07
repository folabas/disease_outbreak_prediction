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
          <main className="flex-1">
            <Outlet />
          </main>
          <Footer />
        </div>
      ) : (
        <div className="flex min-h-screen">
          <div className="fixed inset-y-0 left-0 z-40">
            {/* Mobile Menu Button */}
            {isMobile && (
              <button
                onClick={toggleMobileMenu}
                className="fixed top-4 left-4 z-50 p-2 rounded-md bg-white shadow-lg hover:bg-gray-50 focus:outline-none"
                aria-label="Toggle menu"
              >
                <svg
                  className="w-6 h-6 text-gray-600"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  {isMobileMenuOpen ? (
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M6 18L18 6M6 6l12 12"
                    />
                  ) : (
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M4 6h16M4 12h16M4 18h16"
                    />
                  )}
                </svg>
              </button>
            )}

            <Sidebar
              isOpen={!isMobile || isMobileMenuOpen}
              isMobile={isMobile}
              onClose={() => setIsMobileMenuOpen(false)}
            />

            {/* Mobile Menu Backdrop */}
            {isMobile && isMobileMenuOpen && (
              <div
                className="fixed inset-0 bg-black bg-opacity-50 z-30"
                onClick={() => setIsMobileMenuOpen(false)}
                aria-hidden="true"
              />
            )}
          </div>

          {/* Main Content with proper sidebar spacing */}
          <div className="flex-1 flex flex-col min-h-screen md:ml-64">
            <main className="flex-1 px-4 py-8 md:px-6 lg:px-8">
              <Outlet />
            </main>
            <Footer />
          </div>
        </div>
      )}
    </div>
  );
};

export default Layout;
