/**
 * Utilities for normalizing API responses and handling errors
 */

import type { ApiResponse } from "../services/types";

/**
 * Normalize API response structure
 * Handles both {data: {...}} and {data: {data: {...}}} formats
 */
export function normalizeApiResponse<T>(response: any): T | undefined {
  if (!response) return undefined;
  
  // Handle axios response structure
  const data = response?.data ?? response;
  
  // Handle ApiResponse wrapper
  if (data && typeof data === "object") {
    // Check if it's wrapped in ApiResponse format
    if ("data" in data && "status" in data) {
      return data.data as T;
    }
    // Check if it's double-wrapped
    if ("data" in data && typeof data.data === "object" && "data" in data.data) {
      return data.data.data as T;
    }
    // Return as-is if it's already the data
    return data as T;
  }
  
  return undefined;
}

/**
 * Extract error message from API error
 */
export function extractErrorMessage(error: unknown): string {
  if (error instanceof Error) {
    return error.message;
  }
  
  if (typeof error === "object" && error !== null) {
    const err = error as any;
    
    // Handle axios error structure
    if (err.response) {
      const detail = err.response.data?.detail || err.response.data?.error || err.response.data?.message;
      if (detail) {
        return typeof detail === "string" ? detail : JSON.stringify(detail);
      }
      return `HTTP ${err.response.status}: ${err.response.statusText || "Request failed"}`;
    }
    
    // Handle error object with message
    if (err.message) {
      return err.message;
    }
    
    // Handle error object with detail
    if (err.detail) {
      return typeof err.detail === "string" ? err.detail : JSON.stringify(err.detail);
    }
  }
  
  return "An unknown error occurred";
}

/**
 * Check if value is null or undefined
 */
export function isNullOrUndefined(value: unknown): value is null | undefined {
  return value === null || value === undefined;
}

/**
 * Safe array access with fallback
 */
export function safeArray<T>(value: unknown, fallback: T[] = []): T[] {
  if (Array.isArray(value)) {
    return value;
  }
  return fallback;
}

/**
 * Safe number conversion
 */
export function safeNumber(value: unknown, fallback: number = 0): number {
  if (typeof value === "number" && isFinite(value)) {
    return value;
  }
  if (typeof value === "string") {
    const parsed = parseFloat(value);
    if (!isNaN(parsed) && isFinite(parsed)) {
      return parsed;
    }
  }
  return fallback;
}

/**
 * Safe string conversion
 */
export function safeString(value: unknown, fallback: string = ""): string {
  if (typeof value === "string") {
    return value;
  }
  if (value === null || value === undefined) {
    return fallback;
  }
  return String(value);
}


