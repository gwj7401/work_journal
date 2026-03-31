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
        :theme="auth.editorTheme"
        preview-theme="github"
        language="zh-CN"
        @on-upload-img="onUploadImg"
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
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const today = dayjs().format('YYYY年MM月DD日 dddd')
const content = ref('')
const tags = ref([])
const tagInput = ref('')
const saving = ref(false)
const entryId = ref(null)

const toolbars = [
  'bold', 'underline', 'italic', 'strikethrough', 'quote', '-',
  'title', 'unorderedList', 'orderedList', 'task', '-',
  'link', 'image', 'table', 'codeRow', 'code', '-',
  'revoke', 'next', 'save', 'pageFullscreen', 'preview', 'htmlPreview'
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

const onUploadImg = async (files, callback) => {
  const uploadTasks = files.map(file => {
    return new Promise((resolve, reject) => {
      const form = new FormData()
      form.append('file', file)
      api.post('/upload/image', form, {
        headers: { 'Content-Type': 'multipart/form-data' }
      }).then(res => {
        resolve(res.data.url)
      }).catch(err => {
        ElMessage.error(`图片 ${file.name} 上传失败`)
        reject(err)
      })
    })
  })

  Promise.all(uploadTasks).then((urls) => {
    callback(urls)
  })
}
</script>

<style scoped>
.today-view { height: 100%; animation: fadeIn 0.5s ease-out; }
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
}
.page-header h2 { color: var(--text-primary); margin: 0 0 4px; font-size: 24px; font-weight: 700; }
.page-date { color: var(--text-secondary); margin: 0; font-size: 14px; opacity: 0.8; }
.header-actions { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; justify-content: flex-end; }
.tag-item { cursor: default; }
.editor-wrap { border-radius: 12px; overflow: hidden; box-shadow: 0 4px 24px rgba(0,0,0,0.1); border: 1px solid var(--border-color); }

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
