<script setup lang="ts">
import { Chart as ChartJS, Title, Tooltip, Legend, BarElement, LineElement, CategoryScale, LinearScale, PointElement } from 'chart.js';
import { Bar } from 'vue-chartjs';
import { computed, ref, watch, nextTick } from 'vue';
import type { ChartOptions, ChartData, ActiveElement, Chart } from 'chart.js';
import { calculateLinearRegression, REGRESSION_CONFIG } from '../../js/regression.ts';

// Register ChartJS components
ChartJS.register(Title, Tooltip, Legend, BarElement, LineElement, CategoryScale, LinearScale, PointElement);

// Color palette for categories - consistent colors for visual identity
const CATEGORY_COLORS = [
  '#0d6efd', // Blue - primary
  '#6610f2', // Purple
  '#dc3545', // Red
  '#fd7e14', // Orange
  '#ffc107', // Yellow
  '#198754', // Green
  '#20c997', // Teal
  '#0dcaf0', // Cyan
  '#6f42c1', // Indigo
  '#d63384', // Pink
  '#212529', // Dark
  '#6c757d', // Gray
];

// Constants
const ZERO = 0;
const ONE = 1;
const TRENDLINE_BORDER_WIDTH = 2;
const TRENDLINE_DASH_PATTERN = [5, 5];

// Selected label styling
const SELECTED_LABEL_COLOR = '#000000';
const NORMAL_LABEL_COLOR = '#6c757d';

interface MultiCategoryChartData {
  label: string;
  timestamp?: number;
  values: Record<string, number>;
}

interface CategoryConfig {
  id: string;
  label: string;
}

interface BarChartProps {
  data: MultiCategoryChartData[];
  categories: CategoryConfig[];
  title?: string;
  showTrendline?: boolean;
  selectable?: boolean;
}

const props = defineProps<BarChartProps>();

const emit = defineEmits(['bar-selected']);

// Track selected bar index (X-axis position)
const selectedBarIndex = ref<number | null>(null);

// Reference to the chart instance
const chartRef = ref<{ chart: Chart } | null>(null);

// Watch for selection changes and trigger chart update
watch(selectedBarIndex, () => {
  if (chartRef.value?.chart) {
    nextTick(() => {
      chartRef.value?.chart.update();
    });
  }
});

// Get color for a category by index
const getCategoryColor = (index: number): string => {
  return CATEGORY_COLORS[index % CATEGORY_COLORS.length];
};

// Build the chart data with stacking
const chartData = computed<ChartData<'bar'>>(() => {
  const labels = props.data.map(item => item.label);

  // Create one dataset per category
  const datasets: any[] = props.categories.map((category, categoryIndex) => {
    const color = getCategoryColor(categoryIndex);

    return {
      label: category.label,
      data: props.data.map(dataItem => dataItem.values[category.id] || ZERO),
      backgroundColor: color,
      borderColor: color,
      borderWidth: ONE,
      borderSkipped: false,
      stack: 'stack',
    };
  });

  // Add trendline as a line dataset when enabled
  if (props.showTrendline && props.data.length >= REGRESSION_CONFIG.MIN_POINTS) {
    // Calculate total values for each data point (sum of all selected categories)
    const totalValues = props.data.map(dataItem => {
      return props.categories.reduce((sum, category) => {
        return sum + (dataItem.values[category.id] || ZERO);
      }, ZERO);
    });

    // Check if data is in descending order (newest first) by comparing timestamps
    const hasTimestamps = props.data.every(item => item.timestamp !== undefined);
    const isDescending = hasTimestamps && props.data.length > ONE ?
      props.data[ZERO].timestamp! > props.data[ONE].timestamp! :
      false;

    // For descending data, use reversed indices for x-values
    const n = props.data.length - ONE;
    const points = props.data.map((_, displayIndex) => {
      const x = isDescending ? n - displayIndex : displayIndex;
      return { x, y: totalValues[displayIndex] };
    });

    const { slope, intercept } = calculateLinearRegression(points, { excludeOutliers: true });

    // Generate trendline data points
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
      tension: 0,
      pointRadius: 0,
      borderDash: TRENDLINE_DASH_PATTERN,
      order: 1, // Ensure trendline is drawn above bars
    });
  }

  return {
    labels,
    datasets
  };
});

// Handle bar selection - selects the entire stacked bar at X position
const handleChartClick = (event: unknown, elements: ActiveElement[]) => {
  if (!props.selectable || elements.length === ZERO) return;

  const element = elements[ZERO];
  if (element && element.index !== undefined) {
    const barIndex = element.index;

    // Toggle selection - if clicking the same bar, deselect it
    if (selectedBarIndex.value === barIndex) {
      selectedBarIndex.value = null;
    } else {
      selectedBarIndex.value = barIndex;

      // Emit selection event with all category values for this bar
      const dataItem = props.data[barIndex];
      const values: Record<string, number> = {};
      let total = ZERO;

      props.categories.forEach(category => {
        const value = dataItem.values[category.id] || ZERO;
        values[category.id] = value;
        total += value;
      });

      emit('bar-selected', {
        index: barIndex,
        label: dataItem.label,
        values,
        total
      });
    }
  }
};

const chartOptions = computed<ChartOptions<'bar'>>(() => ({
  responsive: true,
  maintainAspectRatio: false,
  layout: {
    padding: {
      bottom: 20
    }
  },
  onClick: handleChartClick,
  plugins: {
    legend: {
      display: props.categories.length > ZERO,
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
        label: (context) => {
          const value = context.raw as number;
          const label = context.dataset.label || '';
          return `${label}: ${value}`.trim();
        },
        // Show total for the bar in tooltip footer
        footer: (context): string | void => {
          if (context.length === ZERO) return;

          // Sum all datasets at this index
          const index = context[ZERO].dataIndex;
          const total = context.reduce((sum, item) => {
            return sum + (item.raw as number);
          }, ZERO);

          const label = props.data[index]?.label || '';
          return `Total: ${total} (${label})`;
        }
      }
    }
  },
  scales: {
    x: {
      stacked: true,
      grid: {
        display: false
      },
      ticks: {
        display: true,
        color: (context: { index: number }) => {
          return context.index === selectedBarIndex.value ? SELECTED_LABEL_COLOR : NORMAL_LABEL_COLOR;
        },
        font: (context: { index: number }) => {
          return {
            size: 12,
            family: 'sans-serif',
            weight: context.index === selectedBarIndex.value ? 'bold' : 'normal'
          };
        }
      }
    },
    y: {
      stacked: true,
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
    <Bar ref="chartRef" :data="chartData" :options="chartOptions" />
  </div>
</template>

<style scoped>
.chart-container {
  position: relative;
  height: 400px;
  width: 100%;
}
</style>
