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
          <el-radio-button label="quarterly" value="quarterly">季度</el-radio-button>
          <el-radio-button label="annual" value="annual">年度</el-radio-button>
        </el-radio-group>

        <!-- 年份 -->
        <el-select v-model="selectedYear" size="large" style="width:100px;">
          <el-option v-for="y in years" :key="y" :label="y+'年'" :value="y" />
        </el-select>

        <!-- 季度（仅季度模式） -->
        <el-select v-if="!isAnnual" v-model="selectedQuarter" size="large" style="width:110px;">
          <el-option v-for="q in [1,2,3,4]" :key="q" :label="`第${q}季度`" :value="q" />
        </el-select>

        <el-button type="primary" size="large" :loading="generating" :disabled="isFinal" @click="generate">
          <el-icon><MagicStick /></el-icon> AI生成
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

    <div v-if="generating" class="generating-state" v-loading="true" element-loading-text="AI正在深度聚合历史工作并生成完整汇总，这比平时更长一些，请耐心等待..." element-loading-background="transparent" style="height: calc(100vh - 260px); width: 100%;">
    </div>

    <div v-else-if="summary" class="summary-area">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; gap: 16px;">
        <el-alert
          type="info"
          :closable="false"
          show-icon
          title="定稿请锁定，防止重新生成覆盖。支持多版本快照存档。"
          style="flex: 1;"
        />
        <el-switch
          v-model="isFinal"
          active-text="🔒 终稿锁定"
          inactive-text="未锁定"
          @change="saveEdit"
        />
      </div>
      <MdEditor
        v-model="editContent"
        :theme="auth.editorTheme"
        preview-theme="github"
        language="zh-CN"
        :style="`height: calc(100vh - ${isAnnual ? 300 : 310}px);`"
      />
      <div style="margin-top: 12px; display: flex; gap: 12px;">
        <el-button type="success" :loading="saving" @click="saveEdit">保存修改</el-button>
        <el-button @click="showHistory = true">
          <el-icon><TimerIcon /></el-icon> 版本历史
        </el-button>
      </div>
    </div>

    <el-empty v-else :description="emptyText" />

    <!-- 版本历史弹窗 -->
    <el-dialog v-model="showHistory" title="版本快照历史" width="600px" append-to-body>
      <el-table :data="historyList" v-loading="loadingHistory" max-height="400px">
        <el-table-column property="created_at" label="时间" width="160">
          <template #default="scope">{{ dayjs(scope.row.created_at).format('YYYY-MM-DD HH:mm') }}</template>
        </el-table-column>
        <el-table-column property="version_note" label="备注" />
        <el-table-column label="操作" width="100">
          <template #default="scope">
            <el-button link type="primary" @click="restoreVersion(scope.row)">还原</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { MdEditor } from 'md-editor-v3'
import 'md-editor-v3/lib/style.css'
import dayjs from 'dayjs'
import api from '@/api'
import { ElMessage, ElMessageBox } from 'element-plus'
import { MagicStick, Download, Timer as TimerIcon } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const mode = ref('quarterly')
const isAnnual = computed(() => mode.value === 'annual')

const now = dayjs()
const currentYear = now.year()
const years = Array.from({ length: 5 }, (_, i) => currentYear - i)

const selectedYear = ref(currentYear)
const selectedQuarter = ref(Math.ceil((now.month() + 1) / 3))
const summary = ref(null)
const editContent = ref('')
const isFinal = ref(false)
const generating = ref(false)
const saving = ref(false)

const showHistory = ref(false)
const historyList = ref([])
const loadingHistory = ref(false)

const emptyText = computed(() =>
  isAnnual.value
    ? `点击「AI生成」即可生成${selectedYear.value}年度工作总结`
    : `点击「AI生成」即可生成${selectedYear.value}年第${selectedQuarter.value}季度工作总结`
)

watch([mode, selectedYear, selectedQuarter], loadExisting)

async function loadExisting() {
  summary.value = null
  editContent.value = ''
  isFinal.value = false
  try {
    const url = isAnnual.value
      ? `/aggregate/annual/${selectedYear.value}`
      : `/aggregate/quarterly/${selectedYear.value}/${selectedQuarter.value}`
    const res = await api.get(url)
    summary.value = res.data
    editContent.value = res.data.edited_content || res.data.ai_content || ''
    isFinal.value = res.data.is_final || false
  } catch {}
}

watch(showHistory, (val) => {
  if (val && summary.value) fetchHistory()
})

async function fetchHistory() {
  loadingHistory.value = true
  try {
    const res = await api.get(`/history/${isAnnual.value ? 'annual' : 'quarterly'}/${summary.value.id}`)
    historyList.value = res.data
  } catch (err) {
    console.error(err)
  } finally {
    loadingHistory.value = false
  }
}

async function restoreVersion(version) {
  try {
    await ElMessageBox.confirm('确定要从该历史快照恢复吗？', '提示', { type: 'warning' })
    editContent.value = version.content
    showHistory.value = false
    ElMessage.success('已恢复至编辑器')
  } catch {}
}

async function generate() {
  generating.value = true
  summary.value = null
  try {
    const label = isAnnual.value ? `${selectedYear.value}年度` : `${selectedYear.value}年第${selectedQuarter.value}季度`
    ElMessage.info(`AI正在分析并生成${label}总结...`)
    const url = isAnnual.value ? '/aggregate/annual/generate' : '/aggregate/quarterly/generate'
    const body = isAnnual.value
      ? { year: selectedYear.value }
      : { year: selectedYear.value, quarter: selectedQuarter.value }
    const res = await api.post(url, body)
    summary.value = res.data
    editContent.value = res.data.edited_content || res.data.ai_content || ''
    isFinal.value = res.data.is_final || false
    ElMessage.success('生成成功！')
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '生成失败')
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
    await api.put(url, { 
      edited_content: editContent.value,
      is_final: isFinal.value 
    })
    ElMessage.success('保存成功')
    if (isFinal.value && showHistory.value) fetchHistory()
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

onMounted(loadExisting)
</script>

<style scoped>
.aggregate-view { height: 100%; animation: fadeIn 0.5s ease-out; }
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
  flex-wrap: wrap;
  gap: 12px;
}
.page-header h2 { color: var(--text-primary); margin: 0 0 4px; font-size: 24px; font-weight: 700; }
.page-sub { color: var(--text-secondary); margin: 0; font-size: 14px; opacity: 0.8; }
.header-actions { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }
.summary-area { display: flex; flex-direction: column; gap: 16px; }

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

:deep(.el-alert) {
  background-color: rgba(99, 102, 241, 0.1);
  border: 1px solid rgba(99, 102, 241, 0.2);
  color: var(--text-primary);
}
</style>
