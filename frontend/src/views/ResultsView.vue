<template>
  <div class="results">
    <h1>提取结果</h1>

    <div v-if="loading" class="loading">加载中...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else-if="results.length === 0" class="empty">暂无提取结果，请先到「对话列表」页面提取。</div>
    <template v-else>
      <div class="result-count">共 {{ results.length }} 条结果</div>
      <div class="result-list">
        <div v-for="r in results" :key="r.conversation_id" class="result-card">
          <div class="result-header">
            <span class="res-id">{{ r.conversation_id }}</span>
            <span class="badge" :class="'badge-' + r.resolution_status">{{ statusLabel(r.resolution_status) }}</span>
            <span class="badge" :class="'badge-' + r.user_sentiment">{{ sentimentLabel(r.user_sentiment) }}</span>
          </div>
          <div class="result-body">
            <div class="field">
              <span class="field-label">摘要</span>
              <span class="field-value">{{ r.user_issue_summary }}</span>
            </div>
            <div class="field">
              <span class="field-label">类别</span>
              <div class="tag-group">
                <span v-for="c in r.issue_categories" :key="c" class="tag">{{ c }}</span>
              </div>
            </div>
            <div class="field">
              <span class="field-label">措施</span>
              <span class="field-value">{{ r.resolution_action || '-' }}</span>
            </div>
            <div class="field-row">
              <span>紧急度: {{ urgencyLabel(r.urgency_level) }}</span>
              <span>跟进: {{ r.requires_follow_up ? '需要' : '无需' }}</span>
              <span>转人工: {{ r.escalation_required ? '是' : '否' }}</span>
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getResults } from '../api/index.js'

const results = ref([])
const loading = ref(true)
const error = ref('')

onMounted(async () => {
  try {
    const res = await getResults()
    results.value = res.data.results
  } catch (e) {
    error.value = '加载失败: ' + (e.response?.data?.detail || e.message)
  } finally {
    loading.value = false
  }
})

function statusLabel(s) {
  const map = { resolved: '已解决', partially_resolved: '部分解决', unresolved: '未解决', pending: '待处理' }
  return map[s] || s
}
function sentimentLabel(s) {
  const map = { angry: '愤怒', negative: '负面', neutral: '中性', positive: '积极' }
  return map[s] || s
}
function urgencyLabel(s) {
  const map = { high: '高', medium: '中', low: '低' }
  return map[s] || s
}
</script>

<style scoped>
.results h1 { margin-bottom: 20px; }
.loading, .error, .empty { color: #666; padding: 20px; }
.result-count { font-size: 14px; color: #888; margin-bottom: 12px; }
.result-list { display: flex; flex-direction: column; gap: 12px; }
.result-card { background: #fff; border-radius: 10px; padding: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.08); }
.result-header { display: flex; align-items: center; gap: 10px; margin-bottom: 12px; }
.res-id { font-weight: 600; font-size: 14px; }
.badge { font-size: 11px; padding: 2px 8px; border-radius: 10px; }
.badge-resolved { background: #d4edda; color: #155724; }
.badge-partially_resolved { background: #fff3cd; color: #856404; }
.badge-unresolved { background: #f8d7da; color: #721c24; }
.badge-pending { background: #e2e3e5; color: #383d41; }
.badge-angry { background: #f8d7da; color: #721c24; }
.badge-negative { background: #fff3cd; color: #856404; }
.badge-neutral { background: #e2e3e5; color: #383d41; }
.badge-positive { background: #d4edda; color: #155724; }
.result-body { display: flex; flex-direction: column; gap: 8px; }
.field { display: flex; gap: 8px; font-size: 13px; }
.field-label { color: #888; flex-shrink: 0; width: 40px; }
.field-value { flex: 1; color: #333; }
.field-row { display: flex; gap: 16px; font-size: 12px; color: #888; }
.tag-group { display: flex; flex-wrap: wrap; gap: 4px; }
.tag { background: #e8f0fe; color: #1967d2; padding: 2px 8px; border-radius: 4px; font-size: 12px; }
</style>
