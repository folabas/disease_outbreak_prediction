import { useState } from "react";
import { NavLink } from "react-router-dom";
import Sidebar from "./Sidebar";

interface NavbarProps {
  isOpen: boolean;
  isMobile: boolean;
  onClose: () => void;
}

const Navbar = ({ isOpen, isMobile, onClose }: NavbarProps) => {
  const [sidebarOpen, setSidebarOpen] = useState(false);

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
      {/* Navbar */}
      <nav className="bg-[#0D2544] shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            {/* Logo */}
            <div className="flex-shrink-0 flex items-center">
              <img
                src="/Clean logo.png"
                alt="OutbreakIQ Logo"
                className="h-10 w-auto"
              />
              <span className="text-xl font-bold tracking-tight text-white px-3">
                OutbreakIQ
              </span>
            </div>

            {/* Desktop navigation */}
            <div className="hidden md:flex justify-center flex-1">
              <div className="flex space-x-8">
                {navigationItems.map((item) => (
                  <NavLink
                    key={item.name}
                    to={item.path}
                    className={({ isActive }) =>
                      `inline-flex items-center text-white px-1 pt-1 text-sm font-medium border-b-2 ${
                        isActive
                          ? "border-green-700 text-green-700"
                          : "border-transparent text-gray-400 hover:border-green-700 hover:text-green-700"
                      }`
                    }
                  >
                    {item.name}
                  </NavLink>
                ))}
              </div>
            </div>

            {/* Mobile menu button */}
            <div className="md:hidden">
              <button
                type="button"
                onClick={handleSidebarToggle}
                className="inline-flex items-center justify-center p-2 rounded-md text-gray-200 hover:text-gray-300 hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-green-700"
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

      {/* Sidebar overlay for mobile */}
      {sidebarOpen && (
        <div className="fixed inset-0 z-40 flex md:hidden">
          {/* Background overlay */}
          <div
            className="fixed inset-0 bg-black bg-opacity-50"
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
