export type ExchangeRates = {
  source: 'NBP'
  effectiveDate: string
  // Each value is the PLN price of one unit of the currency.
  rates: Record<string, number>
  stale: boolean
}

export function parseNbpRates(payload: unknown): ExchangeRates {
  if (!Array.isArray(payload) || payload.length !== 1) throw new Error('Invalid exchange table')
  const table = payload[0]
  if (!/^\d{4}-\d{2}-\d{2}$/.test(table?.effectiveDate || '') || !Array.isArray(table?.rates)) {
    throw new Error('Invalid exchange table')
  }
  const rates: Record<string, number> = { PLN: 1 }
  for (const entry of table.rates) {
    if (
      !/^[A-Z]{3}$/.test(entry.code || '') ||
      typeof entry.mid !== 'number' ||
      !Number.isFinite(entry.mid) ||
      entry.mid <= 0
    )
      throw new Error('Invalid exchange rate')
    if (entry.code !== 'PLN') rates[entry.code] = entry.mid
  }
  if (!['EUR', 'USD', 'UAH'].every((code) => rates[code])) throw new Error('Missing exchange rate')
  return { source: 'NBP', effectiveDate: table.effectiveDate, rates, stale: false }
}

export function convertCurrency(
  amount: number,
  from: string,
  to: string,
  exchange: ExchangeRates | null,
): number | null {
  if (from === to) return amount
  const source = exchange?.rates[from]
  const target = exchange?.rates[to]
  if (!source || !target) return null
  return (amount * source) / target
}
