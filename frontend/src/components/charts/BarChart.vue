<script setup lang="ts">
import { Chart as ChartJS, Title, Tooltip, Legend, BarElement, LineElement, CategoryScale, LinearScale, PointElement } from 'chart.js';
import { Bar } from 'vue-chartjs';
import { computed } from 'vue';

// Register ChartJS components
ChartJS.register(Title, Tooltip, Legend, BarElement, LineElement, CategoryScale, LinearScale, PointElement);

interface ChartDataItem {
  label: string;
  value: number;
  timestamp?: number;
}

interface BarChartProps {
  data: ChartDataItem[];
  title?: string;
  showTrendline?: boolean;
  currency?: string;
}

const props = defineProps<BarChartProps>();

// Constants
const MIN_POINTS_FOR_REGRESSION = 2;
const ZERO = 0;
const TRENDLINE_BORDER_WIDTH = 2;
const TRENDLINE_DASH_PATTERN = [5, 5];
/**
 * Calculate linear regression for a set of points
 * Returns { slope, intercept } for the line y = slope * x + intercept
 * @param points - Array of {x, y} points
 * @param excludeMinMax - If true, excludes the points with minimum and maximum y-values (default: false)
 */
function calculateLinearRegression(
  points: { x: number; y: number }[],
  excludeMinMax: boolean = false
): { slope: number; intercept: number } {
  // Filter out points with minimum and maximum y-values if requested
  let filteredPoints = points;
  if (excludeMinMax && points.length > MIN_POINTS_FOR_REGRESSION) {
    const yValues = points.map(p => p.y);
    const minY = Math.min(...yValues);
    const maxY = Math.max(...yValues);

    // Find indices of first occurrence of min and max
    const minIndex = points.findIndex(p => p.y === minY);
    const maxIndex = points.findIndex(p => p.y === maxY);

    // Remove one min and one max point (if they're different)
    if (minIndex !== maxIndex) {
      filteredPoints = points.filter((_, index) => index !== minIndex && index !== maxIndex);
    } else {
      // If min and max are the same (all values equal), remove just one
      filteredPoints = points.filter((_, index) => index !== minIndex);
    }

    // If we filtered out too many points, use all points
    if (filteredPoints.length < MIN_POINTS_FOR_REGRESSION) {
      filteredPoints = points;
    }
  }

  if (filteredPoints.length < MIN_POINTS_FOR_REGRESSION) {
    return { slope: ZERO, intercept: points.length > ZERO ? points[ZERO].y : ZERO };
  }

  const n = filteredPoints.length;
  let sumX = ZERO, sumY = ZERO, sumXY = ZERO, sumX2 = ZERO;

  for (const point of filteredPoints) {
    sumX += point.x;
    sumY += point.y;
    sumXY += point.x * point.y;
    sumX2 += point.x * point.x;
  }

  const slope = (n * sumXY - sumX * sumY) / (n * sumX2 - sumX * sumX);
  const intercept = (sumY - slope * sumX) / n;

  return { slope, intercept };
}

const chartData = computed(() => {
  const datasets: any[] = [
    {
      label: 'Cost of Living',
      data: props.data.map(item => item.value),
      backgroundColor: '#0d6efd',
      borderColor: '#0d6efd',
      borderWidth: 1,
      type: 'bar'
    }
  ];

  // Add trendline as a line dataset when enabled
  if (props.showTrendline && props.data.length >= MIN_POINTS_FOR_REGRESSION) {
    // Check if data is in descending order (newest first) by comparing timestamps
    // If timestamps are in descending order, we need to reverse the x-values for regression
    const hasTimestamps = props.data.every(item => item.timestamp !== undefined);
    const isDescending = hasTimestamps && props.data.length > 1 ?
      props.data[0].timestamp! > props.data[1].timestamp! :
      false;

    // For descending data (newest first), use reversed indices for x-values
    // This ensures x=0 maps to oldest and x=n maps to newest in the regression
    const n = props.data.length - 1;
    const points = props.data.map((item, displayIndex) => {
      const x = isDescending ? n - displayIndex : displayIndex;
      return { x, y: item.value };
    });

    const { slope, intercept } = calculateLinearRegression(points, true);

    // Generate trendline data points using the regression formula
    // Map back to display order
    const trendlineData = props.data.map((_, displayIndex) => {
      const x = isDescending ? n - displayIndex : displayIndex;
      return slope * x + intercept;
    });

    datasets.push({
      label: 'Trend',
      data: trendlineData,
      borderColor: '#dc3545',
      borderWidth: TRENDLINE_BORDER_WIDTH,
      backgroundColor: 'transparent',
      type: 'line',
      tension: ZERO, // Straight line for regression
      pointRadius: ZERO, // No points on trendline
      borderDash: TRENDLINE_DASH_PATTERN // Dashed line for trendline
    });
  }

  return {
    labels: props.data.map(item => item.label),
    datasets
  };
});

const chartOptions = computed(() => ({
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      display: props.showTrendline && props.data.length >= MIN_POINTS_FOR_REGRESSION,
      position: 'top',
      align: 'end'
    },
    title: {
      display: !!props.title,
      text: props.title,
      font: {
        size: 16
      }
    },
    tooltip: {
      callbacks: {
        label: (context: any) => {
          const value = context.raw as number;
          const label = context.dataset.label || '';
          return `${label}: ${Math.abs(value)} ${props.currency || ''}`.trim();
        }
      }
    }
  },
  scales: {
    y: {
      beginAtZero: true,
      ticks: {
        callback: (value: number | string) => {
          if (typeof value === 'number') {
            return Math.abs(value);
          }
          return value;
        }
      }
    }
  }
}));
</script>

<template>
  <div class="chart-container">
    <Bar :data="chartData" :options="chartOptions" />
  </div>
</template>

<style scoped>
.chart-container {
  position: relative;
  height: 400px;
  width: 100%;
}
</style>