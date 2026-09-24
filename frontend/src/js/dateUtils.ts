/**
 * Date utility functions for What's the Damage frontend
 * @module js/dateUtils
 */

import { useLocaleStore } from '../stores/locale.js';

/**
 * Format a timestamp as a localized month and year string.
 *
 * Uses the current app locale from the locale store to format the date
 * according to the user's language preferences.
 * Must be called within a component setup function or composable context.
 *
 * @param timestamp - Unix epoch timestamp in seconds
 * @returns Formatted month and year string (e.g., "January 2024", "2024 január")
 */
export function formatMonthYear(timestamp: number): string {
  // Validate that timestamp is a valid number
  if (typeof timestamp !== 'number' || Number.isNaN(timestamp) || !Number.isFinite(timestamp)) {
    return 'Invalid Date'
  }

  const localeStore = useLocaleStore();
  const date = new Date(timestamp * 1000); // Convert from seconds to milliseconds

  return date.toLocaleString(localeStore.locale, {
    month: 'long',
    year: 'numeric'
  });
}

/**
 * Extract year and month in ISO format (YYYY-MM) from a date string.
 * Handles various date formats (YYYY-MM-DD, YYYY.MM.DD, etc.)
 *
 * @param dateString - Date string in any format
 * @returns Month key in YYYY-MM format, or 'unknown' if parsing fails
 */
export function extractMonthKey(dateString: string | undefined): string {
  if (!dateString || typeof dateString !== 'string') {
    return 'unknown'
  }

  // Try to parse as ISO date first (YYYY-MM-DD or YYYY-MM)
  // Also handles YYYY.MM.DD format (Hungarian banks)
  // The strategy: extract first 4 chars as year, then find the month part
  
  // Clean the string and try to extract year and month
  const trimmed = dateString.trim()
  
  // Try to split by common separators
  const parts = trimmed.split(/[\s./-]/)
  
  if (parts.length >= 3 && parts[0] && parts[1]) {
    // Assume format is year, month, day (in any order, but year is usually first)
    const year = parts[0]
    const month = parts[1].padStart(2, '0')
    
    if (year.length === 4 && month.length <= 2) {
      return `${year}-${month}`
    }
  } else if (parts.length >= 2 && parts[0] && parts[1]) {
    // Might be YYYY-MM or similar
    const year = parts[0]
    const month = parts[1].padStart(2, '0')
    
    if (year.length === 4 && month.length <= 2) {
      return `${year}-${month}`
    }
  }
  
  // Fallback: try to extract YYYY and MM from start of string
  // Works for formats like YYYYMMDD, YYYY.MM.DD, YYYY-MM-DD
  if (trimmed.length >= 7) {
    const year = trimmed.substring(0, 4)
    const monthChar = trimmed.charAt(4)
    
    // If separator is a digit, it's likely YYYYMMDD format
    if (year && /\d{4}/.test(year)) {
      let month: string
      
      // Check the 5th character (index 4)
      if (/\d/.test(monthChar)) {
        // Format: YYYYMMDD
        month = trimmed.substring(4, 6)
      } else if (trimmed.length >= 6) {
        // Format: YYYY-MM-DD, YYYY.MM.DD, YYYY/MM/DD, etc.
        // Find the next non-separator character after year
        const rest = trimmed.substring(4)
        const monthMatch = rest.match(/^\D*(\d{1,2})/)
        if (monthMatch) {
          month = monthMatch[1].padStart(2, '0')
        } else {
          month = trimmed.substring(5, 7).replace(/\D/g, '')
        }
      } else {
        month = ''
      }
      
      if (month && month.length <= 2) {
        return `${year}-${month.padStart(2, '0')}`
      }
    }
  }
  
  return 'unknown'
}

/**
 * Create a Date object for the first day of a month from a month key.
 * Handles month keys in YYYY-MM format.
 *
 * @param monthKey - Month key in YYYY-MM format
 * @returns Date object for the first day of the month, or undefined if invalid
 */
