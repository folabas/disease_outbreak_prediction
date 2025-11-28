/**
 * Validation utilities for form inputs
 */

import type { Disease } from "../services/types";

const ALLOWED_DISEASES: Disease[] = ["cholera", "malaria", "ebola", "covid"];
const MIN_YEAR = 2006;
const MAX_YEAR = new Date().getFullYear() + 1; // Allow one year in future

/**
 * Validate disease input
 */
export function validateDisease(disease: string): Disease | null {
  const normalized = disease.toLowerCase().trim();
  if (ALLOWED_DISEASES.includes(normalized as Disease)) {
    return normalized as Disease;
  }
  return null;
}

/**
 * Validate region input
 */
export function validateRegion(region: string): string {
  const normalized = region.trim();
  // Normalize common variations
  if (["All Nigeria", "All Regions", "all", "All"].includes(normalized)) {
    return "All";
  }
  return normalized;
}

/**
 * Validate year input
 */
export function validateYear(year: string | number): number | null {
  const num = typeof year === "string" ? parseInt(year, 10) : year;
  if (isNaN(num) || num < MIN_YEAR || num > MAX_YEAR) {
    return null;
  }
  return num;
}

/**
 * Validate numeric input with range
 */
export function validateNumeric(
  value: string | number,
  min?: number,
  max?: number
): number | null {
  const num = typeof value === "string" ? parseFloat(value) : value;
  if (isNaN(num)) {
    return null;
  }
  if (min !== undefined && num < min) {
    return null;
  }
  if (max !== undefined && num > max) {
    return null;
  }
  return num;
}

/**
 * Get validation error message
 */
export function getValidationError(
  field: string,
  value: unknown,
  validator: (v: unknown) => boolean | null
): string | null {
  if (validator(value) === false || validator(value) === null) {
    return `Invalid ${field}`;
  }
  return null;
}


