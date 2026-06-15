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
 * 
 * @param timestamp - Unix epoch timestamp in seconds
 * @returns Formatted month and year string (e.g., "January 2024", "2024 január")
 */
export function formatMonthYear(timestamp: number): string {
  const localeStore = useLocaleStore();
  const date = new Date(timestamp * 1000); // Convert from seconds to milliseconds
  return date.toLocaleString(localeStore.locale, { 
    month: 'long', 
    year: 'numeric' 
  });
}
