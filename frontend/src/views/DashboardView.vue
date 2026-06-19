<template>
  <div class="dashboard">
    <h1>仪表盘</h1>
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
          <div class="card-value">{{ stats.user_sentiment?.negative + stats.user_sentiment?.angry || 0 }}</div>
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
import { getStats } from '../api/index.js'

const stats = ref(null)
const loading = ref(true)
const error = ref('')

onMounted(async () => {
  try {
    const res = await getStats()
    stats.value = res.data
  } catch (e) {
    error.value = '加载失败: ' + (e.response?.data?.detail || e.message)
  } finally {
    loading.value = false
  }
})

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
</script>

<style scoped>
.dashboard h1 { margin-bottom: 20px; }
.loading, .error { color: #666; padding: 20px; }
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
