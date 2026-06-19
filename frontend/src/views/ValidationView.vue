<template>
  <div class="validation">
    <h1>人工验证</h1>

    <div v-if="loading" class="loading">加载中...</div>
    <div v-else-if="error" class="error">{{ error }}</div>

    <!-- 全部验证完毕 → 显示报告 -->
    <div v-else-if="currentIdx >= results.length" class="empty">
      <div class="done-icon">✓</div>
      <h2>全部验证完毕</h2>
      <div v-if="summary" class="summary-box">
        <div class="summary-row">
          <span>已验证 <strong>{{ summary.total }}</strong> 个字段</span>
          <span>正确 <strong>{{ summary.correct }}</strong> 个</span>
        </div>
        <div class="accuracy">{{ summary.accuracy }}%</div>
        <div class="accuracy-label">整体准确率</div>
        <div class="field-grid">
          <div v-for="(rate, field) in summary.per_field" :key="field" class="field-stat">
            <span class="field-name">{{ fieldLabels[field] || field }}</span>
            <span class="field-rate">{{ rate }}</span>
          </div>
        </div>
      </div>
      <button class="btn btn-primary" @click="reset" style="margin-top:16px">重新验证</button>
    </div>

    <template v-else>
      <!-- 进度 -->
      <div class="progress">
        <div class="progress-bar">
          <div class="progress-fill" :style="{ width: (currentIdx / results.length * 100) + '%' }"></div>
        </div>
        <span class="progress-text">{{ currentIdx + 1 }} / {{ results.length }}</span>
      </div>

      <div class="validation-grid">
        <!-- 左栏：原始对话 -->
        <div class="card conv-preview">
          <div class="card-title">
            <span class="conv-id">{{ currentConv.id }}</span>
            <span class="conv-meta">{{ currentConv.channel }} · {{ currentConv.agent }} · {{ currentConv.turns.length }} 轮</span>
          </div>
          <div class="turns">
            <div v-for="(t, i) in currentConv.turns" :key="i"
              class="turn" :class="t.role === 'user' ? 'turn-user' : 'turn-agent'">
              <span class="turn-role">{{ t.role === 'user' ? '👤' : '💁' }}</span>
              <span class="turn-text">{{ t.content }}</span>
            </div>
          </div>
        </div>

        <!-- 右栏：验证表单 -->
        <div class="card validate-form">
          <div class="card-title">提取结果验证</div>

          <div v-for="f in fields" :key="f.key" class="field-item"
            :class="{ 'field-verified': verified[f.key] !== undefined }">
            <div class="field-header">
              <span class="field-label">{{ f.label }}</span>
              <span class="field-value">{{ formatValue(currentResult[f.key]) }}</span>
            </div>
            <div class="field-actions">
              <button class="vote-btn yes-btn"
                :class="{ active: verified[f.key] === true }"
                @click="setVote(f.key, true)">✓ 正确</button>
              <button class="vote-btn no-btn"
                :class="{ active: verified[f.key] === false }"
                @click="setVote(f.key, false)">✗ 错误</button>
            </div>
          </div>

          <div class="submit-area">
            <div v-if="voteCount > 0" class="vote-count">已评 {{ voteCount }} / {{ fields.length }} 个字段</div>
            <button class="btn btn-primary btn-submit"
              :disabled="voteCount === 0"
              @click="submitValidation">
              提交验证
            </button>
            <button class="btn btn-skip" @click="skipConv">
              跳过此条
            </button>
          </div>
        </div>
      </div>

      <!-- 实时准确率摘要 -->
      <div v-if="summary && summary.total > 0" class="summary-strip">
        当前准确率: <strong>{{ summary.accuracy }}%</strong>
        （{{ summary.correct }}/{{ summary.total }}）
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import {
  getConversations, getResults,
  validateBatch, getValidationSummary
} from '../api/index.js'

const conversations = ref([])
const results = ref([])
const summary = ref(null)
const loading = ref(true)
const error = ref('')
const currentIdx = ref(0)
const verified = ref({})
const submitting = ref(false)

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

const currentConv = computed(() => {
  if (currentIdx.value >= results.value.length) return null
  const id = results.value[currentIdx.value]?.conversation_id
  return conversations.value.find(c => c.id === id) || null
})

const currentResult = computed(() => results.value[currentIdx.value] || {})

const voteCount = computed(() => Object.keys(verified.value).length)

async function load() {
  loading.value = true
  try {
    const [cRes, rRes, sRes] = await Promise.all([
      getConversations(),
      getResults(),
      getValidationSummary(),
    ])
    conversations.value = cRes.data.conversations
    results.value = rRes.data.results
    summary.value = sRes.data
    if (results.value.length === 0) {
      error.value = '暂无提取结果，请先提取对话'
    }
  } catch (e) {
    error.value = '加载失败: ' + (e.response?.data?.detail || e.message)
  } finally {
    loading.value = false
  }
}

function setVote(key, value) {
  verified.value = { ...verified.value, [key]: value }
}

