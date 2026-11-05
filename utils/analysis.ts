import { primaryCategory, type CategoryMode } from './categoryRanking'

export type Transaction = {
  transaction_date: string
  transaction_time?: string
  transaction_id: string
  amount: number
  currency?: string
  tags: string[]
  counterparty: string
  location: string
  title: string
  description: string
  source_file?: string
  source_page?: string
  statement_period_start?: string
  statement_period_end?: string
}
export type Scope = {
  start: string
  end: string
  mode: CategoryMode
  currency: string
  category: string
  merchant: string
  tags: string[]
  transfers: boolean
}
export type LabelFilter = '' | 'unsure' | 'uncategorized'
export type Grouping = 'day' | 'week' | 'month'
export const iso = (date: Date) => date.toISOString().slice(0, 10)
export const dateObject = (date: string) => new Date(date + 'T12:00:00Z')
export const label = (value: string) =>
  value === 'UNTAGGED'
    ? 'Uncategorized'
    : value.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())
export const merchantName = (t: Transaction) =>
  t.counterparty || t.location || t.title || 'Unknown merchant'
export const dateLabel = (date: string) =>
  date
    ? new Intl.DateTimeFormat('en-GB', {
        day: 'numeric',
        month: 'short',
        year: 'numeric',
        timeZone: 'UTC',
      }).format(dateObject(date))
    : '—'
export const monthLabel = (date: string) =>
  new Intl.DateTimeFormat('en-GB', { month: 'short', year: 'numeric', timeZone: 'UTC' }).format(
    dateObject(date.slice(0, 7) + '-01'),
  )
export function monthRange(month: string, min: string, max: string) {
  const start = month + '-01'
  const d = dateObject(start)
  d.setUTCMonth(d.getUTCMonth() + 1)
  d.setUTCDate(0)
  return { start: start < min ? min : start, end: iso(d) > max ? max : iso(d) }
}
export function presetRange(preset: string, min: string, max: string) {
  if (!min || !max) return { start: '', end: '' }
  if (preset === 'all') return { start: min, end: max }
  if (preset === 'latest') return monthRange(max.slice(0, 7), min, max)
  if (preset === 'complete') {
    const d = dateObject(max)
    const next = dateObject(max)
    next.setUTCDate(next.getUTCDate() + 1)
    if (next.getUTCDate() !== 1) {
      d.setUTCDate(1)
      d.setUTCMonth(d.getUTCMonth() - 1)
    }
    const range = monthRange(iso(d).slice(0, 7), min, max)
    return range.end < range.start ? { start: min, end: max } : range
  }
  const d = dateObject(max)
  d.setUTCDate(1)
  d.setUTCMonth(d.getUTCMonth() - 5)
  return { start: iso(d) < min ? min : iso(d), end: max }
}
export function filterScope(rows: Transaction[], scope: Scope) {
  return rows.filter(
    (t) =>
      t.transaction_date &&
      Number.isFinite(t.amount) &&
      (!scope.start || t.transaction_date >= scope.start) &&
      (!scope.end || t.transaction_date <= scope.end) &&
      (t.currency || 'PLN') === scope.currency &&
      (scope.transfers || !t.tags.includes('own_account_transfer')) &&
      (scope.mode === 'net' || (scope.mode === 'spending' ? t.amount < 0 : t.amount > 0)) &&
      (!scope.category || primaryCategory(t) === scope.category) &&
      (!scope.merchant || merchantName(t) === scope.merchant) &&
      (!scope.tags.length || scope.tags.some((tag) => t.tags.includes(tag))),
  )
}
export const matchesLabel = (t: Transaction, kind: LabelFilter) =>
  !kind || (kind === 'unsure' ? t.tags.includes('UNSURE') : primaryCategory(t) === 'UNTAGGED')
export const searchMatches = (t: Transaction, query: string) =>
  [t.counterparty, t.location, t.title, t.description, t.transaction_id].some((v) =>
    (v || '').toLocaleLowerCase().includes(query.trim().toLocaleLowerCase()),
  )
export const valueCents = (t: Transaction, mode: CategoryMode) =>
  Math.round((mode === 'spending' ? Math.abs(t.amount) : t.amount) * 100)
export const total = (rows: Transaction[], mode: CategoryMode) =>
  rows.reduce((sum, t) => sum + valueCents(t, mode), 0) / 100
export function periods(rows: Transaction[], scope: Scope, grouping: Grouping) {
  const buckets = new Map<
    string,
    { key: string; start: string; end: string; title: string; cents: number; count: number }
  >()
  if (!scope.start || !scope.end) return []
  const current = dateObject(scope.start)
  if (grouping === 'month') current.setUTCDate(1)
  if (grouping === 'week')
    current.setUTCDate(current.getUTCDate() - ((current.getUTCDay() + 6) % 7))
  while (iso(current) <= scope.end) {
    const key = iso(current)
    const end = new Date(current)
    if (grouping === 'month') {
      end.setUTCMonth(end.getUTCMonth() + 1)
      end.setUTCDate(0)
    }
    if (grouping === 'week') end.setUTCDate(end.getUTCDate() + 6)
    buckets.set(key, {
      key,
      start: key < scope.start ? scope.start : key,
      end: iso(end) > scope.end ? scope.end : iso(end),
      title: grouping === 'month' ? monthLabel(key) : dateLabel(key),
      cents: 0,
      count: 0,
    })
    if (grouping === 'month') current.setUTCMonth(current.getUTCMonth() + 1)
    else current.setUTCDate(current.getUTCDate() + (grouping === 'week' ? 7 : 1))
  }
  for (const t of rows) {
    const d = dateObject(t.transaction_date)
    if (grouping === 'month') d.setUTCDate(1)
    if (grouping === 'week') d.setUTCDate(d.getUTCDate() - ((d.getUTCDay() + 6) % 7))
    const bucket = buckets.get(iso(d))
    if (bucket) {
      bucket.cents += valueCents(t, scope.mode)
      bucket.count++
    }
  }
  return [...buckets.values()].map((b) => ({ ...b, total: b.cents / 100 }))
}
