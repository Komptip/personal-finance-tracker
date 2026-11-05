export default defineNuxtConfig({
  compatibilityDate: '2025-06-20',
  devtools: { enabled: false },
  telemetry: false,
  ssr: true,
  runtimeConfig: {
    dataFile: 'data/processed/tagged_transactions.csv',
  },
  typescript: {
    strict: true,
  },
})