async function submitValidation() {
  const convId = currentResult.value.conversation_id
  if (!convId || submitting.value) return

  submitting.value = true
  try {
    const batch = Object.entries(verified.value).map(([field, isCorrect]) => ({
      conv_id: convId,
      field,
      is_correct: isCorrect,
    }))
    await validateBatch(batch)
    const sRes = await getValidationSummary()
    summary.value = sRes.data
    verified.value = {}
    if (currentIdx.value < results.value.length - 1) {
      currentIdx.value++
    } else {
      currentIdx.value++  // triggers the "all done" state
    }
  } catch (e) {
    alert('提交失败: ' + (e.response?.data?.detail || e.message))
  } finally {
    submitting.value = false
  }
}

function skipConv() {
  verified.value = {}
  if (currentIdx.value < results.value.length - 1) {
    currentIdx.value++
  } else {
    currentIdx.value++
  }
}

function reset() {
  currentIdx.value = 0
  verified.value = {}
  load()
}

function formatValue(v) {
  if (Array.isArray(v)) return v.join(', ')
  if (typeof v === 'boolean') return v ? '是' : '否'
  return v || '-'
}
onMounted(() => {
  load()
})
</script>

<style scoped>
.validation h1 { margin-bottom: 20px; }
.loading, .error { color: #666; padding: 20px; }
.empty { text-align: center; padding: 60px 20px; color: #666; }
.done-icon { font-size: 48px; color: #34c759; margin-bottom: 12px; }
.empty h2 { margin-bottom: 16px; }

/* Progress */
.progress { display: flex; align-items: center; gap: 12px; margin-bottom: 20px; }
.progress-bar { flex: 1; height: 6px; background: #e0e0e0; border-radius: 3px; overflow: hidden; }
.progress-fill { height: 100%; background: #007aff; border-radius: 3px; transition: width 0.3s; }
.progress-text { font-size: 13px; color: #888; flex-shrink: 0; }

/* Grid */
.validation-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 16px; }
.card { background: #fff; border-radius: 10px; padding: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.08); }
.card-title { display: flex; align-items: center; gap: 10px; margin-bottom: 12px; font-weight: 600; font-size: 14px; }
.conv-id { font-weight: 700; color: #1a1a2e; }
.conv-meta { font-size: 12px; color: #888; font-weight: 400; }

/* Turns */
.turns { max-height: 400px; overflow-y: auto; display: flex; flex-direction: column; gap: 6px; }
.turn { display: flex; gap: 8px; padding: 6px 8px; border-radius: 6px; font-size: 13px; line-height: 1.5; }
.turn-user { background: #f0f4ff; color: #1a1a2e; }
.turn-agent { background: #f5f5f7; color: #555; }
.turn-role { flex-shrink: 0; }
.turn-text { flex: 1; }

/* Fields */
.field-item { display: flex; align-items: center; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #f0f0f0; }
.field-item:last-child { border-bottom: none; }
.field-header { flex: 1; display: flex; flex-direction: column; gap: 2px; }
.field-label { font-size: 12px; color: #888; }
.field-value { font-size: 14px; color: #1d1d1f; word-break: break-all; }
.field-verified { background: #f8f9fa; border-radius: 6px; padding: 10px; margin: 4px -10px; border-bottom: none !important; }
.field-actions { display: flex; gap: 6px; flex-shrink: 0; margin-left: 12px; }

/* Vote buttons */
.vote-btn { padding: 5px 12px; border: 1px solid #ddd; border-radius: 6px; cursor: pointer; font-size: 12px; background: #fff; transition: all 0.15s; }
.vote-btn:hover { border-color: #007aff; }
.vote-btn.active { border-width: 2px; }
.yes-btn.active { border-color: #34c759; background: #e8f8ed; color: #1a7a3a; }
.no-btn.active { border-color: #ff3b30; background: #fde8e7; color: #a31e1a; }

/* Submit */
.submit-area { display: flex; align-items: center; gap: 8px; margin-top: 16px; padding-top: 12px; border-top: 1px solid #e0e0e0; }
.vote-count { font-size: 12px; color: #888; flex: 1; }
.btn { padding: 8px 20px; border: none; border-radius: 8px; cursor: pointer; font-size: 13px; font-weight: 600; }
.btn-primary { background: #007aff; color: #fff; }
.btn-primary:disabled { background: #80bdff; cursor: not-allowed; }
.btn-primary:hover:not(:disabled) { background: #0056b3; }
.btn-skip { background: #f0f0f0; color: #666; }
.btn-skip:hover { background: #e0e0e0; }
.btn-submit { flex: 1; }

/* Summary strip */
.summary-strip { background: #fff; border-radius: 8px; padding: 12px 16px; font-size: 14px; color: #666; box-shadow: 0 1px 3px rgba(0,0,0,0.06); display: inline-block; }
.summary-strip strong { color: #1d1d1f; }

/* Done summary box */
.summary-box { background: #fff; border-radius: 12px; padding: 24px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); max-width: 420px; margin: 0 auto; }
.summary-row { display: flex; justify-content: center; gap: 24px; font-size: 14px; color: #555; margin-bottom: 16px; }
.accuracy { font-size: 48px; font-weight: 800; color: #1a1a2e; }
.accuracy-label { font-size: 14px; color: #888; margin-bottom: 20px; }
.field-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
.field-stat { display: flex; justify-content: space-between; padding: 6px 12px; background: #f8f9fa; border-radius: 6px; font-size: 13px; }
.field-name { color: #666; }
.field-rate { font-weight: 600; color: #1d1d1f; }

@media (max-width: 768px) {
  .validation-grid { grid-template-columns: 1fr; }
}
</style>