export function createMonthDate(monthKey: string): Date | undefined {
  // Ensure monthKey is in YYYY-MM format
  const normalized = extractMonthKey(monthKey)
  
  if (normalized === 'unknown') {
    return undefined
  }
  
  // Create date string in ISO format
  const dateString = `${normalized}-01T00:00:00Z`
  const date = new Date(dateString)
  
  if (Number.isNaN(date.getTime())) {
    return undefined
  }
  
  return date
}

/**
 * Parse ISO date string to Date object.
 * Handles ISO 8601 formats (YYYY-MM-DD, YYYY-MM-DDTHH:MM:SS, etc.)
 * Also falls back to parsing numeric strings (epoch timestamps) for backward compatibility.
 *
 * @param dateString - ISO 8601 date string or epoch timestamp string
 * @returns Date object (local timezone) or null if invalid
 */
export function parseDate(dateString: string | null | undefined): Date | null {
  if (!dateString) return null;
  
  // Try to parse as ISO date string first
  try {
    const date = new Date(dateString);
    if (!Number.isNaN(date.getTime())) {
      return date;
    }
  } catch {
    // Fall through to try other formats
  }
  
  // Fallback: try parsing as epoch timestamp string
  if (typeof dateString === 'string' && /^\d+$/.test(dateString)) {
    const timestamp = parseInt(dateString, 10);
    if (!Number.isNaN(timestamp)) {
      return new Date(timestamp * 1000);
    }
  }
  
  return null;
}

/**
 * Format date for display.
 * Accepts Date objects or ISO date strings.
 *
 * @param date - Date object or ISO string
 * @param locale - BCP 47 language tag (e.g., 'en-US', 'hu-HU')
 * @returns Formatted date string
 */
export function formatDate(date: Date | string | null, locale: string = 'en-US'): string {
  if (!date) return '';
  const dateObj = date instanceof Date ? date : parseDate(date);
  if (!dateObj) return '';
  return dateObj.toLocaleDateString(locale, {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  });
}

/**
 * Format date as YYYY-MM-DD.
 * Accepts Date objects or ISO date strings.
 *
 * @param date - Date object or ISO string
 * @returns Date string in YYYY-MM-DD format
 */
export function formatDateISO(date: Date | string | null): string {
  if (!date) return '';
  const dateObj = date instanceof Date ? date : parseDate(date);
  if (!dateObj) return '';
  return dateObj.toISOString().split('T')[0];
}

/**
 * Extract year-month key (YYYY-MM) for grouping.
 * Accepts Date objects or ISO date strings.
 *
 * @param date - Date object or ISO string
 * @returns Year-month string (e.g., "2024-01")
 */
export function getMonthKey(date: Date | string | null): string {
  if (!date) return 'unknown';
  const dateObj = date instanceof Date ? date : parseDate(date);
  if (!dateObj) return 'unknown';
  const year = dateObj.getFullYear();
  const month = String(dateObj.getMonth() + 1).padStart(2, '0');
  return `${year}-${month}`;
}

/**
 * Convert Date to epoch timestamp (for legacy code paths).
 * Accepts Date objects or ISO date strings.
 *
 * @param date - Date object or ISO string
 * @returns Unix timestamp in seconds, or null
 */
export function toEpoch(date: Date | string | null): number | null {
  if (!date) return null;
  const dateObj = date instanceof Date ? date : parseDate(date);
  if (!dateObj) return null;
  return Math.floor(dateObj.getTime() / 1000);
}

/**
 * Check if two dates are the same day.
 * Accepts Date objects or ISO date strings.
 *
 * @param date1 - First date
 * @param date2 - Second date
 * @returns true if same day
 */
export function isSameDay(date1: Date | string | null, date2: Date | string | null): boolean {
  if (!date1 || !date2) return false;
  const d1 = date1 instanceof Date ? date1 : parseDate(date1);
  const d2 = date2 instanceof Date ? date2 : parseDate(date2);
  if (!d1 || !d2) return false;
  return d1.getFullYear() === d2.getFullYear() &&
         d1.getMonth() === d2.getMonth() &&
         d1.getDate() === d2.getDate();
}
