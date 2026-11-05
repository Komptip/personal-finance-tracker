<script setup lang="ts">
import { ArrowRight, ScanSearch, ChartColumnIncreasing, Layers, CircleHelp } from 'lucide-vue-next'
import { periods, total, label, matchesLabel, type LabelFilter } from '~/utils/analysis'
import { rankCategoryTotals } from '~/utils/categoryRanking'
const { matching, scope, rangeText, money, evidence, preset } = useAnalysis()
const tab = ref('observations')
const kind = ref<LabelFilter>('unsure')
const page = ref(1)
const checking = computed(() => matching.value.filter((t) => matchesLabel(t, kind.value)))
const peak = computed(
  () =>
    periods(matching.value, scope.value, 'month').sort(
      (a, b) => Math.abs(b.total) - Math.abs(a.total),
    )[0],
)
const category = computed(
  () =>
    rankCategoryTotals(matching.value, { month: '', sort: 'desc', mode: scope.value.mode }).sort(
      (a, b) => Math.abs(b.total) - Math.abs(a.total),
    )[0],
)
const unsure = computed(() => matching.value.filter((t) => t.tags.includes('UNSURE')))
watch([kind, () => JSON.stringify(scope.value)], () => (page.value = 1))
</script>
<template>
  <header class="page-head">
    <div>
      <p class="eyebrow">UNDERSTAND THE STORY</p>
      <h1>Review</h1>
      <p>Observations grounded in your current selection.</p>
    </div>
    <span class="read-only"><ScanSearch :size="17" /> Read-only analysis</span>
  </header>
  <ScopeToolbar />
  <DataState
    ><div class="review-tabs segmented">
      <button :aria-pressed="tab === 'observations'" @click="tab = 'observations'">
        Observations</button
      ><button :aria-pressed="tab === 'labels'" @click="tab = 'labels'">Labels to inspect</button>
    </div>
    <template v-if="tab === 'observations'"
      ><p class="review-intro">
        {{ rangeText }} · {{ matching.length.toLocaleString() }} transactions. These describe the
        available records, not a complete assessment of your finances.
      </p>
      <div class="observations">
        <article v-if="peak && matching.length" class="panel observation">
          <span class="observation-icon"><ChartColumnIncreasing :size="24" /></span>
          <div>
            <p class="eyebrow">01 / MONTHLY ACTIVITY</p>
            <h2>
              {{ peak.title }} has the
              {{
                scope.mode === 'net' ? 'largest net movement' : 'highest ' + scope.mode + ' total'
              }}
            </h2>
            <p>
              {{ money(peak.total) }} across {{ peak.count }} transactions, within
              {{ peak.start }} – {{ peak.end }}. Months may have different or partial coverage; this
              is not a like-for-like comparison.
            </p>
            <button class="text-button" @click="evidence({ start: peak.start, end: peak.end })">
              View {{ peak.count }} transactions <ArrowRight :size="16" />
            </button>
          </div>
        </article>
        <article v-if="category" class="panel observation">
          <span class="observation-icon"><Layers :size="24" /></span>
          <div>
            <p class="eyebrow">02 / CATEGORY FOCUS</p>
            <h2>
              {{ label(category.category) }} has the
              {{ scope.mode === 'net' ? 'largest net magnitude' : 'largest matching total' }}
            </h2>
            <p>
              {{ money(category.total) }} across {{ category.count }} transactions<span
                v-if="scope.mode !== 'net' && total(matching, scope.mode)"
              >
                · {{ ((category.total / total(matching, scope.mode)) * 100).toFixed(1) }}% of this
                selection</span
              >. Categories use one primary label per transaction. Incoming labels indicate
              direction, not a verified income source.
            </p>
            <button class="text-button" @click="evidence({ category: category.category })">
              View {{ category.count }} transactions <ArrowRight :size="16" />
            </button>
          </div>
        </article>
        <article v-if="unsure.length" class="panel observation">
          <span class="observation-icon amber"><CircleHelp :size="24" /></span>
          <div>
            <p class="eyebrow">03 / LABEL QUALITY</p>
            <h2>{{ unsure.length }} transactions are marked UNSURE</h2>
            <p>
              These inferred labels may need checking against the original description. Their
              matching {{ scope.mode === 'net' ? 'net flow' : scope.mode }} totals
              {{ money(total(unsure, scope.mode)) }}.
            </p>
            <button class="text-button" @click="evidence({}, 'unsure')">
              View {{ unsure.length }} transactions <ArrowRight :size="16" />
            </button>
          </div>
        </article>
        <div v-if="!matching.length" class="panel state">
          <h2>No observations for this selection</h2>
          <p>Broaden your dates or adjust the filters.</p>
          <button @click="preset('all')">All history</button>
        </div>
      </div></template
    >
    <section v-else class="panel labels-panel">
      <div class="panel-head">
        <div>
          <h2>Labels to inspect</h2>
          <p class="helper">
            Labels are inferred. Inspect original details here; editing is not available.
          </p>
        </div>
        <label class="sr-only" for="label-kind">Label condition</label
        ><select id="label-kind" v-model="kind">
          <option value="unsure">Needs checking</option>
          <option value="uncategorized">Uncategorized</option>
        </select>
      </div>
      <div class="ledger-summary">
        <strong aria-live="polite">{{ checking.length }} matching labels</strong
        ><button v-if="checking.length" class="text-button" @click="evidence({}, kind)">
          Open searchable ledger <ArrowRight :size="16" />
        </button>
      </div>
      <TransactionList
        :transactions="checking.slice((page - 1) * 50, page * 50)"
        :reason="kind === 'unsure' ? 'Marked UNSURE' : 'No primary category'"
      />
      <div v-if="!checking.length" class="state">
        <h2>No matching labels in this selection</h2>
        <p>This applies to the current dates and filters only.</p>
        <button @click="preset('all')">All history</button>
      </div>
      <nav v-if="checking.length > 50" class="pagination" aria-label="Label pages">
        <span
          >{{ (page - 1) * 50 + 1 }}–{{ Math.min(page * 50, checking.length) }} of
          {{ checking.length }}</span
        >
        <div>
          <button :disabled="page === 1" @click="page--">Previous</button
          ><button :disabled="page * 50 >= checking.length" @click="page++">Next</button>
        </div>
      </nav>
    </section>
  </DataState>
</template>
