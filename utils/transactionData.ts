import type { Transaction } from './analysis'

const dateValid = (value: string) => {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value)) return false
  const date = new Date(`${value}T12:00:00Z`)
  return Number.isFinite(date.valueOf()) && date.toISOString().slice(0, 10) === value
}

export function parseTransactionRows(rows: Record<string, string>[], fields: string[]) {
  if (!['transaction_date', 'amount', 'currency'].every((field) => fields.includes(field))) {
    throw new Error('Required columns missing')
  }
  const transactions: Transaction[] = rows.map((row, index) => {
    if (!dateValid(row.transaction_date || '')) throw new Error('Invalid date')
    if (!/^[+-]?\d+(?:\.\d{1,2})?$/.test(row.amount || '')) throw new Error('Invalid amount')
    const amount = Number(row.amount)
    if (!Number.isFinite(amount) || Math.abs(amount) > 1e12) throw new Error('Invalid amount')
    const currency = (row.currency || '').toUpperCase()
    if (!/^[A-Z]{3}$/.test(currency)) throw new Error('Invalid currency')
    const tags: unknown = row.tags ? JSON.parse(row.tags) : []
    if (!Array.isArray(tags) || !tags.every((tag) => typeof tag === 'string')) {
      throw new Error('Invalid tags')
    }
    for (const key of ['statement_period_start', 'statement_period_end']) {
      if (row[key] && !dateValid(row[key])) throw new Error('Invalid statement date')
    }
    // Only return fields used by the UI. Raw statement text, account and card
    // numbers in legacy CSV columns never become extra API fields.
    return {
      transaction_date: row.transaction_date,
      transaction_time: row.transaction_time || '',
      transaction_id: row.transaction_id || `row-${index + 1}`,
      amount,
      currency,
      tags,
      counterparty: row.counterparty || '',
      location: row.location || '',
      title: row.title || '',
      description: row.description || '',
      source_file: row.source_file || '',
      source_page: row.source_page || '',
      statement_period_start: row.statement_period_start || '',
      statement_period_end: row.statement_period_end || '',
    }
  })
  const dates = transactions.map((row) => row.transaction_date).sort()
  return {
    transactions,
    meta: {
      count: transactions.length,
      minDate: dates[0] || null,
      maxDate: dates.at(-1) || null,
      demo:
        transactions.length > 0 &&
        transactions.every((row) => row.source_file === 'generated-demo'),
    },
  }
}

export type TransactionData = ReturnType<typeof parseTransactionRows>
