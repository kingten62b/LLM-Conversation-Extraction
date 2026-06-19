<template>
  <div class="conversations">
    <div class="header">
      <h1>对话列表</h1>
      <button class="btn btn-primary" @click="extractAll" :disabled="extracting">
        {{ extracting ? '提取中...' : '一键全部提取' }}
      </button>
    </div>

    <div v-if="loading" class="loading">加载中...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <template v-else>
      <div v-if="message" class="toast" :class="messageType">{{ message }}</div>

      <div class="filter-bar">
        <button v-for="f in filters" :key="f.key" class="filter-btn"
          :class="{ active: activeFilter === f.key }" @click="activeFilter = f.key">
          {{ f.label }}
        </button>
      </div>

      <div class="conversation-list">
        <div v-for="conv in filteredConvs" :key="conv.id" class="conv-card">
          <div class="conv-header">
            <span class="conv-id">{{ conv.id }}</span>
            <span class="conv-meta">{{ conv.channel }} · {{ conv.agent }} · {{ conv.turns.length }} 轮</span>
            <span v-if="extractedIds.has(conv.id)" class="badge badge-done">已提取</span>
          </div>
          <div class="conv-turns">
            <div v-for="(t, i) in conv.turns.slice(0, 4)" :key="i" class="turn"
              :class="t.role === 'user' ? 'turn-user' : 'turn-agent'">
              <span class="turn-role">{{ t.role === 'user' ? '👤' : '💁' }}</span>
              <span class="turn-text">{{ t.content }}</span>
            </div>
            <div v-if="conv.turns.length > 4" class="turn-more">... 还有 {{ conv.turns.length - 4 }} 轮</div>
          </div>
          <div class="conv-actions">
            <button class="btn btn-sm" @click="extractSingle(conv.id)"
              :disabled="extractingSingle === conv.id">
              {{ extractingSingle === conv.id ? '提取中...' : '提取' }}
            </button>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { getConversations, extractAll as apiExtractAll, extractSingle as apiExtractSingle, getResults } from '../api/index.js'

const conversations = ref([])
const results = ref([])
const loading = ref(true)
const error = ref('')
const extracting = ref(false)
const extractingSingle = ref(null)
const message = ref('')
const messageType = ref('info')
const activeFilter = ref('all')

const filters = [
  { key: 'all', label: '全部' },
  { key: 'done', label: '已提取' },
  { key: 'pending', label: '待提取' },
]

const extractedIds = computed(() => new Set(results.value.map(r => r.conversation_id)))

const filteredConvs = computed(() => {
  if (activeFilter.value === 'all') return conversations.value
  return conversations.value.filter(c => {
    const done = extractedIds.value.has(c.id)
    return activeFilter.value === 'done' ? done : !done
  })
})

async function load() {
  loading.value = true
  try {
    const [cRes, rRes] = await Promise.all([getConversations(), getResults()])
    conversations.value = cRes.data.conversations
    results.value = rRes.data.results
  } catch (e) {
    error.value = '加载失败: ' + (e.response?.data?.detail || e.message)
  } finally {
    loading.value = false
  }
}

function showMessage(text, type = 'info') {
  message.value = text
  messageType.value = type
  setTimeout(() => { message.value = '' }, 3000)
}

async function extractAll() {
  extracting.value = true
  try {
    const res = await apiExtractAll()
    results.value = res.data.results
    showMessage(`全部 ${results.value.length} 条提取完成`, 'success')
  } catch (e) {
    showMessage('提取失败: ' + (e.response?.data?.detail || e.message), 'error')
  } finally {
    extracting.value = false
  }
}

async function extractSingle(convId) {
  extractingSingle.value = convId
  try {
    const res = await apiExtractSingle(convId)
    results.value = [...results.value.filter(r => r.conversation_id !== convId), res.data]
    showMessage(`${convId} 提取完成`, 'success')
  } catch (e) {
    showMessage('提取失败: ' + (e.response?.data?.detail || e.message), 'error')
  } finally {
    extractingSingle.value = null
  }
}

onMounted(load)
</script>

<style scoped>
.header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.header h1 { margin: 0; }
.loading, .error { color: #666; padding: 20px; }
.toast { padding: 10px 16px; border-radius: 8px; margin-bottom: 16px; font-size: 14px; }
.toast.success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
.toast.error { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
.toast.info { background: #d1ecf1; color: #0c5460; border: 1px solid #bee5eb; }

.filter-bar { display: flex; gap: 8px; margin-bottom: 16px; }
.filter-btn { padding: 6px 14px; border: 1px solid #ddd; border-radius: 20px; background: #fff; cursor: pointer; font-size: 13px; }
.filter-btn.active { background: #007aff; color: #fff; border-color: #007aff; }

.conversation-list { display: flex; flex-direction: column; gap: 12px; }
.conv-card { background: #fff; border-radius: 10px; padding: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.08); }
.conv-header { display: flex; align-items: center; gap: 12px; margin-bottom: 12px; }
.conv-id { font-weight: 600; font-size: 14px; }
.conv-meta { font-size: 12px; color: #888; }
.badge { font-size: 11px; padding: 2px 8px; border-radius: 10px; }
.badge-done { background: #d4edda; color: #155724; }

.conv-turns { display: flex; flex-direction: column; gap: 6px; margin-bottom: 12px; }
.turn { display: flex; gap: 8px; font-size: 13px; padding: 4px 0; }
.turn-user { color: #1a1a2e; }
.turn-agent { color: #555; }
.turn-role { flex-shrink: 0; }
.turn-more { font-size: 12px; color: #999; padding: 4px 0; }

.conv-actions { display: flex; gap: 8px; }
.btn { padding: 6px 16px; border-radius: 6px; border: none; cursor: pointer; font-size: 13px; font-weight: 500; }
.btn-primary { background: #007aff; color: #fff; }
.btn-primary:disabled { background: #80bdff; }
.btn-sm { background: #f0f0f0; color: #333; }
.btn-sm:disabled { opacity: 0.5; }
</style>
