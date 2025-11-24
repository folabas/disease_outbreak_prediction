import React from "react";

interface ErrorDisplayProps {
  error: string | undefined;
  title?: string;
  className?: string;
}

export const ErrorDisplay: React.FC<ErrorDisplayProps> = ({ error, title = "Error", className = "" }) => {
  if (!error) return null;

  return (
    <div className={`bg-red-50 border-l-4 border-red-600 p-4 rounded-md text-sm text-red-700 ${className}`}>
      <div className="flex items-start">
        <svg className="h-5 w-5 text-red-600 mr-2 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
          <path
            fillRule="evenodd"
            d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
            clipRule="evenodd"
          />
        </svg>
        <div>
          <h3 className="font-semibold">{title}</h3>
          <p>{error}</p>
        </div>
      </div>
    </div>
  );
};

