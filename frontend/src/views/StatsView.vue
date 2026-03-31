<template>
  <div class="stats-view">
    <h2 class="page-title">统计看板</h2>

    <el-row :gutter="24" class="stat-cards">
      <el-col :span="8" v-for="card in cardData" :key="card.label">
        <div class="stat-card" :class="card.class">
          <div class="stat-info">
            <div class="stat-num" :class="card.numClass">{{ card.value }}</div>
            <div class="stat-label">{{ card.icon }} {{ card.label }}</div>
          </div>
        </div>
      </el-col>
    </el-row>

    <div class="section-grid">
      <div class="section heatmap-section">
        <div class="section-header">
          <h3>年度活跃度 (过去365天)</h3>
        </div>
        <div class="heatmap-container">
          <div class="heatmap-wrap">
            <div v-for="(item, i) in stats.heatmap" :key="i"
              class="heatmap-dot"
              :class="{ active: item.count > 0 }"
              :title="`${item.date}: ${item.count}篇`"
            />
          </div>
        </div>
      </div>

      <div class="section tags-section" v-if="stats.top_tags.length">
        <div class="section-header">
          <h3>常用标签 Top 10</h3>
        </div>
        <div class="tag-list">
          <div v-for="t in stats.top_tags" :key="t.tag" class="tag-row">
            <span class="tag-name">#{{ t.tag }}</span>
            <el-progress 
              :percentage="Math.round(t.count / stats.top_tags[0].count * 100)"
              :stroke-width="10" 
              :show-text="false" 
              :color="getProgressColor(t.count)"
              style="flex:1; margin: 0 16px;" 
            />
            <span class="tag-count">{{ t.count }}次</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import api from '@/api'

const stats = ref({ heatmap: [], streak: 0, total_this_month: 0, top_tags: [] })

const cardData = computed(() => [
  { label: '连续打卡天数', value: stats.value.streak, icon: '🔥', numClass: 'streak' },
  { label: '本月日志数', value: stats.value.total_this_month, icon: '📝', numClass: 'monthly' },
  { label: '标签种类', value: stats.value.top_tags.length, icon: '🏷️', numClass: 'tags' }
])

onMounted(async () => {
  try {
    const res = await api.get('/journals/stats/heatmap')
    stats.value = res.data
  } catch {}
})

function getProgressColor(count) {
  if (!stats.value.top_tags.length) return '#6366f1'
  const max = stats.value.top_tags[0].count
  const ratio = count / max
  if (ratio > 0.8) return 'var(--primary-color)'
  if (ratio > 0.5) return '#fbbf24'
  return '#94a3b8'
}
</script>

<style scoped>
.stats-view { padding-bottom: 40px; animation: fadeIn 0.5s ease-out; }
.page-title { color: var(--text-primary); margin: 0 0 24px; font-size: 24px; font-weight: 700; }

.stat-cards { margin-bottom: 32px; }
.stat-card {
  background: var(--sidebar-bg);
  backdrop-filter: var(--sidebar-blur);
  border: 1px solid var(--border-color);
  border-radius: 20px;
  padding: 32px 24px;
  text-align: center;
  transition: all 0.3s ease;
  box-shadow: 0 4px 20px rgba(0,0,0,0.05);
}
.stat-card:hover { transform: translateY(-4px); box-shadow: 0 8px 30px rgba(0,0,0,0.1); border-color: var(--primary-color); }
.stat-num { font-size: 48px; font-weight: 800; line-height: 1; }
.stat-num.streak { color: #f56c6c; text-shadow: 0 0 20px rgba(245, 108, 108, 0.2); }
.stat-num.monthly { color: var(--primary-color); text-shadow: 0 0 20px rgba(99, 102, 241, 0.2); }
.stat-num.tags { color: #10b981; text-shadow: 0 0 20px rgba(16, 185, 129, 0.2); }
.stat-label { color: var(--text-secondary); font-size: 14px; font-weight: 500; margin-top: 12px; }

.section-grid { display: flex; flex-direction: column; gap: 32px; }
.section {
  background: var(--sidebar-bg);
  backdrop-filter: var(--sidebar-blur);
  border: 1px solid var(--border-color);
  border-radius: 20px;
  padding: 24px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.05);
}
.section-header { margin-bottom: 20px; border-left: 4px solid var(--primary-color); padding-left: 12px; }
.section h3 { color: var(--text-primary); font-size: 16px; font-weight: 600; margin: 0; }

.heatmap-container { overflow-x: auto; padding-bottom: 8px; }
.heatmap-wrap { display: flex; flex-wrap: wrap; gap: 4px; min-width: 800px; }
.heatmap-dot {
  width: 12px; height: 12px;
  border-radius: 2px;
  background: var(--input-bg);
  border: 1px solid var(--border-color);
  transition: all 0.2s;
}
.heatmap-dot.active { background: var(--primary-color); box-shadow: 0 0 8px var(--primary-color); border: none; }
.heatmap-dot:hover { transform: scale(1.3); z-index: 10; }

.tag-list { display: flex; flex-direction: column; gap: 16px; }
.tag-row { display: flex; align-items: center; }
.tag-name { color: var(--text-primary); font-size: 14px; font-weight: 500; width: 120px; text-overflow: ellipsis; overflow: hidden; white-space: nowrap; }
.tag-count { color: var(--text-secondary); font-size: 14px; width: 60px; text-align: right; }

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

:deep(.el-progress-bar__outer) { background-color: var(--input-bg) !important; }
</style>
