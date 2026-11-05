<script setup lang="ts">
const { status, rows, load } = useAnalysis()
</script>
<template>
  <section
    v-if="status === 'pending' || status === 'idle'"
    class="panel state"
    aria-busy="true"
    aria-live="polite"
  >
    <div class="skeleton" />
    <h2>Loading transaction history</h2>
    <p>Preparing your local overview…</p>
  </section>
  <section v-else-if="status === 'error'" class="panel state" role="alert">
    <h2>Transaction history could not be loaded</h2>
    <p>Check your local import file, then retry. Dates, amounts and currencies must be valid.</p>
    <button class="primary" @click="load">Retry</button>
  </section>
  <section v-else-if="!rows.length" class="panel state">
    <h2>No transactions available</h2>
    <p>Import a bank export using the project import guide, then reload this page.</p>
  </section>
  <slot v-else />
</template>
