// Basic Types
export type Region = string; // e.g. 'lagos', 'kano', etc.
export type Disease = "cholera" | "malaria" | "ebola" | "covid";
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

// Shared Feature Blocks
export interface WashMetrics {
  access_to_clean_water_percent: number;
  water_contamination_index: number;
}

export interface HospitalCapacity {
  hospital_beds: number;
  icu_beds: number;
  staff_count: number;
  antimalarial_stock_level: number;
  ppe_availability_score: number;
}

export interface MobilityAndDemographics {
  population: number;
  population_density: number;
  growth_rate_percent: number;
  urban_percent: number;
  market_density: number;
  mobility_index: number;
}

export interface EpidemiologicalSignals {
  cases: number;
  deaths: number;
  cases_last_week: number;
  cases_2w_avg: number;
  cases_growth_rate: number;
  cases_mean_4w: number;
  cases_std_4w: number;
  cases_per_100k: number;
  deaths_last_week: number;
  deaths_mean_4w: number;
  who_cases_national: number;
}

export interface ClimateSignals {
  temperature_2m_mean: number;
  relative_humidity_2m_mean: number;
  precipitation_sum: number;
}

export interface FeatureSnapshot
  extends WashMetrics,
    HospitalCapacity,
    MobilityAndDemographics,
    EpidemiologicalSignals,
    ClimateSignals {
  state: Region;
  disease: Disease;
  week: number;
  year: number;
  mosquito_density_index?: number;
  breeding_sites_count?: number;
}

// Analytics Metrics Types
export interface ModelMetricRow {
  disease: string;
  sample_size?: number;
  positive?: number;
  negative?: number;
  mae?: number;
  rmse?: number;
  r2?: number;
  accuracy_pct?: number;
  precision_weighted_pct?: number;
  recall_weighted_pct?: number;
  f1_weighted_pct?: number;
  precision_pos_pct?: number;
  recall_pos_pct?: number;
  f1_pos_pct?: number;
  precision_neg_pct?: number;
  recall_neg_pct?: number;
  f1_neg_pct?: number;
  auc?: number;
  timestamp?: string;
  model_version?: string;
  roc_path?: string;
  chart_path?: string;
}

export interface RegressionMetricRow {
  disease: string;
  mae?: number;
  model?: string;
  overall_mae?: number;
}

export interface AlertMetricRow {
  disease: string;
  precision?: number;
  recall?: number;
  f1?: number;
}

export interface InsightMetricsSummary {
  accuracy?: number;
  precision?: number;
  recall?: number;
  f1?: number;
  auc?: number | null;
}

export interface FeatureImportanceEntry {
  name: string;
  value: number;
}

export interface InsightsAnalyticsResponse {
  metrics?: InsightMetricsSummary;
  featureImportance?: FeatureImportanceEntry[];
  notes?: string | string[];
}

export interface ReportArtifact {
  name: string;
  path: string;
  exists: boolean;
  size_bytes?: number;
  updated_at?: number;
  download_url: string;
}

export interface ReportsHealth {
  timestamp?: number;
  status?: string;
  rows_used_for_eval?: number;
  overall_mae?: number;
  diseases?: string[];
  sklearn?: boolean;
  [key: string]: unknown;
}

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

// Recommendations Response Types
export interface RecommendationsResponse {
  source: "ollama" | "gemini" | "rule_based";
  recommendations: string[];
  region?: string | null;
  disease: Disease;
  year?: number | null;
  context?: {
    topFactors?: Array<{ feature: string; weight: number }>;
    region?: string | null;
    disease: Disease;
  };
}

// Hotspots Response Types
export interface HotspotEntry {
  region: string;
  score: number;
}

export interface HotspotsResponse {
  disease: Disease;
  hotspots: HotspotEntry[];
}