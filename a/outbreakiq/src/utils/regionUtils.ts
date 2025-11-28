/**
 * Utility functions for region normalization and display
 */

export function normalizeRegion(region: string): string {
  const normalized = region.trim();
  // Normalize common variations to "All"
  if (["All Nigeria", "All Regions", "all", "All"].includes(normalized)) {
    return "All";
  }
  return normalized;
}

export function displayRegion(region: string): string {
  const normalized = normalizeRegion(region);
  // For display, show "All Nigeria" instead of "All" for better UX
  if (normalized === "All") {
    return "All Nigeria";
  }
  return normalized;
}

export function isAllRegion(region: string): boolean {
  return normalizeRegion(region) === "All";
}

