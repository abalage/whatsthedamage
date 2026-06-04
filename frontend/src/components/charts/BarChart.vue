<script setup lang="ts">
import { Chart as ChartJS, Title, Tooltip, Legend, BarElement, LineElement, CategoryScale, LinearScale, PointElement } from 'chart.js';
import { Bar } from 'vue-chartjs';
import { computed } from 'vue';
import type { ChartOptions } from 'chart.js';
import { calculateLinearRegression, REGRESSION_CONFIG } from '../../js/regression.ts';

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
}

const props = defineProps<BarChartProps>();

// Constants
const ZERO = 0;
const TRENDLINE_BORDER_WIDTH = 2;
const TRENDLINE_DASH_PATTERN = [5, 5];

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
  if (props.showTrendline && props.data.length >= REGRESSION_CONFIG.MIN_POINTS) {
    // Check if data is in descending order (newest first) by comparing timestamps
    // If timestamps are in descending order, we need to reverse the x-values for regression
    // FIXME remove this hack by changing order of data presentation
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

    const { slope, intercept } = calculateLinearRegression(points, { excludeOutliers: true });

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
      pointRadius: 5, // No points on trendline
      borderDash: TRENDLINE_DASH_PATTERN // Dashed line for trendline
    });
  }

  return {
    labels: props.data.map(item => item.label),
    datasets
  };
});

const chartOptions = computed<ChartOptions<'bar'>>(() => ({
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      display: props.showTrendline && props.data.length >= REGRESSION_CONFIG.MIN_POINTS,
      position: 'top' as const,
      align: 'end' as const
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
          return `${label}: ${value}`.trim();
        }
      }
    }
  },
  scales: {
    y: {
      beginAtZero: true,
      ticks: {
        callback: (value: number | string) => {
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
