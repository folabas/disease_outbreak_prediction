import { useState, useEffect } from "react";
import { NavLink } from "react-router-dom";
import Sidebar from "./Sidebar";

interface NavbarProps {
  isOpen?: boolean;
  isMobile?: boolean;
  onClose?: () => void;
}

const Navbar = ({ isOpen, isMobile, onClose }: NavbarProps) => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 20);
    };
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  const handleSidebarToggle = () => setSidebarOpen(!sidebarOpen);
  const handleSidebarClose = () => setSidebarOpen(false);

  const navigationItems = [
    { name: "Home", path: "/" },
    { name: "Predictions", path: "/predictions" },
    { name: "Climate", path: "/climate" },
    { name: "Population", path: "/population" },
    { name: "Hospital", path: "/hospital" },
    { name: "Insights", path: "/insights" },
  ];

  return (
    <>
      {/* Floating Pill Navbar Wrapper */}
      <div className="fixed top-0 left-0 right-0 z-50 flex justify-center mt-6 px-4 transition-all duration-300">
        <nav className={`w-full max-w-5xl rounded-full transition-all duration-300 border border-white/10 ${
          scrolled ? "bg-[#0D2544]/90 backdrop-blur-md shadow-[0_8px_30px_rgb(0,0,0,0.12)]" : "bg-white/10 backdrop-blur-md shadow-sm"
        }`}>
          <div className="px-6 lg:px-8">
            <div className="flex justify-between items-center h-16">
              {/* Logo */}
              <div className="flex-shrink-0 flex items-center">
                <img
                  src="/Clean logo.png"
                  alt="OutbreakIQ Logo"
                  className="h-8 w-auto"
                />
                <span className={`text-xl font-bold tracking-tight px-3 transition-colors ${scrolled ? "text-white" : "text-white"}`}>
                  Outbreak<span className="text-green-600">IQ</span>
                </span>
              </div>

              {/* Desktop navigation (Centered) */}
              <div className="hidden md:flex justify-center flex-1">
                <div className="flex space-x-6">
                  {navigationItems.map((item) => (
                    <NavLink
                      key={item.name}
                      to={item.path}
                      className={({ isActive }) =>
                        `inline-flex items-center px-3 py-2 text-sm font-medium transition-all duration-200 rounded-full ${
                          isActive
                            ? "bg-green-600 text-white"
                            : "text-gray-200 hover:bg-white/20"
                        }`
                      }
                    >
                      {item.name}
                    </NavLink>
                  ))}
                </div>
              </div>

              {/* Empty div for balancing flex layout on desktop if needed, or keeping it clean */}
              <div className="hidden md:block w-24"></div>

              {/* Mobile menu button */}
              <div className="md:hidden">
                <button
                  type="button"
                  onClick={handleSidebarToggle}
                  className="inline-flex items-center justify-center p-2 rounded-full text-white hover:bg-white/20 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-green-600 transition-colors"
                >
                  <span className="sr-only">Open main menu</span>
                  <svg
                    className="block h-6 w-6"
                    xmlns="http://www.w3.org/2000/svg"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    aria-hidden="true"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M4 6h16M4 12h16M4 18h16"
                    />
                  </svg>
                </button>
              </div>
            </div>
          </div>
        </nav>
      </div>

      {/* Sidebar overlay for mobile */}
      {sidebarOpen && (
        <div className="fixed inset-0 z-[60] flex md:hidden">
          {/* Background overlay */}
          <div
            className="fixed inset-0 bg-black bg-opacity-50 backdrop-blur-sm"
            onClick={handleSidebarClose}
          ></div>

          {/* Sidebar itself */}
          <Sidebar
            isOpen={sidebarOpen}
            isMobile={true}
            onClose={handleSidebarClose}
          />
        </div>
      )}
    </>
  );
};

export default Navbar;
