// Basic Types
export type Region = string; // e.g. 'lagos', 'kano', etc.
export type Disease = "malaria" | "cholera" | "covid-19";
export type DateString = string; // ISO 8601 format

// Generic API Response wrapper (supports legacy and normalized envelopes)
export type ApiResponse<T> =
  | {
      status: "success";
      data: T;
      message?: string;
      timestamp: string;
    }
  | {
      success: boolean;
      data: T;
      message?: string;
      timestamp: string;
    };

// Prediction Types
export interface OutbreakPrediction {
  region: Region;
  disease: Disease;
  riskLevel: "low" | "medium" | "high" | "critical";
  probability: number;
  predictedCases: number;
  timeframe: {
    start: DateString;
    end: DateString;
  };
  confidence: number;
}

export interface RiskFactor {
  region: Region;
  factors: {
    climate: number;
    population: number;
    healthcare: number;
    historical: number;
  };
  weightedScore: number;
  lastUpdated: DateString;
}

// Climate Types
export interface ClimateData {
  region: Region;
  temperature: {
    current: number;
    min: number;
    max: number;
    average: number;
  };
  rainfall: {
    amount: number; // in mm
    intensity: "light" | "moderate" | "heavy";
  };
  humidity: number;
  timestamp: DateString;
}

export interface WeatherForecast extends Omit<ClimateData, "timestamp"> {
  forecastDate: DateString;
  probability: number;
}

// Population Types
export interface PopulationData {
  region: Region;
  totalPopulation: number;
  densityPerKm2: number;
  demographics: {
    ageGroups: {
      [key: string]: number; // e.g. '0-14': 1000000
    };
    gender: {
      male: number;
      female: number;
    };
  };
  year: number;
}

// Healthcare Types
export interface HospitalData {
  region: Region;
  facilities: {
    total: number;
    types: {
      [key: string]: number; // e.g. 'primary': 100
    };
  };
  capacity: {
    beds: number;
    occupancyRate: number;
    staff: {
      doctors: number;
      nurses: number;
      specialists: number;
    };
  };
  lastUpdated: DateString;
}

// Disease Data Types
export interface DiseaseData {
  region: Region;
  disease: Disease;
  cases: {
    confirmed: number;
    suspected: number;
    recovered: number;
    deaths: number;
  };
  transmissionRate: number;
  period: {
    start: DateString;
    end: DateString;
  };
}

export interface OutbreakAlert {
  id: string;
  region: Region;
  disease: Disease;
  severity: "warning" | "alert" | "emergency";
  details: {
    cases: number;
    trend: "increasing" | "stable" | "decreasing";
    description: string;
  };
  timestamp: DateString;
}

// Geospatial Types
export interface GeoData {
  type: "Feature" | "FeatureCollection";
  geometry: {
    type: "Point" | "Polygon" | "MultiPolygon";
    coordinates: number[] | number[][] | number[][][];
  };
  properties: {
    name: string;
    value?: number;
    [key: string]: any;
  };
}

// Analytics Types
export interface InsightData {
  region: Region;
  period: {
    start: DateString;
    end: DateString;
  };
  trends: {
    cases: {
      current: number;
      previous: number;
      percentageChange: number;
    };
    risk: {
      current: "low" | "medium" | "high" | "critical";
      previous: "low" | "medium" | "high" | "critical";
    };
    factors: {
      [key: string]: {
        impact: number;
        trend: "increasing" | "stable" | "decreasing";
      };
    };
  };
  recommendations: string[];
}
