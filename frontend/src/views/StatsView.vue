<template>
  <div class="stats-view">
    <h2 class="page-title">统计看板</h2>

    <el-row :gutter="20" class="stat-cards">
      <el-col :span="8">
        <div class="stat-card">
          <div class="stat-num streak">{{ stats.streak }}</div>
          <div class="stat-label">🔥 连续打卡天数</div>
        </div>
      </el-col>
      <el-col :span="8">
        <div class="stat-card">
          <div class="stat-num">{{ stats.total_this_month }}</div>
          <div class="stat-label">📝 本月日志数</div>
        </div>
      </el-col>
      <el-col :span="8">
        <div class="stat-card">
          <div class="stat-num">{{ stats.top_tags.length }}</div>
          <div class="stat-label">🏷️ 标签种类</div>
        </div>
      </el-col>
    </el-row>

    <div class="section">
      <h3>过去365天</h3>
      <div class="heatmap-wrap">
        <div v-for="(item, i) in stats.heatmap" :key="i"
          class="heatmap-dot"
          :class="{ active: item.count > 0 }"
          :title="item.date"
        />
      </div>
    </div>

    <div class="section" v-if="stats.top_tags.length">
      <h3>常用标签 Top 10</h3>
      <div class="tag-list">
        <div v-for="t in stats.top_tags" :key="t.tag" class="tag-row">
          <span class="tag-name">#{{ t.tag }}</span>
          <el-progress :percentage="Math.round(t.count / stats.top_tags[0].count * 100)"
            :stroke-width="8" :show-text="false" style="flex:1; margin: 0 12px;" />
          <span class="tag-count">{{ t.count }}次</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '@/api'

const stats = ref({ heatmap: [], streak: 0, total_this_month: 0, top_tags: [] })

onMounted(async () => {
  try {
    const res = await api.get('/journals/stats/heatmap')
    stats.value = res.data
  } catch {}
})
</script>

<style scoped>
.stats-view { padding-bottom: 40px; }
.page-title { color: #fff; margin: 0 0 24px; font-size: 20px; }
.stat-cards { margin-bottom: 32px; }
.stat-card {
  background: rgba(255,255,255,0.05);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 16px;
  padding: 24px;
  text-align: center;
}
.stat-num { font-size: 42px; font-weight: 700; color: #409eff; }
.stat-num.streak { color: #f56c6c; }
.stat-label { color: rgba(255,255,255,0.5); font-size: 13px; margin-top: 6px; }
.section { margin-bottom: 32px; }
.section h3 { color: rgba(255,255,255,0.7); font-size: 14px; margin: 0 0 16px; }
.heatmap-wrap { display: flex; flex-wrap: wrap; gap: 3px; }
.heatmap-dot {
  width: 10px; height: 10px;
  border-radius: 2px;
  background: rgba(255,255,255,0.06);
}
.heatmap-dot.active { background: #409eff; }
.tag-list { display: flex; flex-direction: column; gap: 10px; }
.tag-row { display: flex; align-items: center; }
.tag-name { color: rgba(255,255,255,0.6); font-size: 13px; width: 100px; }
.tag-count { color: rgba(255,255,255,0.4); font-size: 13px; width: 40px; text-align: right; }
</style>
