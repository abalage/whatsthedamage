/**
 * Linear Regression Utilities
 *
 * This module provides functions for calculating linear regression on datasets.
 * Useful for creating trend lines in charts and visualizations.
 */

// ============================================================================
// Configuration
// ============================================================================

/**
 * Configuration constants for linear regression calculations
 */
export const REGRESSION_CONFIG = {
  MIN_POINTS: 2,
  DEFAULT_SLOPE: 0,
  DEFAULT_INTERCEPT: 0
} as const;

// ============================================================================
// Types
// ============================================================================

/**
 * Options for calculating linear regression
 */
export interface RegressionOptions {
  /** If true, excludes one point with minimum y-value and one with maximum y-value */
  excludeOutliers?: boolean;
}

/**
 * A point with x and y coordinates for regression analysis
 */
export interface RegressionPoint {
  x: number;
  y: number;
}

/**
 * Result of linear regression calculation
 */
export interface RegressionResult {
  slope: number;
  intercept: number;
}

// ============================================================================
// Helper Functions
// ============================================================================

/**
 * Filters out points with minimum and maximum y-values from the dataset.
 * This helps prevent outliers from skewing the trendline.
 *
 * @param points - Array of regression points
 * @returns Filtered array with outliers removed, or original array if filtering
 *          would leave fewer than MIN_POINTS points
 */
export function filterOutliers(points: RegressionPoint[]): RegressionPoint[] {
  if (points.length <= REGRESSION_CONFIG.MIN_POINTS) {
    return points;
  }

  const yValues = points.map(p => p.y);
  const minY = Math.min(...yValues);
  const maxY = Math.max(...yValues);

  // Find indices of first occurrence of min and max
  const minIndex = points.findIndex(p => p.y === minY);
  const maxIndex = points.findIndex(p => p.y === maxY);

  // Remove one min and one max point (if they're different)
  if (minIndex !== maxIndex) {
    return points.filter((_, index) => index !== minIndex && index !== maxIndex);
  }

  // If min and max are the same (all values equal), remove just one
  return points.filter((_, index) => index !== minIndex);
}

/**
 * Calculates the sums required for linear regression formula.
 *
 * @param points - Array of regression points
 * @returns Object containing the four sums: sumX, sumY, sumXY, sumX2
 */
export function calculateRegressionSums(points: RegressionPoint[]): {
  sumX: number;
  sumY: number;
  sumXY: number;
  sumX2: number;
} {
  const initialSums = {
    sumX: 0,
    sumY: 0,
    sumXY: 0,
    sumX2: 0
  };

  return points.reduce((sums, point) => {
    sums.sumX += point.x;
    sums.sumY += point.y;
    sums.sumXY += point.x * point.y;
    sums.sumX2 += point.x * point.x;
    return sums;
  }, { ...initialSums });
}

/**
 * Calculates the slope and intercept from regression sums.
 * Uses the formula: y = slope * x + intercept
 * where slope = (n * ΣXY - ΣX * ΣY) / (n * ΣX² - (ΣX)²)
 * and intercept = (ΣY - slope * ΣX) / n
 *
 * @param sums - Object containing sumX, sumY, sumXY, sumX2
 * @param n - Number of points
 * @returns Object containing slope and intercept
 */
export function calculateSlopeAndIntercept(
  sums: { sumX: number; sumY: number; sumXY: number; sumX2: number },
  n: number
): RegressionResult {
  const denominator = n * sums.sumX2 - sums.sumX * sums.sumX;
  const ZERO = 0;

  // Handle edge case: if denominator is zero (vertical line or single point)
  if (denominator === ZERO) {
    return {
      slope: REGRESSION_CONFIG.DEFAULT_SLOPE,
      intercept: sums.sumY / n
    };
  }

  const slope = (n * sums.sumXY - sums.sumX * sums.sumY) / denominator;
  const intercept = (sums.sumY - slope * sums.sumX) / n;

  return { slope, intercept };
}

// ============================================================================
// Main Function
// ============================================================================

/**
 * Calculates linear regression for a set of points.
 *
 * The line of best fit follows the formula: y = slope * x + intercept
 *
 * @param points - Array of {x, y} points for regression analysis
 * @param options - Optional configuration for regression calculation
 * @param options.excludeOutliers - If true, excludes one point with minimum y-value
 *                                 and one point with maximum y-value before calculating
 *                                 the regression (default: false)
 * @returns Object containing slope and intercept for the line of best fit
 *
 * @example
 * // Basic usage
 * import { calculateLinearRegression } from '@/js/regression';
 * const { slope, intercept } = calculateLinearRegression(points);
 *
 * @example
 * // With outlier exclusion
 * import { calculateLinearRegression } from '@/js/regression';
 * const { slope, intercept } = calculateLinearRegression(points, {
 *   excludeOutliers: true
 * });
 */
export function calculateLinearRegression(
  points: RegressionPoint[],
  options: RegressionOptions = {}
): RegressionResult {
  const { excludeOutliers = false } = options;

  // Validate input
  if (points.length < REGRESSION_CONFIG.MIN_POINTS) {
    return {
      slope: REGRESSION_CONFIG.DEFAULT_SLOPE,
      intercept: points.length > 0 ? points[0].y : REGRESSION_CONFIG.DEFAULT_INTERCEPT
    };
  }

  // Filter outliers if requested
  const filteredPoints = excludeOutliers ? filterOutliers(points) : points;

  // Ensure we still have enough points after filtering
  if (filteredPoints.length < REGRESSION_CONFIG.MIN_POINTS) {
    return {
      slope: REGRESSION_CONFIG.DEFAULT_SLOPE,
      intercept: points.length > 0 ? points[0].y : REGRESSION_CONFIG.DEFAULT_INTERCEPT
    };
  }

  // Calculate regression
  const sums = calculateRegressionSums(filteredPoints);
  return calculateSlopeAndIntercept(sums, filteredPoints.length);
}
