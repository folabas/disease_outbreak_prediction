import React from 'react';
import { Link } from 'react-router-dom';

const Footer = () => {
  return (
    <div className="px-4 sm:px-10 md:px-20 lg:px-40 flex justify-center py-5 mt-10">
      <div className="layout-content-container flex flex-col w-full max-w-6xl flex-1">
        <footer className="flex flex-col gap-6 px-5 py-10 text-center border-t border-gray-200">
          {/* Quick Links */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-8 mb-8">
            <div>
              <h3 className="text-[#212529] font-bold mb-4">About</h3>
              <ul className="space-y-2">
                <li>
                  <Link to="/about" className="text-[#6C757D] hover:text-[#212529] text-sm">
                    Our Mission
                  </Link>
                </li>
                <li>
                  <Link to="/team" className="text-[#6C757D] hover:text-[#212529] text-sm">
                    Team
                  </Link>
                </li>
              </ul>
            </div>
            
            <div>
              <h3 className="text-[#212529] font-bold mb-4">Resources</h3>
              <ul className="space-y-2">
                <li>
                  <Link to="/documentation" className="text-[#6C757D] hover:text-[#212529] text-sm">
                    Documentation
                  </Link>
                </li>
                <li>
                  <Link to="/api" className="text-[#6C757D] hover:text-[#212529] text-sm">
                    API
                  </Link>
                </li>
              </ul>
            </div>
            
            <div>
              <h3 className="text-[#212529] font-bold mb-4">Support</h3>
              <ul className="space-y-2">
                <li>
                  <Link to="/contact" className="text-[#6C757D] hover:text-[#212529] text-sm">
                    Contact Us
                  </Link>
                </li>
                <li>
                  <Link to="/faq" className="text-[#6C757D] hover:text-[#212529] text-sm">
                    FAQ
                  </Link>
                </li>
              </ul>
            </div>
          </div>

          {/* Bottom Links */}
          <div className="flex flex-col sm:flex-row flex-wrap items-center justify-center gap-6">
            <Link to="/privacy" className="text-[#6C757D] hover:text-[#212529] text-sm font-normal leading-normal min-w-32">
              Privacy Policy
            </Link>
            <Link to="/terms" className="text-[#6C757D] hover:text-[#212529] text-sm font-normal leading-normal min-w-32">
              Terms of Service
            </Link>
            <Link to="/contact" className="text-[#6C757D] hover:text-[#212529] text-sm font-normal leading-normal min-w-32">
              Contact
            </Link>
          </div>

          {/* Copyright */}
          <p className="text-[#6C757D] text-sm font-normal leading-normal">
            © {new Date().getFullYear()} OutbreakIQ. All rights reserved.
          </p>
        </footer>
      </div>
    </div>
  );
};

export default Footer;