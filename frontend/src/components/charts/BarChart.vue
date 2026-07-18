<script setup lang="ts">
import { Chart as ChartJS, Title, Tooltip, Legend, BarElement, LineElement, CategoryScale, LinearScale, PointElement } from 'chart.js';
import { Bar } from 'vue-chartjs';
import { computed, ref, watch, nextTick } from 'vue';
import type { ChartOptions, ChartData, ActiveElement, Chart } from 'chart.js';
import { calculateLinearRegression, REGRESSION_CONFIG } from '../../js/regression.ts';
import { useThemeStore } from '../../stores/theme';

// Register ChartJS components
ChartJS.register(Title, Tooltip, Legend, BarElement, LineElement, CategoryScale, LinearScale, PointElement);

// Use theme store for colors
const themeStore = useThemeStore();

// Constants
const ZERO = 0;
const ONE = 1;
const TRENDLINE_BORDER_WIDTH = 2;
const TRENDLINE_DASH_PATTERN = [5, 5];

// Selected label styling - use theme colors
const SELECTED_LABEL_COLOR = '#000000';
const NORMAL_LABEL_COLOR = (): string => {
  return themeStore.currentTheme.colors.textSecondary;
};

// Helper function to get category color from theme
const getCategoryColor = (index: number): string => {
  const colors = themeStore.currentTheme.colors.chart.category;
  return colors[index % colors.length];
};

// Get trendline color from theme
const getTrendlineColor = (): string => {
  return themeStore.currentTheme.colors.chart.trendline;
};

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

const emit = defineEmits(['selection-changed']);

// Track selected bar indices (X-axis positions)
const selectedBarIndices = ref<number[]>([]);

// Reference to the chart instance
const chartRef = ref<{ chart: Chart } | null>(null);

// Watch for selection changes and trigger chart update
watch(selectedBarIndices, () => {
  if (chartRef.value?.chart) {
    nextTick(() => {
      chartRef.value?.chart.update();
    });
  }
});

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
      borderColor: getTrendlineColor(),
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

// Handle bar selection - selects/deselects the entire stacked bar at X position
const handleChartClick = (event: unknown, elements: ActiveElement[]) => {
  if (!props.selectable || elements.length === ZERO) return;

  const element = elements[ZERO];
  if (element && element.index !== undefined) {
    const barIndex = element.index;
    const currentSelection = [...selectedBarIndices.value];
    const isSelected = currentSelection.includes(barIndex);

    if (isSelected) {
      selectedBarIndices.value = currentSelection.filter(i => i !== barIndex);
    } else {
      selectedBarIndices.value = [...currentSelection, barIndex];
    }

    // Build selected items data
    const selectedItems = selectedBarIndices.value.map(idx => {
      const item = props.data[idx];
      const values: Record<string, number> = {};
      let total = ZERO;
      props.categories.forEach(category => {
        const value = item.values[category.id] || ZERO;
        values[category.id] = value;
        total += value;
      });
      return {
        index: idx,
        label: item.label,
        values,
        total
      };
    });

    emit('selection-changed', {
      selectedIndices: selectedBarIndices.value,
      selectedItems,
      changedIndex: barIndex,
      isSelected: !isSelected
    });
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
          return selectedBarIndices.value.includes(context.index) ? SELECTED_LABEL_COLOR : NORMAL_LABEL_COLOR();
        },
        font: (context: { index: number }) => {
          return {
            size: 12,
            family: 'sans-serif',
            weight: selectedBarIndices.value.includes(context.index) ? 'bold' : 'normal'
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
