/**
 * Utility functions for date format normalization
 */

/**
 * Normalize various date formats to a consistent format for charts
 */
export function normalizeDate(dateStr: string | null | undefined): string {
  if (!dateStr) return "";
  
  const str = String(dateStr).trim();
  
  // Handle ISO date strings (YYYY-MM-DD)
  if (/^\d{4}-\d{2}-\d{2}/.test(str)) {
    return str.split("T")[0]; // Remove time component if present
  }
  
  // Handle week format (YYYY-W##)
  if (/^\d{4}-W\d{2}/.test(str)) {
    return str;
  }
  
  // Handle timestamp
  if (/^\d+$/.test(str)) {
    const date = new Date(Number(str) * 1000);
    return date.toISOString().split("T")[0];
  }
  
  // Try to parse as date
  try {
    const date = new Date(str);
    if (!isNaN(date.getTime())) {
      return date.toISOString().split("T")[0];
    }
  } catch {
    // Fall through
  }
  
  return str; // Return as-is if can't parse
}

/**
 * Format date for display in charts
 */
export function formatDateForChart(dateStr: string): string {
  const normalized = normalizeDate(dateStr);
  
  // If it's a week format, format it nicely
  if (/^\d{4}-W\d{2}/.test(normalized)) {
    return normalized.replace("W", " Week ");
  }
  
  // If it's a date, format as short date
  if (/^\d{4}-\d{2}-\d{2}/.test(normalized)) {
    const date = new Date(normalized);
    return date.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
  }
  
  return normalized;
}

/**
 * Sort dates in ascending order
 */
export function sortByDate<T extends { date?: string; name?: string }>(items: T[]): T[] {
  return [...items].sort((a, b) => {
    const dateA = normalizeDate(a.date || a.name);
    const dateB = normalizeDate(b.date || b.name);
    return dateA.localeCompare(dateB);
  });
}


