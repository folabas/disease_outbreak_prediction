import axios from "axios";

// API Base URL - Change this to your actual API endpoint
export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8001/api/v1";

// Create axios instance with default config
export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// Add request interceptor for auth tokens if needed
api.interceptors.request.use(
  (config) => {
    // Log outbound requests for verification
    try {
      const method = (config.method || "get").toUpperCase();
      const url = `${config.baseURL || ""}${config.url || ""}`;
      const params = config.params || {};
      const data = config.data || undefined;
      // mark start time
      (config as any).meta = { startTime: Date.now() };
      console.log("[API]", method, url, { params, data });
    } catch {}
    const token = localStorage.getItem("token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Add response interceptor for error handling
api.interceptors.response.use(
  (response) => {
    try {
      const meta = (response.config as any)?.meta;
      const durationMs = meta?.startTime ? Date.now() - meta.startTime : undefined;
      const url = `${response.config.baseURL || ""}${response.config.url || ""}`;
      console.log("[API] RES", response.status, url, durationMs ? `${durationMs}ms` : "");
    } catch {}
    return response;
  },
  (error) => {
    // Handle specific error codes
    if (error.response?.status === 401) {
      // Handle unauthorized
      localStorage.removeItem("token");
    }
    try {
      const cfg = error.config || {};
      const url = `${cfg.baseURL || ""}${cfg.url || ""}`;
      const status = error.response?.status;
      console.warn("[API] ERR", status, url, error.message);
    } catch {}
    return Promise.reject(error);
  }
);
