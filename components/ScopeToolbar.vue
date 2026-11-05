<script setup lang="ts">
import { CalendarDays, SlidersHorizontal, X, ArrowLeft, RotateCcw } from 'lucide-vue-next'
import {
  label,
  merchantName,
  monthLabel,
  dateLabel,
  filterScope,
  presetRange,
  monthRange,
} from '~/utils/analysis'
const {
  scope,
  rows,
  currencies,
  displayCurrency,
  displayCurrencies,
  exchangeRates,
  exchangeStatus,
  loadExchangeRates,
  displayValue,
  min,
  max,
  partial,
  rangeText,
  previous,
  back,
  preset,
  month,
  setRange,
  clearFilters,
  reset,
  resetVersion,
} = useAnalysis()
const filterDialog = ref<HTMLDialogElement>()
watch(resetVersion, () => {
  custom.value = false
})
const custom = ref(false)
const start = ref('')
const end = ref('')
const dateError = computed(() =>
  !start.value || !end.value
    ? 'Choose both dates.'
    : start.value > end.value
      ? 'Start date must be on or before end date.'
      : '',
)
const draft = reactive({ tags: [] as string[], transfers: false, merchant: '' })
const tagSearch = ref('')
const months = computed(() =>
  [...new Set(rows.value.map((t) => t.transaction_date.slice(0, 7)).filter(Boolean))]
    .sort()
    .reverse(),
)
const tags = computed(() => [...new Set(rows.value.flatMap((t) => t.tags))].sort())
const merchants = computed(() => [...new Set(rows.value.map(merchantName))].sort())
const filteredTags = computed(() =>
  tags.value.filter((t) => label(t).toLowerCase().includes(tagSearch.value.toLowerCase())),
)
const groups = computed(() =>
  [
    {
      name: 'Labels & transfers',
      tags: filteredTags.value.filter((t) => /UNSURE|UNTAGGED|transfer|incoming/.test(t)),
    },
    {
      name: 'Spending categories',
      tags: filteredTags.value.filter((t) => !/UNSURE|UNTAGGED|transfer|incoming/.test(t)),
    },
  ].filter((g) => g.tags.length),
)
const draftCount = computed(() => filterScope(rows.value, { ...scope.value, ...draft }).length)
const active = computed(
  () =>
    scope.value.tags.length +
    Number(!!scope.value.category) +
    Number(!!scope.value.merchant) +
    Number(scope.value.transfers),
)
const selectedDate = computed(() => {
  for (const key of ['six', 'all', 'latest', 'complete']) {
    const r = presetRange(key, min.value, max.value)
    if (r.start === scope.value.start && r.end === scope.value.end) return key
  }
  const m = scope.value.start.slice(0, 7)
  if (m) {
    const r = monthRange(m, min.value, max.value)
    if (r.start === scope.value.start && r.end === scope.value.end) return 'month:' + m
  }
  return 'custom'
})
function openCustomDates() {
  start.value = scope.value.start
  end.value = scope.value.end
  custom.value = true
}
function applyCustomDates() {
  if (dateError.value) return
  setRange(start.value, end.value)
  custom.value = false
}
function chooseDate(event: Event) {
  const key = (event.target as HTMLSelectElement).value
  if (key === 'custom') {
    start.value = scope.value.start
    end.value = scope.value.end
    custom.value = true
  } else {
    custom.value = false
    key.startsWith('month:') ? month(key.slice(6)) : preset(key)
  }
}
function openFilters() {
  Object.assign(draft, {
    tags: [...scope.value.tags],
    transfers: scope.value.transfers,
    merchant: scope.value.merchant,
  })
  tagSearch.value = ''
  filterDialog.value?.showModal()
}
function applyFilters() {
  Object.assign(scope.value, { ...draft, tags: [...draft.tags] })
  filterDialog.value?.close()
}
function toggleGroup(group: string[], checked: boolean) {
  draft.tags = checked
    ? [...new Set([...draft.tags, ...group])]
    : draft.tags.filter((t) => !group.includes(t))
}
</script>
<template>
  <section class="scope-section" aria-label="Analysis scope">
    <div class="toolbar">
      <div class="date-control">
        <CalendarDays :size="17" /><label class="sr-only" for="date-preset">Date range</label
        ><select id="date-preset" :value="selectedDate" @change="chooseDate">
          <option value="" disabled>Choose date range</option>
          <option value="six">Latest 6 months</option>
          <option value="latest">Latest month available</option>
          <option value="complete">Latest complete month</option>
          <option value="all">All history</option>
          <option value="custom">Custom dates…</option>
          <optgroup label="Choose a month">
            <option v-for="m in months" :key="m" :value="'month:' + m">{{ monthLabel(m) }}</option>
          </optgroup>
        </select>
      </div>
      <div class="currency-control">
        <label class="sr-only" for="currency">Display currency</label
        ><select id="currency" v-model="displayCurrency">
          <option v-for="c in displayCurrencies" :key="c">{{ c }}</option>
        </select>
      </div>
      <div v-if="currencies.length > 1" class="currency-control">
        <label for="source-currency">Transactions in</label>
        <select id="source-currency" v-model="scope.currency">
          <option v-for="c in currencies" :key="c">{{ c }}</option>
        </select>
      </div>
      <button class="filter-button" @click="openFilters">
        <SlidersHorizontal :size="17" /> Filters
        <span v-if="active" class="counter">{{ active }}</span>
      </button>
      <button
        v-if="selectedDate === 'custom' && !custom"
        class="text-button"
        @click="openCustomDates"
      >
        Edit dates
      </button>
      <button class="text-button reset-button" @click="reset">
        <RotateCcw :size="14" /> Reset view
      </button>
    </div>
    <form
      v-if="custom"
      class="custom-dates panel"
      @submit.prevent="applyCustomDates"
      @keydown.esc="custom = false"
    >
      <label
        >Start date<input
          v-model="start"
          type="date"
          :min="min"
          :max="max"
          :aria-invalid="!!dateError"
          aria-describedby="date-error" /></label
      ><label
        >End date<input
          v-model="end"
          type="date"
          :min="min"
          :max="max"
          :aria-invalid="!!dateError"
          aria-describedby="date-error" /></label
      ><button class="primary" :disabled="!!dateError">Apply dates</button
      ><button type="button" @click="custom = false">Cancel</button>
      <p v-if="dateError" id="date-error" class="error-text">{{ dateError }}</p>
    </form>
    <div class="scope-summary">
      <span>{{ rangeText }}</span
      ><span class="dot-separator">·</span
      ><span>{{
        scope.transfers ? 'Own-account transfers included' : 'Own-account transfers excluded'
      }}</span
      ><span v-if="partial" class="badge amber">Partial month · through {{ dateLabel(max) }}</span>
    </div>
    <p v-if="min && scope.start === min && min.slice(8) !== '01'" class="helper">
      First available month is partial · coverage starts {{ dateLabel(min) }}.
    </p>
    <p v-if="currencies.length > 1" class="helper">
      Showing transactions recorded in {{ scope.currency }}. Original currencies are kept separate.
    </p>
    <div v-if="displayCurrency !== scope.currency" class="conversion" aria-live="polite">
      <p v-if="displayValue(1) !== null && exchangeRates">
        Display conversion: 1 {{ scope.currency }} ≈ {{ displayValue(1)?.toFixed(4) }}
        {{ displayCurrency }}.
        <a href="https://api.nbp.pl/en.html" target="_blank" rel="noopener noreferrer"
          >NBP average rates</a
        >, {{ exchangeRates.effectiveDate }}. These are display estimates using the latest available
        rates, not historical transaction rates or bank fees.
        <span v-if="exchangeRates.stale"
          >The last fetched rates are being used because the latest update failed.</span
        >
      </p>
      <p v-else-if="exchangeStatus === 'pending'">Loading exchange rates…</p>
      <p v-else>
        Conversion is unavailable for this currency right now. Original amounts remain in
        transaction details.
        <button class="text-button" @click="loadExchangeRates">Retry rates</button>
      </p>
    </div>
    <div v-if="active || previous" class="chips">
      <button v-if="previous" class="chip" @click="back">
        <ArrowLeft :size="14" /> Back to {{ dateLabel(previous.start) }} –
        {{ dateLabel(previous.end) }}
      </button>
      <button v-if="scope.category" class="chip" @click="scope.category = ''">
        Category: {{ label(scope.category) }} <X :size="14" /><span class="sr-only"
          >Remove category filter</span
        >
      </button>
      <button v-if="scope.merchant" class="chip" @click="scope.merchant = ''">
        Merchant: {{ scope.merchant }} <X :size="14" /><span class="sr-only"
          >Remove merchant filter</span
        >
      </button>
      <button
        v-for="tag in scope.tags"
        :key="tag"
        class="chip"
        @click="scope.tags = scope.tags.filter((t) => t !== tag)"
      >
        Tag: {{ label(tag) }} <X :size="14" /><span class="sr-only">Remove tag filter</span>
      </button>
      <button v-if="scope.transfers" class="chip" @click="scope.transfers = false">
        Transfers included <X :size="14" />
      </button>
      <button v-if="active" class="text-button" @click="clearFilters">Clear filters</button>
    </div>
    <div class="mode-line">
      <div class="segmented" aria-label="Money view">
        <button
          v-for="mode in ['spending', 'income', 'net'] as const"
          :key="mode"
          :aria-pressed="scope.mode === mode"
          @click="scope.mode = mode"
        >
          {{ mode === 'net' ? 'Net flow' : label(mode) }}
        </button>
      </div>
      <span class="mode-help">{{
        scope.mode === 'spending'
          ? 'Money going out'
          : scope.mode === 'income'
            ? 'Money coming in'
            : 'Incoming minus outgoing'
      }}</span>
    </div>
  </section>
  <dialog ref="filterDialog" class="filter-dialog" aria-labelledby="filters-title">
    <form @submit.prevent="applyFilters">
      <div class="dialog-head">
        <div>
          <p class="eyebrow">ANALYSIS SCOPE</p>
          <h2 id="filters-title">Filter transactions</h2>
        </div>
        <button
          type="button"
          class="icon-button"
          aria-label="Cancel filters"
          @click="filterDialog?.close()"
        >
          <X :size="20" />
        </button>
      </div>
      <div class="dialog-body">
        <label class="check-row"
          ><input v-model="draft.transfers" type="checkbox" />Include own-account transfers</label
        >
        <p class="helper">
          Transfers are excluded by default to avoid counting movement between your accounts.
        </p>
        <label class="field"
          >Merchant<input
            v-model="draft.merchant"
            list="merchant-options"
            placeholder="All merchants (leave empty)" /><datalist id="merchant-options">
            <option v-for="m in merchants" :key="m" :value="m" /></datalist
        ></label>
        <div class="section-heading">
          <h3>Tags</h3>
          <button type="button" class="text-button" @click="draft.tags = []">All tags</button>
        </div>
        <p class="helper">
          {{
            draft.tags.length
              ? `${draft.tags.length} selected · matches ANY selected tag`
              : 'All tags · no tag restriction'
          }}. Other filters combine with AND.
        </p>
        <label class="field"
          >Find a tag<input v-model="tagSearch" type="search" placeholder="Search tags"
        /></label>
        <fieldset v-for="group in groups" :key="group.name" class="tag-group">
          <legend>{{ group.name }}</legend>
          <label class="check-row group-select"
            ><input
              type="checkbox"
              :checked="group.tags.every((t) => draft.tags.includes(t))"
              :indeterminate="
                group.tags.some((t) => draft.tags.includes(t)) &&
                !group.tags.every((t) => draft.tags.includes(t))
              "
              @change="toggleGroup(group.tags, ($event.target as HTMLInputElement).checked)"
            />Select group</label
          >
          <div class="tag-grid">
            <label v-for="t in group.tags" :key="t" class="check-row"
              ><input v-model="draft.tags" type="checkbox" :value="t" />{{ label(t) }}</label
            >
          </div>
        </fieldset>
        <p v-if="!filteredTags.length" class="helper">No tags match your search.</p>
      </div>
      <div class="dialog-actions">
        <button type="button" @click="filterDialog?.close()">Cancel</button
        ><button class="primary">Apply · {{ draftCount.toLocaleString() }} transactions</button>
      </div>
    </form>
  </dialog>
</template>
