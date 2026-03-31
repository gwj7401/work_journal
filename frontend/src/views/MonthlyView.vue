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
        
        <el-upload
          action=""
          :auto-upload="false"
          :show-file-list="false"
          accept=".doc,.docx"
          :on-change="handleWordUpload"
          :disabled="isFinal || generating"
          style="display: inline-block; margin: 0 12px;"
        >
          <el-button type="warning" size="large" plain :disabled="isFinal || generating">
            <el-icon><UploadIcon /></el-icon> 导入Word
          </el-button>
        </el-upload>

        <el-button type="primary" size="large" :loading="generating" :disabled="isFinal" @click="generate">
          <el-icon><MagicStick /></el-icon> AI生成总结
        </el-button>
        
        <el-button v-if="summary" size="large" @click="exportWord">
          <el-icon><Download /></el-icon> 导出Word
        </el-button>
      </div>
    </div>

    <div v-if="generating" class="generating-state" v-loading="true" element-loading-text="AI正在深度思考并润色月度小结，请稍等片刻..." element-loading-background="transparent" style="height: calc(100vh - 260px); width: 100%;">
    </div>

    <div v-else-if="summary" class="summary-area">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; gap: 16px;">
        <el-alert
          type="info"
          :closable="false"
          show-icon
          title="生成后的结果可直接修改。如定稿请锁定，防止误触覆盖。"
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
        style="height: calc(100vh - 280px);"
      />
      <div style="margin-top: 12px; display: flex; gap: 12px;">
        <el-button type="success" :loading="saving" @click="saveEdit">保存修改</el-button>
        <el-button @click="showHistory = true">
          <el-icon><TimerIcon /></el-icon> 版本历史
        </el-button>
      </div>
    </div>

    <el-empty v-else description="请选择月份后通过上方「AI生成」或「导入Word」开始" />

    <!-- 版本历史弹窗 -->
    <el-dialog v-model="showHistory" title="版本存档历史" width="600px" append-to-body>
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
import { ref, onMounted, watch } from 'vue'
import { MdEditor } from 'md-editor-v3'
import 'md-editor-v3/lib/style.css'
import dayjs from 'dayjs'
import api from '@/api'
import { ElMessage, ElMessageBox } from 'element-plus'
import { MagicStick, Download, Upload as UploadIcon, Timer as TimerIcon } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const selectedMonth = ref(dayjs().format('YYYY-MM'))
const summary = ref(null)
const editContent = ref('')
const isFinal = ref(false)
const generating = ref(false)
const saving = ref(false)

const showHistory = ref(false)
const historyList = ref([])
const loadingHistory = ref(false)

watch(selectedMonth, loadSummary)

async function loadSummary() {
  const [y, m] = selectedMonth.value.split('-').map(Number)
  try {
    const res = await api.get(`/summary/${y}/${m}`)
    summary.value = res.data
    editContent.value = res.data.edited_content || res.data.ai_content || ''
    isFinal.value = res.data.is_final || false
  } catch { 
    summary.value = null; 
    editContent.value = '';
    isFinal.value = false 
  }
}

watch(showHistory, (val) => {
  if (val && summary.value) fetchHistory()
})

async function fetchHistory() {
  loadingHistory.value = true
  if (!summary.value) return
  try {
    const res = await api.get(`/history/monthly/${summary.value.id}`)
    historyList.value = res.data
  } catch (err) {
    console.error(err)
  } finally {
    loadingHistory.value = false
  }
}

async function restoreVersion(version) {
  try {
    await ElMessageBox.confirm('确定要还原到此版本吗？当前未保存的内容将被覆盖。', '提示', { type: 'warning' })
    editContent.value = version.content
    showHistory.value = false
    ElMessage.success('已还原至编辑器（记得点击保存以生效）')
  } catch {}
}

async function handleWordUpload(file) {
  const [y, m] = selectedMonth.value.split('-').map(Number)
  const formData = new FormData()
  formData.append('file', file.raw)
  try {
    ElMessage.info('正在解析Word并上传存档...')
    const res = await api.post(`/summary/${y}/${m}/upload`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    summary.value = res.data
    editContent.value = res.data.edited_content || ''
    isFinal.value = res.data.is_final || false
    ElMessage.success('Word导入成功，已自动存档并设为定稿！')
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '导入Word失败')
  }
}

async function generate() {
  const [y, m] = selectedMonth.value.split('-').map(Number)
  generating.value = true
  try {
    ElMessage.info('AI正在生成总结，预计30-60秒...')
    const res = await api.post('/summary/generate', { year: y, month: m })
    summary.value = res.data
    editContent.value = res.data.edited_content || res.data.ai_content || ''
    isFinal.value = res.data.is_final || false
    ElMessage.success('总结生成成功！')
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '总结生成失败')
  } finally {
    generating.value = false
  }
}

async function saveEdit() {
  const [y, m] = selectedMonth.value.split('-').map(Number)
  saving.value = true
  try {
    await api.put(`/summary/${y}/${m}`, { 
      edited_content: editContent.value,
      is_final: isFinal.value
    })
    ElMessage.success('已保存 ✓')
    if (isFinal.value && showHistory.value) fetchHistory()
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
.monthly-view { height: 100%; animation: fadeIn 0.5s ease-out; }
.page-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 24px; }
.page-header h2 { color: var(--text-primary); margin: 0 0 4px; font-size: 24px; font-weight: 700; letter-spacing: 0.5px; }
.page-sub { color: var(--text-secondary); margin: 0; font-size: 14px; opacity: 0.8; }
.header-actions { display: flex; align-items: center; gap: 12px; }
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
