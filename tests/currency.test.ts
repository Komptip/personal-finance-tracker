import assert from 'node:assert/strict'
import { test } from 'node:test'
import { convertCurrency, parseNbpRates } from '../utils/currency'
import { filterScope, type Scope, type Transaction } from '../utils/analysis'

// Deliberately simple synthetic rates, never used by the application.
const exchange = parseNbpRates([
  {
    effectiveDate: '2026-01-01',
    rates: [
      { code: 'EUR', mid: 4 },
      { code: 'USD', mid: 5 },
      { code: 'UAH', mid: 0.1 },
    ],
  },
])

test('converts PLN display values into EUR, USD and UAH', () => {
  assert.equal(convertCurrency(100, 'PLN', 'EUR', exchange), 25)
  assert.equal(convertCurrency(100, 'PLN', 'USD', exchange), 20)
  assert.equal(convertCurrency(100, 'PLN', 'UAH', exchange), 1000)
  assert.equal(convertCurrency(-100, 'PLN', 'EUR', exchange), -25)
})
test('cross-currency conversion uses PLN as the reference', () => {
  assert.equal(convertCurrency(10, 'EUR', 'USD', exchange), 8)
  assert.equal(convertCurrency(10, 'EUR', 'PLN', exchange), 40)
})
test('same-currency display works offline, missing FX never becomes a guessed rate', () => {
  assert.equal(convertCurrency(100, 'PLN', 'PLN', null), 100)
  assert.equal(convertCurrency(100, 'PLN', 'EUR', null), null)
  assert.equal(convertCurrency(100, 'XYZ', 'PLN', exchange), null)
})
test('rejects incomplete or invalid rate tables', () => {
  assert.throws(() => parseNbpRates([]))
  assert.throws(() =>
    parseNbpRates([{ effectiveDate: '2026-01-01', rates: [{ code: 'EUR', mid: 0 }] }]),
  )
})
test('changing display currency does not filter away PLN transactions or mutate amounts', () => {
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
  const original: Transaction = {
    transaction_date: '2026-01-01',
    transaction_id: 'demo-fx',
    amount: -100,
    currency: 'PLN',
    tags: [],
    counterparty: 'DEMO',
    title: '',
    description: '',
    location: '',
  }
  const matching = filterScope([original], scope)
  assert.equal(matching.length, 1)
  assert.equal(convertCurrency(matching[0].amount, scope.currency, 'EUR', exchange), -25)
  assert.equal(original.amount, -100)
  assert.equal(original.currency, 'PLN')
})
