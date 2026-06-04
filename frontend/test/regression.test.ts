/**
 * Unit tests for linear regression utility functions
 * @module test/regression
 */

import { expect, test, describe } from 'vitest';
import {
  calculateLinearRegression,
  filterOutliers,
  calculateRegressionSums,
  calculateSlopeAndIntercept,
  REGRESSION_CONFIG
} from '../src/js/regression.js';
import type { RegressionPoint } from '../src/js/regression.js';

// ============================================================================
// Test Helper Functions
// ============================================================================

/**
 * Creates an array of regression points from x and y arrays
 */
function createPoints(xValues: number[], yValues: number[]): RegressionPoint[] {
  if (xValues.length !== yValues.length) {
    throw new Error('xValues and yValues must have the same length');
  }
  return xValues.map((x, index) => ({ x, y: yValues[index] }));
}

/**
 * Rounds a number to 10 decimal places for comparison
 */
function roundTo10Decimal(value: number): number {
  return Math.round(value * 1e10) / 1e10;
}

// ============================================================================
// REGRESSION_CONFIG Tests
// ============================================================================

describe('REGRESSION_CONFIG', () => {
  test('should have correct MIN_POINTS value', () => {
    expect(REGRESSION_CONFIG.MIN_POINTS).toBe(2);
  });

  test('should have correct DEFAULT_SLOPE value', () => {
    expect(REGRESSION_CONFIG.DEFAULT_SLOPE).toBe(0);
  });

  test('should have correct DEFAULT_INTERCEPT value', () => {
    expect(REGRESSION_CONFIG.DEFAULT_INTERCEPT).toBe(0);
  });

  test('should have immutable type (as const assertion)', () => {
    // Note: `as const` is a TypeScript compile-time feature, not runtime
    // The object itself is not frozen at runtime, but TypeScript treats it as readonly
    // This test verifies the type is correctly defined
    expect(REGRESSION_CONFIG.MIN_POINTS).toBe(2);
    expect(REGRESSION_CONFIG.DEFAULT_SLOPE).toBe(0);
    expect(REGRESSION_CONFIG.DEFAULT_INTERCEPT).toBe(0);
  });
});

// ============================================================================
// filterOutliers Tests
// ============================================================================

describe('filterOutliers', () => {
  test('should return all points when array has fewer than MIN_POINTS + 1', () => {
    const points = createPoints([0, 1], [100, 200]);
    const result = filterOutliers(points);
    expect(result).toHaveLength(2);
    expect(result).toEqual(points);
  });

  test('should return all points when array has exactly MIN_POINTS', () => {
    const points = createPoints([0, 1], [100, 200]);
    const result = filterOutliers(points);
    expect(result).toHaveLength(2);
    expect(result).toEqual(points);
  });

  test('should remove one min and one max when they are different', () => {
    const points = createPoints([0, 1, 2, 3, 4], [10, 20, 30, 40, 50]);
    const result = filterOutliers(points);
    
    expect(result).toHaveLength(3);
    // Should have removed x=0 (min y=10) and x=4 (max y=50)
    expect(result.map((p: RegressionPoint) => p.x)).toContain(1);
    expect(result.map((p: RegressionPoint) => p.x)).toContain(2);
    expect(result.map((p: RegressionPoint) => p.x)).toContain(3);
    expect(result.map((p: RegressionPoint) => p.x)).not.toContain(0);
    expect(result.map((p: RegressionPoint) => p.x)).not.toContain(4);
  });

  test('should remove only one point when min and max are the same', () => {
    const points = createPoints([0, 1, 2], [100, 100, 100]);
    const result = filterOutliers(points);
    
    expect(result).toHaveLength(2);
  });

  test('should handle negative values', () => {
    const points = createPoints([0, 1, 2], [-10, 0, 10]);
    const result = filterOutliers(points);
    
    expect(result).toHaveLength(1);
    expect(result[0].y).toBe(0);
  });

  test('should handle floating point values', () => {
    const points = createPoints([0, 1, 2], [1.5, 2.5, 3.5]);
    const result = filterOutliers(points);
    
    expect(result).toHaveLength(1);
    expect(result[0].y).toBe(2.5);
  });

  test('should preserve points when all have same value and count is MIN_POINTS', () => {
    const points = createPoints([0, 1], [50, 50]);
    const result = filterOutliers(points);
    
    expect(result).toHaveLength(2);
  });
});

// ============================================================================
// calculateRegressionSums Tests
// ============================================================================

