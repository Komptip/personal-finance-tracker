import { parseNbpRates, type ExchangeRates } from '../../utils/currency'

let cached: { data: ExchangeRates; fetchedAt: number } | undefined
let pending: Promise<ExchangeRates> | undefined
const cacheDuration = 60 * 60 * 1000

export default defineEventHandler(async () => {
  if (cached && Date.now() - cached.fetchedAt < cacheDuration) return cached.data
  if (!pending) {
    pending = (async () => {
      try {
        // Fixed public endpoint: never send transactions, identifiers or local paths.
        const payload = await $fetch<unknown>(
          'https://api.nbp.pl/api/exchangerates/tables/a/?format=json',
          {
            timeout: 5000,
            retry: 0,
          },
        )
        const data = parseNbpRates(payload)
        cached = { data, fetchedAt: Date.now() }
        return data
      } catch {
        if (cached) return { ...cached.data, stale: true }
        throw createError({
          statusCode: 503,
          statusMessage: 'Exchange rates are temporarily unavailable',
        })
      } finally {
        pending = undefined
      }
    })()
  }
  return pending
})
