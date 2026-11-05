<script setup lang="ts">
import { ChevronDown } from 'lucide-vue-next'
import { primaryCategory } from '~/utils/categoryRanking'
import { label, merchantName, dateLabel, type Transaction } from '~/utils/analysis'
defineProps<{ transactions: Transaction[]; reason?: string }>()
const { money, originalMoney } = useAnalysis()
</script>
<template>
  <div class="transaction-list">
    <div class="ledger-labels" aria-hidden="true">
      <span>Date</span><span>Merchant / description</span><span>Category</span><span>Amount</span
      ><span />
    </div>
    <details
      v-for="(t, index) in transactions"
      :key="t.transaction_id + t.transaction_date + index"
      class="transaction"
    >
      <summary>
        <span class="transaction-date">{{ dateLabel(t.transaction_date) }}</span
        ><span class="transaction-name"
          ><strong>{{ merchantName(t) }}</strong
          ><span v-if="reason" class="helper">{{ reason }}</span></span
        ><span class="transaction-category"
          >{{ label(primaryCategory(t)) }}
          <span v-if="t.tags.includes('UNSURE')" class="badge amber">Needs checking</span></span
        ><span class="transaction-amount" :class="{ positive: t.amount > 0 }"
          >{{ t.amount > 0 ? '+' : '' }}{{ money(t.amount) }}</span
        ><ChevronDown :size="15" class="row-chevron" /><span class="sr-only"
          >Show transaction details</span
        >
      </summary>
      <div class="transaction-details">
        <div>
          <span class="detail-label">ORIGINAL DESCRIPTION</span>
          <p>{{ t.description || t.title || 'No description supplied' }}</p>
          <p v-if="t.title && t.title !== t.description"><strong>Title:</strong> {{ t.title }}</p>
        </div>
        <dl>
          <div>
            <dt>Original amount</dt>
            <dd>{{ originalMoney(t) }}</dd>
          </div>
          <div>
            <dt>Date & time</dt>
            <dd>{{ dateLabel(t.transaction_date) }} {{ t.transaction_time }}</dd>
          </div>
          <div>
            <dt>Transaction ID</dt>
            <dd>{{ t.transaction_id || 'Not supplied' }}</dd>
          </div>
          <div>
            <dt>Location</dt>
            <dd>{{ t.location || 'Not supplied' }}</dd>
          </div>
          <div>
            <dt>Source reference</dt>
            <dd>
              {{ t.source_file || 'Not supplied'
              }}{{ t.source_page ? ' · page ' + t.source_page : '' }}
            </dd>
          </div>
          <div>
            <dt>Statement period</dt>
            <dd>
              {{
                t.statement_period_start
                  ? dateLabel(t.statement_period_start) +
                    ' – ' +
                    dateLabel(t.statement_period_end || '')
                  : 'Not supplied'
              }}
            </dd>
          </div>
        </dl>
        <div class="chips">
          <span v-for="tag in t.tags" :key="tag" class="badge">{{ label(tag) }}</span
          ><span v-if="!t.tags.length" class="badge">No tags</span>
        </div>
        <p class="helper">
          Labels are inferred and have not been verified. Original records are read-only.
        </p>
      </div>
    </details>
  </div>
</template>