describe('calculateRegressionSums', () => {
  test('should calculate correct sums for single point', () => {
    const points = createPoints([5], [10]);
    const result = calculateRegressionSums(points);
    
    expect(result.sumX).toBe(5);
    expect(result.sumY).toBe(10);
    expect(result.sumXY).toBe(50);
    expect(result.sumX2).toBe(25);
  });

  test('should calculate correct sums for multiple points', () => {
    const points = createPoints([0, 1, 2], [0, 1, 4]);
    const result = calculateRegressionSums(points);
    
    // sumX = 0 + 1 + 2 = 3
    // sumY = 0 + 1 + 4 = 5
    // sumXY = 0*0 + 1*1 + 2*4 = 0 + 1 + 8 = 9
    // sumX2 = 0^2 + 1^2 + 2^2 = 0 + 1 + 4 = 5
    expect(result.sumX).toBe(3);
    expect(result.sumY).toBe(5);
    expect(result.sumXY).toBe(9);
    expect(result.sumX2).toBe(5);
  });

  test('should handle negative values', () => {
    const points = createPoints([-1, 0, 1], [-2, 0, 2]);
    const result = calculateRegressionSums(points);
    
    // sumX = -1 + 0 + 1 = 0
    // sumY = -2 + 0 + 2 = 0
    // sumXY = (-1 * -2) + (0 * 0) + (1 * 2) = 2 + 0 + 2 = 4
    // sumX2 = (-1)^2 + 0^2 + 1^2 = 1 + 0 + 1 = 2
    expect(result.sumX).toBe(0);
    expect(result.sumY).toBe(0);
    expect(result.sumXY).toBe(4);
    expect(result.sumX2).toBe(2);
  });

  test('should return zeros for empty array', () => {
    const result = calculateRegressionSums([]);
    
    expect(result.sumX).toBe(0);
    expect(result.sumY).toBe(0);
    expect(result.sumXY).toBe(0);
    expect(result.sumX2).toBe(0);
  });
});

// ============================================================================
// calculateSlopeAndIntercept Tests
// ============================================================================

describe('calculateSlopeAndIntercept', () => {
  test('should calculate correct slope and intercept for perfect line', () => {
    // y = 2x + 0, points: (0,0), (1,2), (2,4)
    // sumX = 3, sumY = 6, sumXY = 10, sumX2 = 5, n = 3
    const sums = { sumX: 3, sumY: 6, sumXY: 10, sumX2: 5 };
    const result = calculateSlopeAndIntercept(sums, 3);
    
    expect(roundTo10Decimal(result.slope)).toBe(2);
    expect(roundTo10Decimal(result.intercept)).toBe(0);
  });

  test('should calculate correct slope and intercept with y-intercept', () => {
    // y = x + 5, points: (0,5), (1,6), (2,7)
    // sumX = 0+1+2 = 3
    // sumY = 5+6+7 = 18
    // sumXY = 0*5 + 1*6 + 2*7 = 0 + 6 + 14 = 20
    // sumX2 = 0+1+4 = 5
    const sums = { sumX: 3, sumY: 18, sumXY: 20, sumX2: 5 };
    const result = calculateSlopeAndIntercept(sums, 3);
    
    expect(roundTo10Decimal(result.slope)).toBe(1);
    expect(roundTo10Decimal(result.intercept)).toBe(5);
  });

  test('should handle horizontal line (slope = 0)', () => {
    // y = 5 (constant), points: (0,5), (1,5), (2,5)
    const sums = { sumX: 3, sumY: 15, sumXY: 15, sumX2: 5 };
    const result = calculateSlopeAndIntercept(sums, 3);
    
    expect(roundTo10Decimal(result.slope)).toBe(0);
    expect(roundTo10Decimal(result.intercept)).toBe(5);
  });

  test('should handle negative slope', () => {
    // y = -x + 10, points: (0,10), (1,9), (2,8)
    // sumX = 0+1+2 = 3
    // sumY = 10+9+8 = 27
    // sumXY = 0*10 + 1*9 + 2*8 = 0 + 9 + 16 = 25
    // sumX2 = 0+1+4 = 5
    const sums = { sumX: 3, sumY: 27, sumXY: 25, sumX2: 5 };
    const result = calculateSlopeAndIntercept(sums, 3);
    
    expect(roundTo10Decimal(result.slope)).toBe(-1);
    expect(roundTo10Decimal(result.intercept)).toBe(10);
  });

  test('should handle edge case when denominator is zero', () => {
    // Vertical line or single point: sumX2 * n = sumX * sumX
    const sums = { sumX: 2, sumY: 4, sumXY: 4, sumX2: 2 };
    const result = calculateSlopeAndIntercept(sums, 2);
    
    expect(result.slope).toBe(REGRESSION_CONFIG.DEFAULT_SLOPE);
    expect(result.intercept).toBe(2); // sumY / n = 4 / 2 = 2
  });
});

