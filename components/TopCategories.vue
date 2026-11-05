<script setup lang="ts">
import { ArrowUpRight } from 'lucide-vue-next'
import { rankCategoryTotals } from '~/utils/categoryRanking'
import { label, merchantName, total } from '~/utils/analysis'
const { matching, scope, rank, money, resetVersion } = useAnalysis()
const tab = ref('categories')
const all = ref(false)
watch(resetVersion, () => {
  tab.value = 'categories'
  all.value = false
})
const ranking = computed(() => {
  if (tab.value === 'categories')
    return rankCategoryTotals(matching.value, {
      month: '',
      sort: rank.value,
      mode: scope.value.mode,
    }).map((r) => ({ key: r.category, name: label(r.category), total: r.total, count: r.count }))
  const buckets = new Map<string, typeof matching.value>()
  for (const t of matching.value) {
    const name = merchantName(t)
    const rows = buckets.get(name) || []
    rows.push(t)
    buckets.set(name, rows)
  }
  return [...buckets]
    .map(([name, rows]) => ({
      key: name,
      name,
      total: total(rows, scope.value.mode),
      count: rows.length,
    }))
    .sort(
      (a, b) =>
        (a.total - b.total) * (rank.value === 'desc' ? -1 : 1) || a.name.localeCompare(b.name),
    )
})
const max = computed(() => Math.max(...ranking.value.map((r) => Math.abs(r.total)), 1))
const sum = computed(() => total(matching.value, scope.value.mode))
watch([tab, () => scope.value.start, () => scope.value.end], () => (all.value = false))
function inspect(key: string) {
  if (tab.value === 'categories') scope.value.category = key
  else scope.value.merchant = key
}
</script>
<template>
  <section class="panel breakdown">
    <div class="panel-head">
      <div>
        <p class="eyebrow">WHERE IT {{ scope.mode === 'income' ? 'COMES FROM' : 'GOES' }}</p>
        <h2>Breakdown</h2>
      </div>
      <span class="badge">{{ ranking.length }} {{ tab }}</span>
    </div>
    <div class="ranking-controls">
      <div class="segmented small">
        <button :aria-pressed="tab === 'categories'" @click="tab = 'categories'">Categories</button
        ><button :aria-pressed="tab === 'merchants'" @click="tab = 'merchants'">Merchants</button>
      </div>
      <label class="sr-only" for="rank-order">Ranking order</label
      ><select id="rank-order" v-model="rank">
        <option value="desc">Highest to lowest</option>
        <option value="asc">Lowest to highest</option>
      </select>
    </div>
    <p v-if="scope.mode === 'net'" class="helper">Ordered by signed net amount.</p>
    <div v-if="ranking.length" class="rank-list">
      <button
        v-for="(r, i) in all ? ranking : ranking.slice(0, 6)"
        :key="r.key"
        class="rank-row"
        @click="inspect(r.key)"
      >
        <span class="rank-index">{{ String(i + 1).padStart(2, '0') }}</span
        ><span class="rank-main"
          ><span class="rank-line"
            ><strong>{{ r.name }}</strong
            ><span>{{ money(r.total) }}</span></span
          ><span class="rank-track"
            ><span :style="{ width: (Math.abs(r.total) / max) * 100 + '%' }" /></span
          ><span class="rank-meta"
            >{{ r.count }} transactions<span v-if="scope.mode !== 'net' && sum">
              · {{ ((r.total / sum) * 100).toFixed(1) }}%</span
            ></span
          ></span
        ><ArrowUpRight :size="15" />
      </button>
    </div>
    <div v-else class="empty-inline">No {{ tab }} match this selection.</div>
    <button
      v-if="ranking.length > 6"
      class="text-button show-all"
      :aria-expanded="all"
      @click="all = !all"
    >
      {{ all ? 'Show fewer' : `Show all ${ranking.length} ${tab}` }}
    </button>
  </section>
</template>
