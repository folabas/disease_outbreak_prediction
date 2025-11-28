import { api } from "./api.config";
import type {
  ApiResponse,
  Region,
  Disease,
  DateString,
  OutbreakPrediction,
  RiskFactor,
  ClimateData,
  WeatherForecast,
  PopulationData,
  HospitalData,
  DiseaseData,
  OutbreakAlert,
  GeoData,
  InsightsAnalyticsResponse,
  ModelMetricRow,
  RegressionMetricRow,
  AlertMetricRow,
  ReportArtifact,
  ReportsHealth,
  RecommendationsResponse,
  HotspotsResponse,
} from "./types";

// All data endpoints organized by domain
export const outbreakAPI = {
  // Metadata
  metadata: {
    getOptions: (params?: { source?: "auto" | "training" | "weather" | "predictions"; disease?: string }) =>
      api.get("/metadata/options", { params }),
    getDiseases: () => api.get<ApiResponse<string[]>>("/diseases"),
    getRegions: () => api.get<ApiResponse<string[]>>("/regions"),
  },

  // Recommendations
  recommendations: {
    get: (params?: { disease?: Disease; region?: string; year?: number }) =>
      api.get<ApiResponse<RecommendationsResponse>>("/recommendations", { params }),
  },

  // Predictions
  predictions: {
    getCurrent: () =>
      api.get<ApiResponse<OutbreakPrediction[]>>("/predictions/current"),
    getByRegion: (region: Region) =>
      api.get<ApiResponse<OutbreakPrediction>>(`/predictions/region/${region}`),
    postPredict: (payload: { disease: Disease; region: Region; lga?: string; asOf?: string; horizonDays?: number; granularity?: string }) =>
      api.post(`/predictions/predict`, payload),
    getHistorical: (params: {
      startDate: DateString;
      endDate: DateString;
      region?: Region;
    }) =>
      api.get<ApiResponse<OutbreakPrediction[]>>("/predictions/historical", {
        params,
      }),
    getRiskFactors: (region: Region) =>
      api.get<ApiResponse<RiskFactor>>(`/risk-factors/${region}`),
  },

  // Climate Data
  climate: {
    getCurrent: () => api.get<ApiResponse<ClimateData[]>>("/climate/current"),
    getByRegion: (region: Region, params?: { disease?: Disease; startDate?: DateString; endDate?: DateString }) =>
      api.get<ApiResponse<ClimateData>>(`/climate/region/${region}`, { params }),
    getHistorical: (params: {
      region: Region;
      disease?: Disease;
      startDate: DateString;
      endDate: DateString;
    }) =>
      api.get<ApiResponse<ClimateData[]>>("/climate/historical", { params }),
    getForecast: (region: Region, days: number = 7, params?: { disease?: Disease; startDate?: DateString; endDate?: DateString }) =>
      api.get<ApiResponse<WeatherForecast[]>>(`/climate/forecast/${region}`, {
        params: { days, ...(params || {}) },
      }),
  },

  // Population Data
  population: {
    getCurrent: (params?: { region?: string; startDate?: DateString; endDate?: DateString }) =>
      api.get<ApiResponse<PopulationData[]>>("/population/current", { params }),
    getByRegion: (region: Region, params?: { startDate?: DateString; endDate?: DateString }) =>
      api.get<ApiResponse<PopulationData>>(`/population/region/${region}`, { params }),
    getDensityMap: () =>
      api.get<ApiResponse<GeoData>>("/population/density-map"),
    getDemographics: (region: Region) =>
      api.get<ApiResponse<PopulationData>>(
        `/population/demographics/${region}`
      ),
  },

  // Healthcare Facilities
  healthcare: {
    getFacilities: () =>
      api.get<ApiResponse<HospitalData[]>>("/hospitals/current"),
    getByRegion: (region: Region) =>
      api.get<ApiResponse<HospitalData>>(`/hospitals/region/${region}`),
    getCapacityTrends: (params: {
      region: Region;
      startDate: DateString;
      endDate: DateString;
    }) =>
      api.get<ApiResponse<HospitalData[]>>("/hospitals/capacity-trends", {
        params,
      }),
    getResourceMap: (resourceType: "beds" | "staff" | "equipment") =>
      api.get<ApiResponse<GeoData>>("/hospitals/resources", {
        params: { resourceType },
      }),
  },

  // Disease Surveillance
  disease: {
    getCurrent: (disease: Disease) =>
      api.get<ApiResponse<DiseaseData[]>>(`/disease/current/${disease}`),
    getByRegion: (disease: Disease, region: Region) =>
      api.get<ApiResponse<DiseaseData>>(`/disease/${disease}/region/${region}`),
    getHistorical: (params: {
      disease: Disease;
      region: Region;
      startDate: DateString;
      endDate: DateString;
    }) =>
      api.get<ApiResponse<DiseaseData[]>>("/disease/historical", { params }),
    getAlerts: (params?: { disease?: Disease; region?: Region; threshold?: number }) =>
      api.get<ApiResponse<OutbreakAlert[]>>("/disease/alerts", { params }),
  },

  // Geospatial Data
  geo: {
    getBoundaries: (params: { level: "state" | "lga"; region?: Region }) =>
      api.get<ApiResponse<GeoData[]>>("/geo/boundaries", { params }),
    getHeatmap: (params: {
      dataType: "cases" | "risk" | "facilities";
      region?: Region;
      disease?: Disease;
    }) => api.get<ApiResponse<GeoData>>("/geo/heatmap", { params }),
  },

  // Analytics & Insights
  analytics: {
    getInsights: (params?: { disease?: string; region?: string }) =>
      api.get<ApiResponse<InsightsAnalyticsResponse>>("/analytics/insights", { params }),
    getHotspots: (params: { disease: Disease; year?: number; top_n?: number }) =>
      api.get<ApiResponse<HotspotsResponse>>("/analytics/hotspots", { params }),
    getModelMetrics: (params?: { disease?: string }) =>
      api.get<ApiResponse<{ rows: ModelMetricRow[]; count: number }>>("/analytics/model-metrics", { params }),
    getRegressionMetrics: () =>
      api.get<ApiResponse<{ rows: RegressionMetricRow[]; count: number }>>("/analytics/regression-metrics"),
    getAlertMetrics: (params?: { disease?: string }) =>
      api.get<ApiResponse<{ rows: AlertMetricRow[]; count: number }>>("/analytics/alert-metrics", { params }),
    getArtifacts: () =>
      api.get<ApiResponse<{ artifacts: ReportArtifact[] }>>("/analytics/artifacts"),
    getHealth: () =>
      api.get<ApiResponse<{ health: ReportsHealth | null }>>("/analytics/health"),
    refreshReports: () =>
      api.post<ApiResponse<{ exit_code: number; stdout: string; stderr: string }>>("/analytics/refresh-reports"),
  },
};
