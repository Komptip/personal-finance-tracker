export type CategoryTransaction = {
  transaction_date: string
  amount: number
  tags: string[]
}

export type CategorySort = 'desc' | 'asc'
export type CategoryMode = 'spending' | 'income' | 'net'

const primaryCategoryPriority = [
  'rent_payment',
  'own_account_transfer',
  'taxes_zus',
  'cash_withdrawal',
  'peer_transfer_out',
  'food_delivery',
  'restaurant_fast_food',
  'groceries',
  'convenience_store',
  'taxi_rideshare',
  'public_transport',
  'software_ai_dev',
  'telecom_internet',
  'education',
  'accounting_business',
  'clothing',
  'electronics',
  'health_beauty',
  'fitness_sport',
  'home_household',
  'travel_lodging',
  'entertainment_nightlife',
  'income_incoming',
  'UNTAGGED',
]

export function primaryCategory(transaction: Pick<CategoryTransaction, 'tags'>): string {
  const tags = transaction.tags.filter((tag) => tag !== 'UNSURE')
  return (
    primaryCategoryPriority.find((category) => tags.includes(category)) || tags[0] || 'UNTAGGED'
  )
}

export function rankCategoryTotals(
  transactions: CategoryTransaction[],
  options: { month: string; sort: CategorySort; mode: CategoryMode },
) {
  const totals = new Map<string, { category: string; cents: number; count: number }>()

  for (const transaction of transactions) {
    if (
      !transaction.transaction_date ||
      !Number.isFinite(transaction.amount) ||
      transaction.amount === 0
    ) {
      continue
    }
    if (options.month && transaction.transaction_date.slice(0, 7) !== options.month) {
      continue
    }
    if (options.mode === 'spending' && transaction.amount >= 0) {
      continue
    }
    if (options.mode === 'income' && transaction.amount <= 0) {
      continue
    }

    const category = primaryCategory(transaction)
    const bucket = totals.get(category) || { category, cents: 0, count: 0 }
    const amount = options.mode === 'spending' ? Math.abs(transaction.amount) : transaction.amount
    bucket.cents += Math.round(amount * 100)
    bucket.count += 1
    totals.set(category, bucket)
  }

  const direction = options.sort === 'asc' ? 1 : -1
  return [...totals.values()]
    .sort((a, b) => (a.cents - b.cents) * direction || a.category.localeCompare(b.category))
    .map(({ category, cents, count }) => ({ category, total: cents / 100, count }))
}
