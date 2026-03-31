<template>
  <div class="calendar-view">
    <div class="page-header">
      <h2>日历视图</h2>
      <div class="month-nav">
        <el-button circle @click="changeMonth(-1)"><el-icon><ArrowLeft /></el-icon></el-button>
        <span class="month-label">{{ currentYear }}年{{ currentMonth }}月</span>
        <el-button circle @click="changeMonth(1)"><el-icon><ArrowRight /></el-icon></el-button>
      </div>
    </div>

    <div class="calendar-grid">
      <div class="weekday-header" v-for="d in weekdays" :key="d">{{ d }}</div>
      <div v-for="i in startOffset" :key="'empty-'+i" class="day-cell empty" />
      <div
        v-for="day in daysInMonth"
        :key="day"
        class="day-cell"
        :class="{
          today: isToday(day),
          'has-entry': hasEntry(day),
          selected: selectedDay === day
        }"
        @click="selectDay(day)"
      >
        <span class="day-num">{{ day }}</span>
        <div v-if="hasEntry(day)" class="dot" />
      </div>
    </div>

    <div v-if="selectedDay" class="entry-preview">
      <div v-if="!editMode">
        <div v-if="selectedEntry" class="fade-in">
          <div class="preview-header">
            <h3>{{ currentYear }}年{{ currentMonth }}月{{ selectedDay }}日</h3>
            <div class="tags-wrap">
              <el-tag v-for="t in selectedEntry.tags" :key="t" size="small" effect="dark" class="preview-tag">
                #{{ t }}
              </el-tag>
            </div>
            <el-button size="small" type="primary" plain @click="enterEditMode" style="margin-left:auto">
              <el-icon><EditPen /></el-icon> 编辑日志
            </el-button>
          </div>
          <div class="preview-content">
            <MdPreview :modelValue="selectedEntry.content" :theme="auth.editorTheme" preview-theme="github" />
          </div>
        </div>
        <el-empty v-else description="这天没有记录工作日志哦">
          <el-button type="primary" @click="enterEditMode">
            <el-icon><EditPen /></el-icon> 补写日志
          </el-button>
        </el-empty>
      </div>
      <div v-else class="fade-in">
        <!-- 编辑模式 -->
        <div class="preview-header">
          <h3>编辑日志: {{ currentYear }}年{{ currentMonth }}月{{ selectedDay }}日</h3>
          <el-input
            v-model="tagInput"
            placeholder="添加标签回车确认"
            size="small"
            style="width:160px; margin-left:12px;"
            @keydown.enter="addTag"
          />
          <el-tag
            v-for="tag in editTags"
            :key="tag"
            closable
            @close="removeTag(tag)"
            class="tag-item"
            style="margin-left: 4px;"
            effect="dark"
          >{{ tag }}</el-tag>
          <div style="margin-left: auto; display: flex; gap: 8px;">
            <el-button size="small" @click="editMode = false">取消</el-button>
            <el-button size="small" type="primary" :loading="saving" @click="saveEntry">保存</el-button>
          </div>
        </div>
        <MdEditor
          v-model="editContent"
          :toolbars="toolbars"
          :theme="auth.editorTheme"
          preview-theme="github"
          language="zh-CN"
          @on-upload-img="onUploadImg"
          style="height: 400px; margin-top: 12px;"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import dayjs from 'dayjs'
import api from '@/api'
import { ArrowLeft, ArrowRight, EditPen } from '@element-plus/icons-vue'
import { MdPreview, MdEditor } from 'md-editor-v3'
import 'md-editor-v3/lib/preview.css'
import 'md-editor-v3/lib/style.css'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const weekdays = ['日','一','二','三','四','五','六']
const today = dayjs()
const currentYear = ref(today.year())
const currentMonth = ref(today.month() + 1)
const entries = ref({})
const selectedDay = ref(null)
const selectedEntry = ref(null)

const editMode = ref(false)
const editContent = ref('')
const editTags = ref([])
const tagInput = ref('')
const saving = ref(false)

const toolbars = [
  'bold', 'underline', 'italic', 'strikethrough', 'quote', '-',
  'title', 'unorderedList', 'orderedList', 'task', '-',
  'link', 'image', 'table', 'codeRow', 'code', '-',
  'revoke', 'next', 'save', 'pageFullscreen', 'preview', 'htmlPreview'
]

const daysInMonth = computed(() => dayjs(`${currentYear.value}-${currentMonth.value}`).daysInMonth())
const startOffset = computed(() => dayjs(`${currentYear.value}-${currentMonth.value}-01`).day())

function isToday(day) {
  return today.year() === currentYear.value && today.month() + 1 === currentMonth.value && today.date() === day
}
function hasEntry(day) {
  return !!entries.value[day]
}

function selectDay(day) {
  selectedDay.value = day
  selectedEntry.value = entries.value[day] || null
  editMode.value = false
  editContent.value = ''
  editTags.value = []
}

