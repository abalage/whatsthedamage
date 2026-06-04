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
      }
    },
    title: {
      display: !!props.title,
      text: props.title,
      font: {
        size: 14
      }
    },
    tooltip: {
      callbacks: {
        label: (context: any) => {
          const label = context.label || '';
          const value = context.raw as number;
          const total = context.dataset.data.reduce((a: number, b: number) => a + b, ZERO);
          const percentage = total > ZERO ? ((value / total) * PERCENTAGE_MULTIPLIER).toFixed(ONE) : ZERO;
          return `${label}: ${value} (${percentage}%)`;
        }
      }
    }
  }
}));
</script>

<template>
  <div class="pie-chart-container">
    <div v-if="total !== undefined" class="pie-chart-total">
      <strong>Total:</strong> {{ total }}
    </div>
    <Pie :data="chartData" :options="chartOptions" />
  </div>
</template>

<style scoped>
.pie-chart-container {
  position: relative;
  height: 280px;
  width: 100%;
}

.pie-chart-total {
  position: absolute;
  top: 10px;
  left: 0;
  right: 0;
  text-align: center;
  font-size: 0.9rem;
  color: #666;
  z-index: 10;
}
</style>
