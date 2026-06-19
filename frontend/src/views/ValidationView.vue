<template>
  <div class="validation">
    <h1>人工验证</h1>

    <div v-if="loading" class="loading">加载中...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else-if="pendingList.length === 0" class="empty">
      所有对话已验证完毕！
      <div v-if="summary" class="summary-box">
        <h3>准确率报告</h3>
        <p>已验证 {{ summary.total }} 个字段，正确 {{ summary.correct }} 个</p>
        <p class="accuracy">整体准确率: <strong>{{ summary.accuracy }}%</strong></p>
        <div v-for="(rate, field) in summary.per_field" :key="field" class="field-row">
          <span class="field-name">{{ fieldLabels[field] || field }}</span>
          <span class="field-rate">{{ rate }}</span>
        </div>
      </div>
    </div>
    <template v-else>
      <div class="progress">已验证 {{ validatedCount }} / {{ totalCount }} 条</div>

      <div class="conv-preview" v-if="currentConv">
        <div class="preview-header">
          <span class="pv-id">{{ convId }}</span>
          <span>{{ currentConv.channel }} · {{ currentConv.agent }}</span>
        </div>
        <div class="preview-turns">
          <div v-for="(t, i) in currentConv.turns" :key="i" class="pv-turn"
            :class="t.role === 'user' ? 'pv-user' : 'pv-agent'">
            <span class="pv-role">{{ t.role === 'user' ? '👤' : '💁' }}</span>
            <span>{{ t.content }}</span>
          </div>
        </div>
      </div>

      <div class="current-result" v-if="currentResult">
        <h3>提取结果</h3>
        <div v-for="f in fields" :key="f.key" class="validation-item">
          <div class="val-field">
            <span class="val-label">{{ f.label }}</span>
            <span class="val-value">{{ formatValue(currentResult[f.key]) }}</span>
          </div>
          <div class="val-actions">
            <button class="btn btn-yes" @click="validate(f.key, true)">✓ 正确</button>
            <button class="btn btn-no" @click="validate(f.key, false)">✗ 错误</button>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { getConversations, getResults, validateField, getValidationSummary } from '../api/index.js'

const conversations = ref([])
const results = ref([])
const summary = ref(null)
const loading = ref(true)
const error = ref('')
const currentIndex = ref(0)

const fields = [
  { key: 'issue_categories', label: '问题类别' },
  { key: 'resolution_status', label: '解决状态' },
  { key: 'resolution_action', label: '处理措施' },
  { key: 'user_sentiment', label: '用户情绪' },
  { key: 'urgency_level', label: '紧急程度' },
  { key: 'requires_follow_up', label: '需跟进' },
  { key: 'escalation_required', label: '转人工' },
]

const fieldLabels = Object.fromEntries(fields.map(f => [f.key, f.label]))

const pendingList = computed(() => {
  if (results.value.length === 0) return []
  const rIds = new Set(results.value.map(r => r.conversation_id))
  return conversations.value.filter(c => rIds.has(c.id))
})

const totalCount = computed(() => pendingList.value.length)
const convId = computed(() => pendingList.value[currentIndex.value]?.id || '')
const currentConv = computed(() => conversations.value.find(c => c.id === convId.value))
const currentResult = computed(() => results.value.find(r => r.conversation_id === convId.value))
const validatedCount = computed(() => currentIndex.value)

onMounted(load)

async function load() {
  try {
    const [cRes, rRes, sRes] = await Promise.all([
      getConversations(),
      getResults(),
      getValidationSummary(),
    ])
    conversations.value = cRes.data.conversations
    results.value = rRes.data.results
    summary.value = sRes.data
    if (sRes.data?.total) {
      error.value = ''
    }
  } catch (e) {
    error.value = '加载失败: ' + (e.response?.data?.detail || e.message)
  } finally {
    loading.value = false
  }
}

async function validate(field, isCorrect) {
  await validateField(convId.value, field, isCorrect)
  const sRes = await getValidationSummary()
  summary.value = sRes.data

  // Check if all fields for this conversation are done
  const allFields = fields.map(f => f.key)
  const convValidations = summary.value.per_field
  const doneFields = Object.keys(convValidations).filter(k =>
    allFields.includes(k)
  )
  if (doneFields.length >= allFields.length && currentIndex.value < pendingList.value.length - 1) {
    currentIndex.value++
  } else if (doneFields.length >= allFields.length) {
    currentIndex.value++
  }
}

function formatValue(v) {
  if (Array.isArray(v)) return v.join(', ')
  if (typeof v === 'boolean') return v ? '是' : '否'
  return v || '-'
}
</script>

<style scoped>
.validation h1 { margin-bottom: 20px; }
.loading, .error, .empty { color: #666; padding: 20px; }
.summary-box { background: #fff; border-radius: 10px; padding: 20px; margin-top: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.08); max-width: 480px; }
.summary-box h3 { margin-bottom: 12px; }
.accuracy { font-size: 18px; margin: 8px 0; }
.field-row { display: flex; justify-content: space-between; padding: 4px 0; font-size: 14px; }
.field-name { color: #555; }
.progress { font-size: 14px; color: #888; margin-bottom: 16px; }
.conv-preview { background: #fff; border-radius: 10px; padding: 16px; margin-bottom: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.08); }
.preview-header { display: flex; gap: 12px; margin-bottom: 12px; font-size: 14px; }
.pv-id { font-weight: 600; }
.pv-turn { display: flex; gap: 8px; padding: 4px 0; font-size: 13px; }
.pv-user { color: #1a1a2e; }
.pv-agent { color: #555; }
.pv-role { flex-shrink: 0; }
.current-result { background: #fff; border-radius: 10px; padding: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.08); }
.current-result h3 { margin-bottom: 12px; font-size: 15px; }
.validation-item { display: flex; justify-content: space-between; align-items: center; padding: 8px 0; border-bottom: 1px solid #f0f0f0; }
.val-field { flex: 1; display: flex; gap: 8px; font-size: 13px; }
.val-label { color: #888; width: 70px; flex-shrink: 0; }
.val-value { color: #333; }
.val-actions { display: flex; gap: 6px; flex-shrink: 0; }
.btn { padding: 4px 12px; border: none; border-radius: 6px; cursor: pointer; font-size: 12px; font-weight: 500; }
.btn-yes { background: #d4edda; color: #155724; }
.btn-yes:hover { background: #c3e6cb; }
.btn-no { background: #f8d7da; color: #721c24; }
.btn-no:hover { background: #f5c6cb; }
</style>