function enterEditMode() {
  editMode.value = true
  if (selectedEntry.value) {
    editContent.value = selectedEntry.value.content || ''
    editTags.value = [...(selectedEntry.value.tags || [])]
  } else {
    editContent.value = ''
    editTags.value = []
  }
}

function addTag() {
  const t = tagInput.value.trim().replace(/^#/, '')
  if (t && !editTags.value.includes(t)) {
    editTags.value.push(t)
  }
  tagInput.value = ''
}

function removeTag(tag) {
  editTags.value = editTags.value.filter(t => t !== tag)
}

async function saveEntry() {
  if (!editContent.value.trim()) return ElMessage.warning('请输入日志内容')
  saving.value = true
  const dateStr = `${currentYear.value}-${String(currentMonth.value).padStart(2, '0')}-${String(selectedDay.value).padStart(2, '0')}`
  try {
    const res = await api.post('/journals', {
      entry_date: dateStr,
      content: editContent.value,
      tags: editTags.value
    })
    entries.value[selectedDay.value] = res.data
    selectedEntry.value = res.data
    editMode.value = false
    ElMessage.success('已保存 ✓')
  } catch (err) {
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

const onUploadImg = async (files, callback) => {
  const uploadTasks = files.map(file => {
    return new Promise((resolve, reject) => {
      const form = new FormData()
      form.append('file', file)
      api.post('/upload/image', form, {
        headers: { 'Content-Type': 'multipart/form-data' }
      }).then(res => resolve(res.data.url))
      .catch(err => {
        ElMessage.error(`图片 ${file.name} 上传失败`)
        reject(err)
      })
    })
  })
  Promise.all(uploadTasks).then(urls => callback(urls))
}

function changeMonth(delta) {
  let m = currentMonth.value + delta
  let y = currentYear.value
  if (m > 12) { m = 1; y++ }
  if (m < 1) { m = 12; y-- }
  currentMonth.value = m
  currentYear.value = y
  selectedDay.value = null
  loadMonthEntries()
}

async function loadMonthEntries() {
  entries.value = {}
  try {
    const res = await api.get(`/journals/month/${currentYear.value}/${currentMonth.value}`)
    res.data.forEach(e => {
      const d = dayjs(e.entry_date).date()
      entries.value[d] = e
    })
  } catch {}
}

onMounted(loadMonthEntries)
</script>

<style scoped>
.calendar-view { height: 100%; animation: fadeIn 0.5s ease-out; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; }
.page-header h2 { color: var(--text-primary); margin: 0; font-size: 24px; font-weight: 700; }
.month-nav { display: flex; align-items: center; gap: 12px; }
.month-label { color: var(--text-primary); font-size: 18px; font-weight: 600; min-width: 110px; text-align: center; }

.calendar-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 8px;
  margin-bottom: 32px;
}
.weekday-header { text-align: center; color: var(--text-secondary); font-size: 13px; font-weight: 600; padding-bottom: 12px; opacity: 0.6; }
.day-cell {
  min-height: 72px;
  border-radius: 12px;
  background: var(--input-bg);
  border: 1px solid var(--border-color);
  padding: 10px;
  cursor: pointer;
  position: relative;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}
.day-cell.empty { background: transparent; border-color: transparent; cursor: default; }
.day-cell:not(.empty):hover { 
  background: var(--input-focus-bg); 
  border-color: var(--primary-color);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}
.day-cell.today { border-color: var(--primary-color); border-width: 2px; }
.day-cell.has-entry { background: rgba(99, 102, 241, 0.08); }
.day-cell.selected { background: rgba(99, 102, 241, 0.15); border-color: var(--primary-color); }
.day-num { color: var(--text-primary); font-size: 14px; font-weight: 500; opacity: 0.6; }
.day-cell.today .day-num { color: var(--primary-color); font-weight: 700; opacity: 1; }
.dot { width: 6px; height: 6px; border-radius: 50%; background: var(--primary-color); margin-top: 8px; box-shadow: 0 0 8px var(--primary-color); }

.entry-preview {
  background: var(--sidebar-bg);
  backdrop-filter: var(--sidebar-blur);
  border: 1px solid var(--border-color);
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 8px 32px rgba(0,0,0,0.1);
  min-height: 200px;
}
.preview-header { display: flex; align-items: center; gap: 12px; margin-bottom: 20px; flex-wrap: wrap; }
.preview-header h3 { color: var(--text-primary); margin: 0; font-size: 18px; font-weight: 600; }
.tags-wrap { display: flex; gap: 8px; flex-wrap: wrap; }
.preview-content { margin-top: 16px; border-radius: 8px; overflow: hidden; border: 1px solid var(--border-color); }

.fade-in { animation: fadeIn 0.4s ease-out; }

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

:deep(.md-editor), :deep(.md-preview) {
  background-color: transparent !important;
}
</style>
