<template>
  <div class="aggregate-view">
    <div class="page-header">
      <div>
        <h2>{{ isAnnual ? '年度总结' : '季度总结' }}</h2>
        <p class="page-sub">AI自动生成 · 公文格式 · 智能聚合月度总结</p>
      </div>
      <div class="header-actions">
        <!-- 模式切换 -->
        <el-radio-group v-model="mode" size="large">
          <el-radio-button value="quarterly">季度</el-radio-button>
          <el-radio-button value="annual">年度</el-radio-button>
        </el-radio-group>

        <!-- 年份 -->
        <el-select v-model="selectedYear" size="large" style="width:100px;">
          <el-option v-for="y in years" :key="y" :label="y+'年'" :value="y" />
        </el-select>

        <!-- 季度（仅季度模式） -->
        <el-select v-if="!isAnnual" v-model="selectedQuarter" size="large" style="width:110px;">
          <el-option v-for="q in [1,2,3,4]" :key="q" :label="`第${q}季度`" :value="q" />
        </el-select>

        <el-button type="primary" size="large" :loading="generating" @click="generate">
          <el-icon><Magic /></el-icon> AI生成
        </el-button>
        <el-button v-if="summary" size="large" @click="exportWord">
          <el-icon><Download /></el-icon> 导出Word
        </el-button>
      </div>
    </div>

    <!-- 数据来源提示 -->
    <el-alert v-if="!generating && !summary" type="info" :closable="false" show-icon style="margin-bottom:16px;">
      <template #title>
        <span v-if="!isAnnual">
          AI将优先聚合该季度已有的<b>月度总结</b>，如无月度总结则直接读取原始日志
        </span>
        <span v-else>
          AI将按优先级聚合：<b>季度总结 → 月度总结 → 原始日志</b>，内容越丰富总结质量越高
        </span>
      </template>
    </el-alert>

    <el-skeleton v-if="generating" :rows="18" animated />

    <div v-else-if="summary" class="summary-area">
      <MdEditor
        v-model="editContent"
        theme="dark"
        preview-theme="github"
        language="zh-CN"
        :style="`height: calc(100vh - ${isAnnual ? 260 : 270}px);`"
      />
      <div style="margin-top:12px; display:flex; gap:10px;">
        <el-button type="success" :loading="saving" @click="saveEdit">保存修改</el-button>
        <el-button @click="generate">重新生成</el-button>
      </div>
    </div>

    <el-empty v-else :description="emptyText" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { MdEditor } from 'md-editor-v3'
import 'md-editor-v3/lib/style.css'
import dayjs from 'dayjs'
import api from '@/api'
import { ElMessage } from 'element-plus'
import { Magic, Download } from '@element-plus/icons-vue'

const mode = ref('quarterly')
const isAnnual = computed(() => mode.value === 'annual')

const now = dayjs()
const currentYear = now.year()
const years = Array.from({ length: 5 }, (_, i) => currentYear - i)

const selectedYear = ref(currentYear)
const selectedQuarter = ref(Math.ceil((now.month() + 1) / 3))
const summary = ref(null)
const editContent = ref('')
const generating = ref(false)
const saving = ref(false)

const emptyText = computed(() =>
  isAnnual.value
    ? `点击「AI生成」即可生成${selectedYear.value}年度工作总结`
    : `点击「AI生成」即可生成${selectedYear.value}年第${selectedQuarter.value}季度工作总结`
)

async function loadExisting() {
  summary.value = null
  try {
    const url = isAnnual.value
      ? `/aggregate/annual/${selectedYear.value}`
      : `/aggregate/quarterly/${selectedYear.value}/${selectedQuarter.value}`
    const res = await api.get(url)
    summary.value = res.data
    editContent.value = res.data.edited_content || res.data.ai_content || ''
  } catch {}
}

async function generate() {
  generating.value = true
  summary.value = null
  try {
    const label = isAnnual.value ? `${selectedYear.value}年度` : `${selectedYear.value}年第${selectedQuarter.value}季度`
    ElMessage.info(`AI正在生成${label}总结，预计60-90秒，请耐心等待...`)
    const url = isAnnual.value ? '/aggregate/annual/generate' : '/aggregate/quarterly/generate'
    const body = isAnnual.value
      ? { year: selectedYear.value }
      : { year: selectedYear.value, quarter: selectedQuarter.value }
    const res = await api.post(url, body)
    summary.value = res.data
    editContent.value = res.data.edited_content || res.data.ai_content || ''
    ElMessage.success('总结生成成功！')
  } finally {
    generating.value = false
  }
}

async function saveEdit() {
  saving.value = true
  try {
    const url = isAnnual.value
      ? `/aggregate/annual/${selectedYear.value}`
      : `/aggregate/quarterly/${selectedYear.value}/${selectedQuarter.value}`
    await api.put(url, { edited_content: editContent.value })
    ElMessage.success('已保存 ✓')
  } finally {
    saving.value = false
  }
}

function exportWord() {
  const token = localStorage.getItem('wj_token')
  const base = import.meta.env.VITE_API_BASE || '/api'
  const url = isAnnual.value
    ? `${base}/aggregate/annual/${selectedYear.value}/export`
    : `${base}/aggregate/quarterly/${selectedYear.value}/${selectedQuarter.value}/export`
  window.open(`${url}?token=${token}`)
}

watch([mode, selectedYear, selectedQuarter], loadExisting)
onMounted(loadExisting)
</script>

<style scoped>
.aggregate-view { height: 100%; }
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
  flex-wrap: wrap;
  gap: 12px;
}
.page-header h2 { color: #fff; margin: 0 0 4px; font-size: 20px; }
.page-sub { color: rgba(255,255,255,0.4); margin: 0; font-size: 13px; }
.header-actions { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.summary-area { display: flex; flex-direction: column; }
</style>
