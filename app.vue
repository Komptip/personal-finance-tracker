<script setup lang="ts">
import {
  ChartNoAxesCombined,
  LayoutDashboard,
  ListFilter,
  ScanSearch,
  ShieldCheck,
} from 'lucide-vue-next'
import { dateLabel } from '~/utils/analysis'
import '~/assets/css/main.css'
const { data, min, max, load, scope, ledger } = useAnalysis()
watch(
  () => JSON.stringify(scope.value),
  () => {
    ledger.value.page = 1
  },
)
await callOnce('load-finance', load)
const route = useRoute()
const navigation = [
  { to: '/', name: 'Overview', icon: LayoutDashboard },
  { to: '/transactions', name: 'Transactions', icon: ListFilter },
  { to: '/suggestions', name: 'Review', icon: ScanSearch },
]
useHead({ title: 'Fin stats · Your money, clearly', htmlAttrs: { lang: 'en' } })
</script>
<template>
  <a class="skip-link" href="#main">Skip to content</a>
  <div class="workspace">
    <aside class="sidebar">
      <NuxtLink class="brand" to="/"
        ><span class="brand-icon"><ChartNoAxesCombined :size="23" /></span> Fin stats<span
          class="brand-dot"
          >.</span
        ></NuxtLink
      >
      <p class="nav-caption">YOUR WORKSPACE</p>
      <nav aria-label="Main navigation">
        <NuxtLink
          v-for="item in navigation"
          :key="item.to"
          :to="item.to"
          :aria-current="route.path === item.to ? 'page' : undefined"
          :class="{ active: route.path === item.to }"
          ><component :is="item.icon" :size="19" /><span>{{ item.name }}</span></NuxtLink
        >
      </nav>
      <div class="sidebar-foot">
        <ShieldCheck :size="18" /><strong>Local & private</strong>
        <p>Your financial history stays here.</p>
        <div v-if="min" class="coverage">
          <span>AVAILABLE TRANSACTIONS</span>{{ dateLabel(min) }}<br />to {{ dateLabel(max) }}
        </div>
      </div>
    </aside>
    <main id="main" class="main" tabindex="-1">
      <div v-if="data?.meta.demo" class="empty-banner" role="status">
        <strong>Demo workspace</strong
        ><span>These transactions are fictional. Import your own bank export to get started.</span>
      </div>
      <NuxtPage />
      <footer class="page-footer">
        <span v-if="min">Available transactions: {{ dateLabel(min) }} – {{ dateLabel(max) }}. </span
        >Coverage does not guarantee every statement or day is present.
      </footer>
    </main>
  </div>
</template>
