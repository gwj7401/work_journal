<template>
  <div class="monthly-view">
    <div class="page-header">
      <div>
        <h2>月度总结</h2>
        <p class="page-sub">AI自动生成 · 公文格式</p>
      </div>
      <div class="header-actions">
        <el-date-picker
          v-model="selectedMonth"
          type="month"
          placeholder="选择月份"
          format="YYYY年MM月"
          value-format="YYYY-MM"
          :clearable="false"
          size="large"
        />
        <el-button type="primary" size="large" :loading="generating" @click="generate">
          <el-icon><Magic /></el-icon> AI生成总结
        </el-button>
        <el-button v-if="summary" size="large" @click="exportWord">
          <el-icon><Download /></el-icon> 导出Word
        </el-button>
      </div>
    </div>

    <el-skeleton v-if="generating" :rows="15" animated />

    <div v-else-if="summary" class="summary-area">
      <el-alert
        type="info"
        :closable="false"
        show-icon
        title="AI生成的公文格式总结，可在下方直接编辑"
        style="margin-bottom:16px;"
      />
      <MdEditor
        v-model="editContent"
        theme="dark"
        preview-theme="github"
        language="zh-CN"
        style="height: calc(100vh - 280px);"
      />
      <el-button
        type="success"
        style="margin-top:12px;"
        :loading="saving"
        @click="saveEdit"
      >保存修改</el-button>
    </div>

    <el-empty v-else description="请选择月份后点击「AI生成总结」" />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { MdEditor } from 'md-editor-v3'
import 'md-editor-v3/lib/style.css'
import dayjs from 'dayjs'
import api from '@/api'
import { ElMessage } from 'element-plus'
import { Magic, Download } from '@element-plus/icons-vue'

const selectedMonth = ref(dayjs().format('YYYY-MM'))
const summary = ref(null)
const editContent = ref('')
const generating = ref(false)
const saving = ref(false)

const [year, month] = () => selectedMonth.value.split('-').map(Number)

async function loadSummary() {
  const [y, m] = selectedMonth.value.split('-').map(Number)
  try {
    const res = await api.get(`/summary/${y}/${m}`)
    summary.value = res.data
    editContent.value = res.data.edited_content || res.data.ai_content || ''
  } catch { summary.value = null }
}

async function generate() {
  const [y, m] = selectedMonth.value.split('-').map(Number)
  generating.value = true
  try {
    ElMessage.info('AI正在生成总结，预计30-60秒...')
    const res = await api.post('/summary/generate', { year: y, month: m })
    summary.value = res.data
    editContent.value = res.data.edited_content || res.data.ai_content || ''
    ElMessage.success('总结生成成功！')
  } finally {
    generating.value = false
  }
}

async function saveEdit() {
  const [y, m] = selectedMonth.value.split('-').map(Number)
  saving.value = true
  try {
    await api.put(`/summary/${y}/${m}`, { edited_content: editContent.value })
    ElMessage.success('已保存 ✓')
  } finally {
    saving.value = false
  }
}

function exportWord() {
  const [y, m] = selectedMonth.value.split('-').map(Number)
  const token = localStorage.getItem('wj_token')
  const base = import.meta.env.VITE_API_BASE || '/api'
  window.open(`${base}/summary/${y}/${m}/export?token=${token}`)
}

onMounted(loadSummary)
</script>

<style scoped>
.monthly-view { height: 100%; }
.page-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 20px; }
.page-header h2 { color: #fff; margin: 0 0 4px; font-size: 20px; }
.page-sub { color: rgba(255,255,255,0.4); margin: 0; font-size: 13px; }
.header-actions { display: flex; align-items: center; gap: 10px; }
.summary-area { display: flex; flex-direction: column; }
</style>
