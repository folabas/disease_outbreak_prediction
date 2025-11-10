import { NavLink } from "react-router-dom";

interface SidebarProps {
  isOpen: boolean;
  isMobile: boolean;
  onClose: () => void;
}

const Sidebar = ({ isOpen, isMobile, onClose }: SidebarProps) => {
  const navigationItems = [
    {
      name: "Home",
      path: "/",
      icon: "M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6",
    },
    {
      name: "Predictions",
      path: "/predictions",
      icon: "M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z",
    },
    {
      name: "Climate",
      path: "/climate",
      icon: "M3 15a4 4 0 004 4h9a5 5 0 10-.1-9.999 5.002 5.002 0 10-9.78 2.096A4.001 4.001 0 003 15z",
    },
    {
      name: "Population",
      path: "/population",
      icon: "M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z",
    },
    {
      name: "Hospital",
      path: "/hospital",
      icon: "M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4",
    },
    {
      name: "Insights",
      path: "/insights",
      icon: "M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z",
    },
  ];

  return (
    <nav
      className={`${isOpen ? "translate-x-0" : "-translate-x-full"} ${
        isMobile
          ? "fixed inset-y-0 left-0 z-40 w-64 transition-transform duration-300 ease-in-out"
          : "relative w-64 min-h-screen"
      } bg-[#0d2544] shadow-lg flex-shrink-0`}
    >
      {/* Logo */}
      <div className="px-6 pt-8 pb-4 flex items-center justify-between">
        <div className="flex items-center">
          <img
            src="/Clean logo.png"
            alt="OutbreakIQ Logo"
            className="h-10 w-auto"
          />
          <span className="ml-2 text-xl font-semibold text-gray-300">
            OutbreakIQ
          </span>
        </div>
        
      </div>

      {/* Navigation Links */}
      <div className="px-4 py-2 h-full">
        <div className="space-y-1">
          {navigationItems.map((item) => (
            <NavLink
              key={item.name}
              to={item.path}
              onClick={isMobile ? onClose : undefined}
              className={({ isActive }) =>
                `flex items-center px-4 py-3 text-sm font-medium rounded-lg transition-colors ${
                  isActive
                    ? "bg-blue-50 text-green-700"
                    : "text-gray-300 hover:bg-gray-50 hover:text-gray-900"
                }`
              }
            >
              <svg
                className="mr-3 h-5 w-5"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
                aria-hidden="true"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d={item.icon}
                />
              </svg>
              {item.name}
            </NavLink>
          ))}
        </div>
      </div>
    </nav>
  );
};

export default Sidebar;
