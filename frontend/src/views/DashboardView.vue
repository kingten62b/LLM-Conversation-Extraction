<template>
  <div class="dashboard">
    <h1>仪表盘</h1>

    <!-- 数据源状态 -->
    <div v-if="dataSource" class="data-source-bar" :class="dataSource.source === 'upload' ? 'source-upload' : 'source-default'">
      <span class="source-icon">{{ dataSource.source === 'upload' ? '📤' : '📁' }}</span>
      <span class="source-text">
        {{ dataSource.source === 'upload' ? '使用上传的数据' : '使用默认数据' }}
      </span>
      <button v-if="dataSource.source === 'upload'" class="source-reset-btn" @click="resetData">重置为默认</button>
    </div>

    <!-- 上传区域 -->
    <div class="upload-area"
      :class="{ 'upload-dragover': dragOver }"
      @dragover.prevent="dragOver = true"
      @dragleave.prevent="dragOver = false"
      @drop.prevent="onDrop">
      <div v-if="!uploading" class="upload-inner">
        <div class="upload-icon">☁️</div>
        <div class="upload-title">上传对话数据</div>
        <div class="upload-hint">拖拽 JSON 文件到此处，或点击选择文件</div>
        <input ref="fileInput" type="file" accept=".json" hidden @change="onFileSelect" />
        <button class="upload-btn" @click="$refs.fileInput.click()">选择文件</button>
        <div v-if="uploadMsg" class="upload-msg" :class="uploadMsg.type">{{ uploadMsg.text }}</div>
      </div>
      <div v-else class="upload-inner">
        <div class="upload-spinner"></div>
        <div class="upload-title">上传中...</div>
      </div>
    </div>

    <!-- 统计信息 -->
    <div v-if="loading" class="loading">加载中...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <template v-else-if="stats">
      <div class="stat-cards">
        <div class="card">
          <div class="card-value">{{ stats.total_conversations }}</div>
          <div class="card-label">总对话数</div>
        </div>
        <div class="card">
          <div class="card-value">{{ stats.resolution_rate }}%</div>
          <div class="card-label">解决率</div>
        </div>
        <div class="card">
          <div class="card-value">{{ stats.resolved_count }}</div>
          <div class="card-label">已解决</div>
        </div>
        <div class="card">
          <div class="card-value">{{ (stats.user_sentiment?.negative || 0) + (stats.user_sentiment?.angry || 0) }}</div>
          <div class="card-label">负面情绪</div>
        </div>
      </div>

      <div class="charts-grid">
        <div class="chart-box">
          <h3>问题类别分布</h3>
          <div class="bar-chart">
            <div v-for="(count, cat) in stats.issue_categories" :key="cat" class="bar-row">
              <span class="bar-label">{{ cat }}</span>
              <div class="bar-track">
                <div class="bar-fill" :style="{ width: (count / maxCat * 100) + '%' }"></div>
                <span class="bar-count">{{ count }}</span>
              </div>
            </div>
          </div>
        </div>

        <div class="chart-box">
          <h3>解决状态</h3>
          <div class="bar-chart">
            <div v-for="(count, status) in stats.resolution_status" :key="status" class="bar-row">
              <span class="bar-label">{{ statusLabel(status) }}</span>
              <div class="bar-track">
                <div class="bar-fill" :style="{ width: (count / maxRes * 100) + '%', background: statusColor(status) }"></div>
                <span class="bar-count">{{ count }}</span>
              </div>
            </div>
          </div>
        </div>

        <div class="chart-box">
          <h3>用户情绪</h3>
          <div class="bar-chart">
            <div v-for="(count, se) in stats.user_sentiment" :key="se" class="bar-row">
              <span class="bar-label">{{ sentimentLabel(se) }}</span>
              <div class="bar-track">
                <div class="bar-fill" :style="{ width: (count / maxSen * 100) + '%', background: sentimentColor(se) }"></div>
                <span class="bar-count">{{ count }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { getStats, uploadConversations, getDataSource } from '../api/index.js'

const stats = ref(null)
const loading = ref(true)
const error = ref('')
const dataSource = ref(null)
const uploading = ref(false)
const dragOver = ref(false)
const uploadMsg = ref(null)
const fileInput = ref(null)

async function loadAll() {
  loading.value = true
  try {
    const [sRes, dRes] = await Promise.all([
      getStats(),
      getDataSource(),
    ])
    stats.value = sRes.data
    dataSource.value = dRes.data
  } catch (e) {
    error.value = '加载失败: ' + (e.response?.data?.detail || e.message)
  } finally {
    loading.value = false
  }
}

onMounted(loadAll)

const maxCat = computed(() => Math.max(...Object.values(stats.value?.issue_categories || {}), 1))
const maxRes = computed(() => Math.max(...Object.values(stats.value?.resolution_status || {}), 1))
const maxSen = computed(() => Math.max(...Object.values(stats.value?.user_sentiment || {}), 1))

function statusLabel(s) {
  const map = { resolved: '已解决', partially_resolved: '部分解决', unresolved: '未解决', pending: '待处理' }
  return map[s] || s
}
function statusColor(s) {
  const map = { resolved: '#34c759', partially_resolved: '#ff9f0a', unresolved: '#ff3b30', pending: '#8e8e93' }
  return map[s] || '#8e8e93'
}
function sentimentLabel(s) {
  const map = { angry: '愤怒', negative: '负面', neutral: '中性', positive: '积极' }
  return map[s] || s
}
function sentimentColor(s) {
  const map = { angry: '#ff3b30', negative: '#ff9f0a', neutral: '#8e8e93', positive: '#34c759' }
  return map[s] || '#8e8e93'
}

async function handleUpload(file) {
  if (!file || !file.name.endsWith('.json')) {
    uploadMsg.value = { type: 'error', text: '请选择 JSON 文件' }
    return
  }
  uploading.value = true
  uploadMsg.value = null
  try {
    const res = await uploadConversations(file)
    uploadMsg.value = { type: 'success', text: `上传成功！导入 ${res.data.conversations} 条对话` }
    await loadAll()
  } catch (e) {
    const msg = e.response?.data?.detail || e.message
    uploadMsg.value = { type: 'error', text: `上传失败: ${msg}` }
  } finally {
    uploading.value = false
  }
}

function onDrop(e) {
  dragOver.value = false
  const file = e.dataTransfer.files[0]
  handleUpload(file)
}

function onFileSelect(e) {
  const file = e.target.files[0]
  handleUpload(file)
  e.target.value = ''
}

function resetData() {
  // Just reload — if no uploaded file, data-source returns "default"
  loadAll()
}
</script>

<style scoped>
.dashboard h1 { margin-bottom: 20px; }
.loading, .error { color: #666; padding: 20px; }

/* Data source */
.data-source-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  border-radius: 8px;
  margin-bottom: 16px;
  font-size: 13px;
}
.source-default {
  background: #f0f4ff;
  color: #555;
}
.source-upload {
  background: #e8f8ed;
  color: #1a7a3a;
}
.source-icon { font-size: 16px; }
.source-text { flex: 1; }
.source-reset-btn {
  background: transparent;
  border: 1px solid #ccc;
  border-radius: 6px;
  padding: 4px 12px;
  font-size: 12px;
  color: #666;
  cursor: pointer;
}
.source-reset-btn:hover { border-color: #999; }

/* Upload */
.upload-area {
  background: #fff;
  border: 2px dashed #ccc;
  border-radius: 12px;
  padding: 32px;
  margin-bottom: 24px;
  text-align: center;
  transition: border-color 0.2s, background 0.2s;
  cursor: pointer;
}
.upload-area:hover,
.upload-dragover {
  border-color: #007aff;
  background: #f0f7ff;
}
.upload-inner { display: flex; flex-direction: column; align-items: center; gap: 8px; }
.upload-icon { font-size: 32px; }
.upload-title { font-size: 16px; font-weight: 600; color: #333; }
.upload-hint { font-size: 13px; color: #999; }
.upload-btn {
  padding: 8px 24px;
  background: #007aff;
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  cursor: pointer;
}
.upload-btn:hover { background: #0056b3; }
.upload-msg { font-size: 13px; padding: 6px 12px; border-radius: 6px; }
.upload-msg.success { background: #e8f8ed; color: #1a7a3a; }
.upload-msg.error { background: #fde8e7; color: #a31e1a; }
.upload-spinner {
  width: 24px;
  height: 24px;
  border: 3px solid #e0e0e0;
  border-top-color: #007aff;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* Stat cards */
.stat-cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 16px; margin-bottom: 24px; }
.card { background: #fff; border-radius: 10px; padding: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.08); }
.card-value { font-size: 32px; font-weight: 700; color: #1a1a2e; }
.card-label { font-size: 13px; color: #666; margin-top: 4px; }
.charts-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 16px; }
.chart-box { background: #fff; border-radius: 10px; padding: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.08); }
.chart-box h3 { margin-bottom: 16px; font-size: 15px; color: #333; }
.bar-chart { display: flex; flex-direction: column; gap: 10px; }
.bar-row { display: flex; align-items: center; gap: 12px; }
.bar-label { width: 100px; font-size: 13px; color: #555; flex-shrink: 0; }
.bar-track { flex: 1; height: 24px; background: #f0f0f0; border-radius: 12px; position: relative; overflow: hidden; display: flex; align-items: center; }
.bar-fill { height: 100%; background: #007aff; border-radius: 12px; transition: width 0.5s; }
.bar-count { position: absolute; right: 10px; font-size: 12px; font-weight: 600; color: #555; }
</style>
