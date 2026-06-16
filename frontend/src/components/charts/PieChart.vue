<script setup lang="ts">
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js';
import { Pie } from 'vue-chartjs';
import { computed } from 'vue';

// Register ChartJS components
ChartJS.register(ArcElement, Tooltip, Legend);

interface PieChartDataItem {
  label: string;
  value: number;
  categoryId: string;
}

interface PieChartProps {
  data: PieChartDataItem[];
  title?: string;
  total?: number;
  showLegend?: boolean;
}

const props = defineProps<PieChartProps>();

// Generate colors for segments
const colors = [
  '#0d6efd', '#6610f2', '#6f42c1', '#d63384',
  '#dc3545', '#fd7e14', '#ffc107', '#198754',
  '#20c997', '#0dcaf0', '#6c757d', '#17a2b8'
];

// Constants
const ZERO = 0;
const ONE = 1;
const PERCENTAGE_MULTIPLIER = 100;

const chartData = computed(() => {
  const labels = props.data.map(item => item.label);
  const values = props.data.map(item => item.value);

  return {
    labels,
    datasets: [
      {
        data: values,
        backgroundColor: props.data.map((_, i) => colors[i % colors.length]),
        borderWidth: 1,
        borderColor: '#fff'
      }
    ]
  };
});

const chartOptions = computed(() => ({
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      display: props.showLegend ?? true,
      position: 'bottom' as const,
      labels: {
        boxWidth: 12,
        padding: 15,
        usePointStyle: true,
        font: {
          size: 11
        }
      },
    },
    tooltip: {
      callbacks: {
        label: (context: any) => {
          const label = context.label || '';
          const value = context.raw as number;
          const totalSum = context.dataset.data.reduce((a: number, b: number) => a + b, ZERO);
          const percentage = totalSum > ZERO ? ((value / totalSum) * PERCENTAGE_MULTIPLIER).toFixed(ONE) : '0';

          // Ensure label always exists even if undefined by tooltip logic strips it
          return `${label || '(Unknown Category)'}: ${value} (${percentage}%)`;
        }
      }
    },
  } as any
}))
</script>

<template>
  <div class="pie-chart-wrapper">
    <div :class="{ 'has-top-info': props.total !== undefined && !props.title }" class="chart-content-area">
      <div v-if="props.total !== undefined && props.title" aria-live="polite">
        <strong>{{ props.title }}</strong>
      </div>
      <Pie
        :data="chartData"
        :options="chartOptions"
        class="pie-chart-element"
      />
    </div>
    <div v-if="(props.total !== undefined && !props.title)" aria-live="polite">
      <strong>Total:</strong> {{ props.total }}
      <slot name="legend"></slot>
    </div>
  </div>
</template>

<style scoped>
.pie-chart-wrapper {
  position: relative;
  height: auto;
  min-height: 280px;
  width: 100%;
  display: flex;
  flex-direction: column;
}

/* Content area that holds the chart, allows shrinking/growing based on aspect ratio needs via vue-chartjs internal sizing if desired, but here we constrain height to prevent overflow. */
.chart-content-area {
  display: flex;
  flex-grow: 1; /* Allow content to expand within available space */
}

/* Ensure Pie element doesn't exceed wrapper constraints */
.pie-chart-element {
    min-height: 20px; /* Small base height even if data is minimal */
    margin-bottom: 1em;
}

/* Adjust spacing logic based on presence of title vs total label to avoid overlap */
.has-top-info {
    padding-bottom: 0.5rem;
    flex-direction: column-reverse !important;
}
</style>