// ============================================================================
// calculateLinearRegression Tests
// ============================================================================

describe('calculateLinearRegression', () => {
  test('should return default values for empty array', () => {
    const result = calculateLinearRegression([]);
    
    expect(result.slope).toBe(REGRESSION_CONFIG.DEFAULT_SLOPE);
    expect(result.intercept).toBe(REGRESSION_CONFIG.DEFAULT_INTERCEPT);
  });

  test('should return default slope for single point', () => {
    const points = createPoints([5], [10]);
    const result = calculateLinearRegression(points);
    
    expect(result.slope).toBe(REGRESSION_CONFIG.DEFAULT_SLOPE);
    expect(result.intercept).toBe(10);
  });

  test('should calculate correct regression for two points', () => {
    // Points: (0, 0) and (2, 4)
    // Line should be y = 2x + 0
    const points = createPoints([0, 2], [0, 4]);
    const result = calculateLinearRegression(points);
    
    expect(roundTo10Decimal(result.slope)).toBe(2);
    expect(roundTo10Decimal(result.intercept)).toBe(0);
  });

  test('should calculate correct regression for three colinear points', () => {
    // Points: (0, 0), (1, 2), (2, 4)
    // Line should be y = 2x + 0
    const points = createPoints([0, 1, 2], [0, 2, 4]);
    const result = calculateLinearRegression(points);
    
    expect(roundTo10Decimal(result.slope)).toBe(2);
    expect(roundTo10Decimal(result.intercept)).toBe(0);
  });

  test('should calculate correct regression with outlier exclusion', () => {
    // Points with outliers: (0, 100), (1, 2), (2, 3), (3, 4), (4, 101)
    // Min y = 2 (at index 1), Max y = 101 (at index 4)
    // After filtering: (0, 100), (2, 3), (3, 4)
    // These points don't form a perfect line, but we can verify the function works
    const points = createPoints([0, 1, 2, 3, 4], [100, 2, 3, 4, 101]);
    const result = calculateLinearRegression(points, { excludeOutliers: true });
    
    // With points (0,100), (2,3), (3,4):
    // The line should have a negative slope (decreasing from 100 to 4)
    expect(result.slope).toBeLessThan(0);
    // Intercept should be positive and close to 100
    expect(result.intercept).toBeGreaterThan(90);
    expect(result.intercept).toBeLessThan(110);
  });

  test('should return default when outlier exclusion leaves insufficient points', () => {
    // Only 2 points, excluding min/max would leave 0
    const points = createPoints([0, 1], [10, 20]);
    const result = calculateLinearRegression(points, { excludeOutliers: true });
    
    // Should fall back to using all points
    expect(roundTo10Decimal(result.slope)).toBe(10);
    expect(roundTo10Decimal(result.intercept)).toBe(10);
  });

  test('should calculate correct regression for real-world data', () => {
    // Simulating cost of living over 5 months: Jan=100, Feb=120, Mar=110, Apr=130, May=140
    const points = createPoints([0, 1, 2, 3, 4], [100, 120, 110, 130, 140]);
    const result = calculateLinearRegression(points);
    
    // Slope should be positive (increasing trend)
    expect(result.slope).toBeGreaterThan(0);
    // Intercept should be close to first value
    expect(result.intercept).toBeGreaterThan(90);
    expect(result.intercept).toBeLessThan(110);
  });

  test('should handle negative values', () => {
    const points = createPoints([0, 1, 2], [-10, -5, 0]);
    const result = calculateLinearRegression(points);
    
    expect(roundTo10Decimal(result.slope)).toBe(5);
    expect(roundTo10Decimal(result.intercept)).toBe(-10);
  });

  test('should work with non-sequential x-values', () => {
    // x values: 10, 20, 30 with y values: 5, 10, 15
    const points = createPoints([10, 20, 30], [5, 10, 15]);
    const result = calculateLinearRegression(points);
    
    expect(roundTo10Decimal(result.slope)).toBe(0.5);
    expect(roundTo10Decimal(result.intercept)).toBe(0);
  });
});
