<script setup lang="ts">
import {
  ArrowRight,
  ArrowDownLeft,
  ReceiptText,
  CalendarDays,
  ArrowUpRight,
  Search,
  X,
} from 'lucide-vue-next'
import { total, periods, searchMatches } from '~/utils/analysis'
const { matching, scope, money, grouping, ledger, resetVersion, clearFilters, preset } =
  useAnalysis()
const amount = computed(() => total(matching.value, scope.value.mode))
const buckets = computed(() => periods(matching.value, scope.value, grouping.value))
const largest = computed(() =>
  matching.value.reduce((best, t) => (Math.abs(t.amount) > Math.abs(best) ? t.amount : best), 0),
)
const recentSearch = ref('')
const hasRecentSearch = computed(() => !!recentSearch.value.trim())
const recentMatches = computed(() =>
  matching.value
    .filter((t) => searchMatches(t, recentSearch.value))
    .sort(
      (a, b) =>
        b.transaction_date.localeCompare(a.transaction_date) ||
        (b.transaction_time || '').localeCompare(a.transaction_time || ''),
    ),
)
const recent = computed(() => recentMatches.value.slice(0, 6))
watch(resetVersion, () => {
  recentSearch.value = ''
})
async function openRecentTransactions() {
  ledger.value = { search: recentSearch.value.trim(), sort: 'newest', page: 1, label: '' }
  await navigateTo('/transactions')
}
const unsure = computed(() => matching.value.filter((t) => t.tags.includes('UNSURE')).length)
</script>
<template>
  <header class="page-head">
    <div>
      <p class="eyebrow">YOUR FINANCES, IN FOCUS</p>
      <h1>Overview</h1>
      <p>A clear view of where your money goes.</p>
    </div>
    <NuxtLink class="button primary" to="/transactions"
      >Explore transactions <ArrowRight :size="16"
    /></NuxtLink>
  </header>
  <ScopeToolbar />
  <DataState
    ><div class="metrics" aria-live="polite">
      <article class="metric prominent">
        <span class="metric-label"
          >{{ scope.mode === 'net' ? 'Net flow' : `Total ${scope.mode}`
          }}<ArrowDownLeft :size="18" /></span
        ><strong :class="{ negative: scope.mode === 'net' && amount < 0 }">{{
          money(amount)
        }}</strong
        ><small>{{
          scope.mode === 'net'
            ? 'Incoming minus outgoing'
            : scope.mode === 'income'
              ? 'All matching incoming transactions'
              : 'All matching outgoing transactions'
        }}</small>
      </article>
      <article class="metric">
        <span class="metric-label">Transactions<ReceiptText :size="17" /></span
        ><strong>{{ matching.length.toLocaleString() }}</strong
        ><small>In this selection</small>
      </article>
      <article class="metric">
        <span class="metric-label">Average per {{ grouping }}<CalendarDays :size="17" /></span
        ><strong>{{ money(amount / (buckets.length || 1)) }}</strong
        ><small>Includes partial & empty periods</small>
      </article>
      <article class="metric">
        <span class="metric-label"
          >{{
            scope.mode === 'net'
              ? 'Largest by magnitude'
              : scope.mode === 'income'
                ? 'Largest incoming'
                : 'Largest outflow'
          }}<ArrowUpRight :size="17" /></span
        ><strong>{{ money(scope.mode === 'spending' ? Math.abs(largest) : largest) }}</strong
        ><small>Single matching transaction</small>
      </article>
    </div>
    <div v-if="!matching.length" class="empty-banner">
      <span>No transactions match this selection.</span
      ><button @click="clearFilters">Clear filters</button
      ><button @click="preset('all')">All history</button>
    </div>
    <div class="overview-grid"><TrendPanel /><TopCategories /></div>
    <section class="panel recent-panel">
      <div class="panel-head">
        <div>
          <p class="eyebrow">FOLLOW THE DETAILS</p>
          <h2>Recent transactions</h2>
        </div>
        <button v-if="recentMatches.length" class="text-button" @click="openRecentTransactions">
          View all {{ recentMatches.length.toLocaleString()
          }}{{ hasRecentSearch ? (recentMatches.length === 1 ? ' match' : ' matches') : '' }}
          <ArrowRight :size="16" />
        </button>
      </div>
      <div class="ledger-tools">
        <div class="search-field">
          <label for="recent-search">Search recent transactions</label>
          <div>
            <Search :size="18" />
            <input
              id="recent-search"
              v-model="recentSearch"
              type="search"
              placeholder="Merchant, description or transaction ID"
              aria-describedby="recent-search-summary"
            />
            <button
              v-if="recentSearch"
              class="icon-button"
              aria-label="Clear recent transaction search"
              @click="recentSearch = ''"
            >
              <X :size="17" />
            </button>
          </div>
          <p id="recent-search-summary" class="helper" role="status">
            Showing {{ recent.length }} of {{ recentMatches.length.toLocaleString() }}
            {{
              hasRecentSearch
                ? recentMatches.length === 1
                  ? 'search match'
                  : 'search matches'
                : recentMatches.length === 1
                  ? 'transaction'
                  : 'transactions'
            }}
            within the selected dates and filters.
          </p>
        </div>
      </div>
      <TransactionList :transactions="recent" />
      <p v-if="!recent.length" class="empty-inline">
        {{
          hasRecentSearch
            ? 'No transactions match this search. Try another term or broaden the dates and filters.'
            : 'No matching transactions.'
        }}
      </p>
    </section>
    <NuxtLink class="review-callout" to="/suggestions"
      ><span
        ><strong>A closer look at your activity</strong
        ><small>{{
          unsure
            ? `${unsure} matching transactions have labels to check.`
            : 'Explore observations and inspect inferred labels.'
        }}</small></span
      ><span>Open Review <ArrowRight :size="17" /></span
    ></NuxtLink>
  </DataState>
</template>
