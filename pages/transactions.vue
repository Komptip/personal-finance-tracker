<script setup lang="ts">
import { Search, X, ChevronLeft, ChevronRight } from 'lucide-vue-next'
import { total, matchesLabel, searchMatches } from '~/utils/analysis'
const { matching, scope, ledger, money, preset, clearFilters } = useAnalysis()
const results = computed(() =>
  matching.value
    .filter((t) => matchesLabel(t, ledger.value.label) && searchMatches(t, ledger.value.search))
    .sort((a, b) =>
      ledger.value.sort === 'newest'
        ? b.transaction_date.localeCompare(a.transaction_date) ||
          (b.transaction_time || '').localeCompare(a.transaction_time || '')
        : ledger.value.sort === 'oldest'
          ? a.transaction_date.localeCompare(b.transaction_date) ||
            (a.transaction_time || '').localeCompare(b.transaction_time || '')
          : ledger.value.sort === 'largest'
            ? Math.abs(b.amount) - Math.abs(a.amount)
            : Math.abs(a.amount) - Math.abs(b.amount),
    ),
)
const pages = computed(() => Math.max(1, Math.ceil(results.value.length / 50)))
const pageRows = computed(() =>
  results.value.slice((ledger.value.page - 1) * 50, ledger.value.page * 50),
)
watch(
  [
    () => JSON.stringify(scope.value),
    () => ledger.value.search,
    () => ledger.value.sort,
    () => ledger.value.label,
  ],
  () => (ledger.value.page = 1),
)
watch(
  pages,
  (n) => {
    if (ledger.value.page > n) ledger.value.page = n
  },
  { immediate: true },
)
</script>
<template>
  <header class="page-head">
    <div>
      <p class="eyebrow">EVERY DETAIL, WITHIN REACH</p>
      <h1>Transactions</h1>
      <p>Find, explore and understand the original records.</p>
    </div>
  </header>
  <ScopeToolbar />
  <DataState
    ><section class="panel ledger-panel">
      <div class="ledger-tools">
        <div class="search-field">
          <label for="ledger-search">Search transactions</label>
          <div>
            <Search :size="18" /><input
              id="ledger-search"
              v-model="ledger.search"
              type="search"
              placeholder="Merchant, description or transaction ID"
            /><button
              v-if="ledger.search"
              class="icon-button"
              aria-label="Clear search"
              @click="ledger.search = ''"
            >
              <X :size="17" />
            </button>
          </div>
        </div>
        <label class="sort-field"
          >Sort transactions<select v-model="ledger.sort">
            <option value="newest">Newest first</option>
            <option value="oldest">Oldest first</option>
            <option value="largest">Largest amount</option>
            <option value="smallest">Smallest amount</option>
          </select></label
        >
      </div>
      <div class="ledger-summary">
        <div aria-live="polite">
          <strong>{{ results.length.toLocaleString() }} matching transactions</strong
          ><span
            >{{ money(total(results, scope.mode)) }}
            {{ scope.mode === 'net' ? 'net flow' : scope.mode }}</span
          >
        </div>
        <p class="helper">Amount sorting uses absolute magnitude.</p>
      </div>
      <div v-if="ledger.search || ledger.label" class="ledger-chips chips">
        <span v-if="ledger.search" class="badge">Ledger search: “{{ ledger.search }}”</span
        ><button v-if="ledger.label" class="chip" @click="ledger.label = ''">
          {{ ledger.label === 'unsure' ? 'Marked UNSURE' : 'No primary category'
          }}<X :size="14" /><span class="sr-only">Remove label filter</span></button
        ><span class="helper">Ledger-only filters</span>
      </div>
      <TransactionList
        :transactions="pageRows"
        :reason="
          ledger.label === 'unsure'
            ? 'Marked UNSURE'
            : ledger.label === 'uncategorized'
              ? 'No primary category'
              : undefined
        "
      />
      <div v-if="!results.length" class="state">
        <h2>
          {{
            ledger.search
              ? 'No search results in this selection'
              : 'No transactions match this selection'
          }}
        </h2>
        <p>Try a broader date range, fewer filters or another search.</p>
        <div class="empty-actions">
          <button v-if="ledger.search" @click="ledger.search = ''">Clear search</button
          ><button @click="clearFilters">Clear filters</button
          ><button class="primary" @click="preset('all')">Search all available dates</button>
        </div>
      </div>
      <nav v-if="results.length" class="pagination" aria-label="Transaction pages">
        <span aria-live="polite"
          >{{ ((ledger.page - 1) * 50 + 1).toLocaleString() }}–{{
            Math.min(ledger.page * 50, results.length).toLocaleString()
          }}
          of {{ results.length.toLocaleString() }}</span
        >
        <div>
          <button aria-label="Previous page" :disabled="ledger.page === 1" @click="ledger.page--">
            <ChevronLeft :size="17" /></button
          ><label
            >Page
            <select v-model.number="ledger.page" aria-label="Transaction page">
              <option v-for="p in pages" :key="p" :value="p">{{ p }}</option>
            </select>
            of {{ pages }}</label
          ><button aria-label="Next page" :disabled="ledger.page === pages" @click="ledger.page++">
            <ChevronRight :size="17" />
          </button>
        </div>
      </nav></section
  ></DataState>
</template>
