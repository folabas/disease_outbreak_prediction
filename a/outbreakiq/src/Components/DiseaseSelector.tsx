import React from "react";
import type { Disease } from "../services/types";

interface DiseaseSelectorProps {
  value: Disease;
  onChange: (disease: Disease) => void;
  className?: string;
  label?: string;
  showLabel?: boolean;
}

const DISEASE_OPTIONS: Disease[] = ["cholera", "malaria", "ebola", "covid"];

export const DiseaseSelector: React.FC<DiseaseSelectorProps> = ({
  value,
  onChange,
  className = "",
  label = "Disease",
  showLabel = true,
}) => {
  return (
    <div className={className}>
      {showLabel && <label className="text-sm text-gray-600 mr-2">{label}:</label>}
      <select
        value={value}
        onChange={(e) => onChange(e.target.value as Disease)}
        className="border rounded-md px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
      >
        {DISEASE_OPTIONS.map((d) => (
          <option key={d} value={d}>
            {d.replace("-", " ").toUpperCase()}
          </option>
        ))}
      </select>
    </div>
  );
};

