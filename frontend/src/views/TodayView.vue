<template>
  <div class="today-view">
    <div class="page-header">
      <div>
        <h2>今日日志</h2>
        <p class="page-date">{{ today }}</p>
      </div>
      <div class="header-actions">
        <el-input
          v-model="tagInput"
          placeholder="添加标签，回车确认"
          size="small"
          style="width:180px;"
          @keydown.enter="addTag"
        />
        <el-tag
          v-for="tag in tags"
          :key="tag"
          closable
          @close="removeTag(tag)"
          class="tag-item"
          effect="dark"
        >{{ tag }}</el-tag>
        <el-button type="primary" :loading="saving" @click="save">
          保 存
        </el-button>
      </div>
    </div>

    <div class="editor-wrap">
      <MdEditor
        v-model="content"
        :toolbars="toolbars"
        theme="dark"
        preview-theme="github"
        language="zh-CN"
        style="height: calc(100vh - 200px);"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { MdEditor } from 'md-editor-v3'
import 'md-editor-v3/lib/style.css'
import dayjs from 'dayjs'
import api from '@/api'
import { ElMessage } from 'element-plus'

const today = dayjs().format('YYYY年MM月DD日 dddd')
const content = ref('')
const tags = ref([])
const tagInput = ref('')
const saving = ref(false)
const entryId = ref(null)

const toolbars = [
  'bold', 'italic', 'strikethrough', '-',
  'unorderedList', 'orderedList', 'task', '-',
  'code', 'table', '-',
  'revoke', 'next', 'save'
]

onMounted(async () => {
  try {
    const res = await api.get('/journals/today')
    if (res.data) {
      content.value = res.data.content
      tags.value = res.data.tags || []
      entryId.value = res.data.id
    }
  } catch {}
})

function addTag() {
  const t = tagInput.value.trim().replace(/^#/, '')
  if (t && !tags.value.includes(t)) {
    tags.value.push(t)
  }
  tagInput.value = ''
}

function removeTag(tag) {
  tags.value = tags.value.filter(t => t !== tag)
}

async function save() {
  if (!content.value.trim()) return ElMessage.warning('请输入日志内容')
  saving.value = true
  try {
    const res = await api.post('/journals', {
      entry_date: dayjs().format('YYYY-MM-DD'),
      content: content.value,
      tags: tags.value
    })
    entryId.value = res.data.id
    ElMessage.success('已保存 ✓')
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.today-view { height: 100%; }
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
}
.page-header h2 { color: #fff; margin: 0 0 4px; font-size: 20px; }
.page-date { color: rgba(255,255,255,0.4); margin: 0; font-size: 13px; }
.header-actions { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; justify-content: flex-end; }
.tag-item { cursor: default; }
.editor-wrap { border-radius: 12px; overflow: hidden; }
</style>
