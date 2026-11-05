import assert from 'node:assert/strict'
import { test } from 'node:test'
import { filterScope, total, type Scope, type Transaction } from '../utils/analysis'
import { parseTransactionRows } from '../utils/transactionData'

const scope: Scope = {
  start: '',
  end: '',
  mode: 'spending',
  currency: 'PLN',
  category: '',
  merchant: '',
  tags: [],
  transfers: false,
}
const rows: Transaction[] = [
  {
    transaction_date: '2026-01-01',
    transaction_id: 'demo-a',
    amount: -10,
    currency: 'PLN',
    tags: [],
    counterparty: '',
    title: '',
    description: '',
    location: '',
  },
  {
    transaction_date: '2026-01-01',
    transaction_id: 'demo-b',
    amount: -20,
    currency: 'EUR',
    tags: [],
    counterparty: '',
    title: '',
    description: '',
    location: '',
  },
  {
    transaction_date: '2026-01-01',
    transaction_id: 'demo-c',
    amount: -30,
    currency: 'PLN',
    tags: ['own_account_transfer'],
    counterparty: '',
    title: '',
    description: '',
    location: '',
  },
]
test('PLN totals exclude other currencies and own-account transfers', () => {
  assert.equal(total(filterScope(rows, scope), 'spending'), 10)
  assert.equal(total(filterScope(rows, { ...scope, currency: 'EUR' }), 'spending'), 20)
  assert.equal(total(filterScope(rows, { ...scope, transfers: true }), 'spending'), 40)
})
test('the API rejects malformed amounts and dates instead of reporting zero', () => {
  const fields = ['transaction_date', 'amount', 'currency']
  for (const row of [
    { transaction_date: '2026-02-31', amount: '1', currency: 'PLN' },
    { transaction_date: '2026-02-01', amount: 'NaN', currency: 'PLN' },
    { transaction_date: '2026-02-01', amount: '', currency: 'PLN' },
  ])
    assert.throws(() => parseTransactionRows([row], fields))
})
test('the API omits legacy account, card and raw-row fields', () => {
  const result = parseTransactionRows(
    [
      {
        transaction_date: '2026-01-01',
        amount: '-1.00',
        currency: 'PLN',
        statement_account: 'PRIVATE',
        card: 'PRIVATE',
        raw_row: 'PRIVATE',
      },
    ],
    ['transaction_date', 'amount', 'currency'],
  )
  assert.equal(JSON.stringify(result).includes('PRIVATE'), false)
  assert.equal(result.meta.count, 1)
})
