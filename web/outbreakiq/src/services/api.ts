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
  InsightData,
} from "./types";

// All data endpoints organized by domain
export const outbreakAPI = {
  // Metadata
  metadata: {
    getOptions: (params?: { source?: "auto" | "training" | "weather" | "predictions"; disease?: string }) =>
      api.get("/metadata/options", { params }),
    getDiseases: () => api.get<string[]>("/diseases"),
    getRegions: () => api.get<string[]>("/regions"),
  },

  // Recommendations
  recommendations: {
    get: (params?: { disease?: string; region?: string; year?: number }) =>
      api.get("/recommendations", { params }),
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
    getByRegion: (region: Region) =>
      api.get<ApiResponse<ClimateData>>(`/climate/region/${region}`),
    getHistorical: (params: {
      region: Region;
      startDate: DateString;
      endDate: DateString;
    }) =>
      api.get<ApiResponse<ClimateData[]>>("/climate/historical", { params }),
    getForecast: (region: Region, days: number = 7) =>
      api.get<ApiResponse<WeatherForecast[]>>(`/climate/forecast/${region}`, {
        params: { days },
      }),
  },

  // Population Data
  population: {
    getCurrent: () =>
      api.get<ApiResponse<PopulationData[]>>("/population/current"),
    getByRegion: (region: Region) =>
      api.get<ApiResponse<PopulationData>>(`/population/region/${region}`),
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
    getAlerts: () => api.get<ApiResponse<OutbreakAlert[]>>("/disease/alerts"),
  },

  // Geospatial Data
  geo: {
    getBoundaries: (params: { level: "state" | "lga"; region?: Region }) =>
      api.get<ApiResponse<GeoData[]>>("/geo/boundaries", { params }),
    getHeatmap: (params: {
      dataType: "cases" | "risk" | "facilities";
      region?: Region;
    }) => api.get<ApiResponse<GeoData>>("/geo/heatmap", { params }),
  },

  // Analytics & Insights
  analytics: {
    getInsights: (params: {
      region: Region;
      timeframe: "weekly" | "monthly" | "yearly";
    }) => api.get<ApiResponse<InsightData>>("/analytics/insights", { params }),
    getHotspots: (params: { disease: Disease; year: number }) =>
      api.get<ApiResponse<GeoData[]>>("/analytics/hotspots", { params }),
  },
};
