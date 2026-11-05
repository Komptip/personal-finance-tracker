import type { TransactionData } from '~/utils/transactionData'
import {
  filterScope,
  presetRange,
  monthRange,
  dateLabel,
  type Scope,
  type Transaction,
  type LabelFilter,
  type Grouping,
} from '~/utils/analysis'

export function useAnalysis() {
  const data = useState<TransactionData | null>('finance-data', () => null)
  const status = useState<'idle' | 'pending' | 'success' | 'error'>('finance-status', () => 'idle')
  const scope = useState<Scope>('finance-scope', () => ({
    start: '',
    end: '',
    mode: 'spending',
    currency: 'PLN',
    category: '',
    merchant: '',
    tags: [],
    transfers: false,
  }))
  const previous = useState<{ start: string; end: string } | null>('finance-previous', () => null)
  const grouping = useState<Grouping>('finance-grouping', () => 'month')
  const rank = useState<'desc' | 'asc'>('finance-ranking', () => 'desc')
  const resetVersion = useState('finance-reset-version', () => 0)
  const ledger = useState('finance-ledger', () => ({
    search: '',
    sort: 'newest',
    page: 1,
    label: '' as LabelFilter,
  }))
  const rows = computed(() => data.value?.transactions || [])
  const currencies = computed(() =>
    [...new Set(rows.value.map((row) => row.currency || 'PLN'))].sort((a, b) =>
      a === 'PLN' ? -1 : b === 'PLN' ? 1 : a.localeCompare(b),
    ),
  )
  const min = computed(() => data.value?.meta.minDate || '')
  const max = computed(() => data.value?.meta.maxDate || '')
  const matching = computed(() => filterScope(rows.value, scope.value))
  const rangeText = computed(
    () => `${dateLabel(scope.value.start)} – ${dateLabel(scope.value.end)}`,
  )
  const partial = computed(
    () =>
      scope.value.end &&
      scope.value.end === max.value &&
      new Date(scope.value.end + 'T12:00:00Z').getUTCDate() !==
        new Date(
          Number(scope.value.end.slice(0, 4)),
          Number(scope.value.end.slice(5, 7)),
          0,
        ).getDate(),
  )
  async function load() {
    status.value = 'pending'
    try {
      data.value = await $fetch<TransactionData>('/api/transactions')
      if (currencies.value.length && !currencies.value.includes(scope.value.currency))
        scope.value.currency = currencies.value[0]
      if (!scope.value.start) Object.assign(scope.value, presetRange('six', min.value, max.value))
      status.value = 'success'
    } catch {
      status.value = 'error'
    }
  }
  function setRange(start: string, end: string, remember = false) {
    previous.value = remember ? { start: scope.value.start, end: scope.value.end } : null
    scope.value.start = start
    scope.value.end = end
    ledger.value.page = 1
  }
  function preset(key: string) {
    const r = presetRange(key, min.value, max.value)
    setRange(r.start, r.end)
  }
  function month(key: string) {
    const r = monthRange(key, min.value, max.value)
    setRange(r.start, r.end)
  }
  function back() {
    if (previous.value) {
      const r = previous.value
      setRange(r.start, r.end)
    }
  }
  function clearFilters() {
    Object.assign(scope.value, { category: '', merchant: '', tags: [], transfers: false })
    ledger.value.label = ''
  }
  function reset() {
    clearFilters()
    preset('six')
    scope.value.mode = 'spending'
    grouping.value = 'month'
    rank.value = 'desc'
    ledger.value = { search: '', sort: 'newest', page: 1, label: '' }
    resetVersion.value++
  }
  function money(value: number, currency = scope.value.currency) {
    return new Intl.NumberFormat('en-GB', {
      style: 'currency',
      currency,
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(value)
  }
  function originalMoney(t: Transaction) {
    return new Intl.NumberFormat('en-GB', {
      style: 'currency',
      currency: t.currency || 'PLN',
      minimumFractionDigits: 2,
    }).format(t.amount)
  }
  async function evidence(options: Partial<Scope> = {}, kind: LabelFilter = '') {
    Object.assign(scope.value, options)
    ledger.value = { search: '', sort: 'newest', page: 1, label: kind }
    await navigateTo('/transactions')
  }
  return {
    data,
    status,
    scope,
    rows,
    currencies,
    min,
    max,
    matching,
    rangeText,
    partial,
    load,
    previous,
    grouping,
    rank,
    resetVersion,
    ledger,
    preset,
    month,
    setRange,
    back,
    clearFilters,
    reset,
    money,
    originalMoney,
    evidence,
  }
}
