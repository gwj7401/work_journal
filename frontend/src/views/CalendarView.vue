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

    <div v-if="selectedEntry" class="entry-preview">
      <div class="preview-header">
        <h3>{{ currentYear }}年{{ currentMonth }}月{{ selectedDay }}日</h3>
        <el-tag v-for="t in selectedEntry.tags" :key="t" size="small" effect="dark" class="preview-tag">
          #{{ t }}
        </el-tag>
      </div>
      <div class="preview-content">{{ selectedEntry.content }}</div>
    </div>
    <el-empty v-else-if="selectedDay" description="当天无日志记录" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import dayjs from 'dayjs'
import api from '@/api'
import { ArrowLeft, ArrowRight } from '@element-plus/icons-vue'

const weekdays = ['日','一','二','三','四','五','六']
const today = dayjs()
const currentYear = ref(today.year())
const currentMonth = ref(today.month() + 1)
const entries = ref({})
const selectedDay = ref(null)
const selectedEntry = ref(null)

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
.calendar-view { padding-bottom: 24px; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; }
.page-header h2 { color: #fff; margin: 0; font-size: 20px; }
.month-nav { display: flex; align-items: center; gap: 12px; }
.month-label { color: #fff; font-size: 16px; min-width: 100px; text-align: center; }
.calendar-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 6px;
  margin-bottom: 24px;
}
.weekday-header { text-align: center; color: rgba(255,255,255,0.3); font-size: 12px; padding: 8px 0; }
.day-cell {
  min-height: 60px;
  border-radius: 10px;
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.06);
  padding: 8px;
  cursor: pointer;
  position: relative;
  transition: all 0.15s;
}
.day-cell.empty { background: transparent; border-color: transparent; cursor: default; }
.day-cell:not(.empty):hover { background: rgba(255,255,255,0.08); border-color: rgba(255,255,255,0.1); }
.day-cell.today { border-color: #409eff; }
.day-cell.has-entry { background: rgba(64,158,255,0.08); }
.day-cell.selected { background: rgba(64,158,255,0.2); border-color: #409eff; }
.day-num { color: rgba(255,255,255,0.6); font-size: 13px; }
.day-cell.today .day-num { color: #409eff; font-weight: 700; }
.dot { width: 6px; height: 6px; border-radius: 50%; background: #409eff; margin-top: 6px; }
.entry-preview {
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 12px;
  padding: 20px;
}
.preview-header { display: flex; align-items: center; gap: 8px; margin-bottom: 12px; flex-wrap: wrap; }
.preview-header h3 { color: #fff; margin: 0; font-size: 15px; }
.preview-tag { cursor: default; }
.preview-content { color: rgba(255,255,255,0.6); font-size: 14px; line-height: 1.8; white-space: pre-wrap; }
</style>
