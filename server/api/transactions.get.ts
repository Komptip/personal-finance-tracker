import { readFile } from 'node:fs/promises'
import { resolve } from 'node:path'
import Papa from 'papaparse'
import { parseTransactionRows } from '../../utils/transactionData'

export default defineEventHandler(async (event) => {
  setHeader(event, 'Cache-Control', 'no-store')
  const config = useRuntimeConfig(event)
  const path = resolve(process.cwd(), config.dataFile)
  let csv: string
  try {
    csv = await readFile(path, 'utf-8')
  } catch (error) {
    if ((error as NodeJS.ErrnoException).code === 'ENOENT') {
      return { transactions: [], meta: { count: 0, minDate: null, maxDate: null, demo: false } }
    }
    throw createError({ statusCode: 500, statusMessage: 'Local dataset could not be read' })
  }
  const parsed = Papa.parse<Record<string, string>>(csv, { header: true, skipEmptyLines: 'greedy' })
  if (parsed.errors.length) {
    throw createError({
      statusCode: 422,
      statusMessage: 'Invalid dataset CSV. Check the local import.',
    })
  }
  try {
    return parseTransactionRows(parsed.data, parsed.meta.fields || [])
  } catch {
    throw createError({
      statusCode: 422,
      statusMessage:
        'Invalid transaction data. Check dates, amounts, currencies and tags in the local import.',
    })
  }
})
