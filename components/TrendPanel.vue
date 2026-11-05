<script setup lang="ts">
import {
  BarElement,
  CategoryScale,
  Chart as ChartJS,
  LinearScale,
  Tooltip,
  type ChartOptions,
} from 'chart.js'
import { Bar } from 'vue-chartjs'
import { primaryCategory } from '~/utils/categoryRanking'
import { periods, label, valueCents } from '~/utils/analysis'
ChartJS.register(CategoryScale, LinearScale, BarElement, Tooltip)
const { matching, scope, displayCurrency, displayValue, grouping, setRange, money, resetVersion } =
  useAnalysis()
const stacked = ref(false)
watch(resetVersion, () => {
  stacked.value = false
})
const buckets = computed(() => periods(matching.value, scope.value, grouping.value))
const categories = computed(() => [...new Set(matching.value.map(primaryCategory))].sort())
function color(key: string) {
  let hash = 0
  for (const c of key) hash = (hash * 31 + c.charCodeAt(0)) | 0
  return `hsl(${Math.abs(hash) % 360}, 40%, 45%)`
}
function inspect(index: number, category?: string) {
  const p = buckets.value[index]
  if (!p) return
  setRange(p.start, p.end, true)
  if (category) scope.value.category = category
  if (grouping.value === 'month') grouping.value = 'day'
}
const chartData = computed(() => ({
  labels: buckets.value.map((p) => (grouping.value === 'month' ? p.title : p.start.slice(5))),
  datasets: stacked.value
    ? categories.value.map((category) => ({
        label: label(category),
        data: buckets.value.map(
          (p) =>
            matching.value
              .filter(
                (t) =>
                  t.transaction_date >= p.start &&
                  t.transaction_date <= p.end &&
                  primaryCategory(t) === category,
              )
              .reduce((s, t) => s + valueCents(t, scope.value.mode), 0) / 100,
        ),
        backgroundColor: color(category),
        borderRadius: 3,
        maxBarThickness: 48,
      }))
    : [
        {
          label: label(scope.value.mode),
          data: buckets.value.map((p) => p.total),
          backgroundColor:
            scope.value.mode === 'net'
              ? buckets.value.map((p) => (p.total < 0 ? '#bf625d' : '#0b756b'))
              : '#0b756b',
          borderRadius: 5,
          maxBarThickness: 48,
        },
      ],
}))
const options = computed<ChartOptions<'bar'>>(() => ({
  responsive: true,
  maintainAspectRatio: false,
  animation: false,
  interaction: { mode: 'nearest', intersect: true },
  plugins: {
    legend: { display: false },
    tooltip: { callbacks: { label: (c) => `${c.dataset.label}: ${money(Number(c.raw))}` } },
  },
  scales: {
    x: {
      stacked: stacked.value,
      grid: { display: false },
      border: { display: false },
      ticks: { maxTicksLimit: 12, color: '#637582', maxRotation: 0, font: { size: 11 } },
    },
    y: {
      stacked: stacked.value,
      beginAtZero: true,
      border: { display: false },
      grid: { color: '#edf1f3' },
      ticks: {
        maxTicksLimit: 5,
        color: '#637582',
        callback: (value) => {
          const converted = displayValue(Number(value))
          return converted === null
            ? '—'
            : new Intl.NumberFormat('en', { notation: 'compact' }).format(converted)
        },
      },
    },
  },
  onClick: (_event, elements) => {
    if (elements[0])
      inspect(
        elements[0].index,
        stacked.value ? categories.value[elements[0].datasetIndex] : undefined,
      )
  },
}))
</script>
<template>
  <section class="panel trend">
    <div class="panel-head">
      <div>
        <p class="eyebrow">THE BIG PICTURE</p>
        <h2>{{ scope.mode === 'net' ? 'Net flow' : label(scope.mode) }} over time</h2>
      </div>
      <label class="sr-only" for="grouping">Group trend by</label
      ><select id="grouping" v-model="grouping">
        <option value="month">Monthly</option>
        <option value="week">Weekly</option>
        <option value="day">Daily</option>
      </select>
    </div>
    <div class="chart-toolbar">
      <span class="helper">{{ displayCurrency }} · select a bar to inspect</span
      ><label class="check-row"
        ><input v-model="stacked" type="checkbox" />Category breakdown</label
      >
    </div>
    <div v-if="matching.length" class="chart-wrap">
      <ClientOnly
        ><Bar
          :data="chartData"
          :options="options"
          role="img"
          :aria-label="`${label(scope.mode)} by ${grouping}. Exact totals and inspect actions are available in View periods below.`"
      /></ClientOnly>
    </div>
    <div v-else class="empty-inline chart-wrap">No transactions match this selection.</div>
    <details v-if="stacked" class="chart-legend">
      <summary>Category legend · {{ categories.length }}</summary>
      <div>
        <span v-for="c in categories" :key="c"
          ><i :style="{ background: color(c) }" />{{ label(c) }}</span
        >
      </div>
    </details>
    <details class="periods">
      <summary>
        View periods
        <span
          >{{ buckets.length }}
          {{ grouping === 'month' ? 'months' : grouping === 'week' ? 'weeks' : 'days' }}</span
        >
      </summary>
      <div class="period-list">
        <div v-for="(p, i) in buckets" :key="p.key">
          <span
            ><strong>{{ p.title }}</strong
            ><small>{{ p.start }} – {{ p.end }} · {{ p.count }} transactions</small></span
          ><strong>{{ money(p.total) }}</strong
          ><button :aria-label="`Inspect ${p.title}`" @click="inspect(i)">Inspect</button>
        </div>
      </div>
    </details>
  </section>
</template>
