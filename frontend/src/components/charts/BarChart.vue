<script setup lang="ts">
import { Chart as ChartJS, Title, Tooltip, Legend, BarElement, CategoryScale, LinearScale } from 'chart.js';
import { Bar } from 'vue-chartjs';
import { computed } from 'vue';

// Register ChartJS components
ChartJS.register(Title, Tooltip, Legend, BarElement, CategoryScale, LinearScale);

interface ChartDataItem {
  label: string;
  value: number;
}

interface BarChartProps {
  data: ChartDataItem[];
  title?: string;
  showTrendline?: boolean;
  trendlineValue?: number;
  currency?: string;
}

const props = defineProps<BarChartProps>();

const chartData = computed(() => ({
  labels: props.data.map(item => item.label),
  datasets: [
    {
      label: 'Cost of Living',
      data: props.data.map(item => item.value),
      backgroundColor: '#0d6efd',
      borderColor: '#0d6efd',
      borderWidth: 1
    }
  ]
}));

const chartOptions = computed(() => ({
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      display: false
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
          return `${label}: ${formatCurrency(Math.abs(value), props.currency)}`;
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
            return formatCurrency(Math.abs(value), props.currency);
          }
          return value;
        }
      }
    }
  }
}));

function formatCurrency(value: number, currency?: string): string {
  return new Intl.NumberFormat('en-US', {
    minimumFractionDigits: 2
  }).format(value) + (currency ? ` ${currency}` : '');
}
</script>

<template>
  <div class="chart-container">
    <Bar :data="chartData" :options="chartOptions" />
    
    <!-- Trendline indicator -->
    <div v-if="showTrendline && trendlineValue !== undefined" class="trendline-indicator">
      <span class="trendline-label">
        <i class="bi bi-graph-up me-1"></i>
        Mean: {{ formatCurrency(Math.abs(trendlineValue), currency) }}
      </span>
    </div>
  </div>
</template>

<style scoped>
.chart-container {
  position: relative;
  height: 400px;
  width: 100%;
}

.trendline-indicator {
  position: absolute;
  top: 10px;
  right: 10px;
  background: rgba(255, 255, 255, 0.95);
  padding: 8px 12px;
  border-radius: 6px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.15);
  z-index: 10;
}

.trendline-label {
  font-size: 0.875rem;
  color: #dc3545;
}
</style>