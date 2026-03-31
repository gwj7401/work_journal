<template>
  <div class="tools-container">
    <h2 class="page-title">实用小工具</h2>
    
    <el-row :gutter="24">
      <el-col :span="12">
        <el-card class="tool-card shadow-sm">
          <template #header>
            <div class="card-header">
              <el-icon class="header-icon"><Files /></el-icon>
              <span>PDF 转 Word (离线完整版)</span>
            </div>
          </template>
          
          <div v-loading="loading" element-loading-text="正在硬核转换中，因页数而异请耐心等待..." element-loading-background="rgba(255, 255, 255, 0.05)">
            <div class="settings-row">
              <div class="setting-item">
                <el-switch v-model="forceOCR" size="small" active-color="var(--primary-color)" />
                <span class="setting-label">强制OCR文字识别 (自动处理扫描件)</span>
              </div>
            </div>
            
            <el-upload
              class="upload-area"
              drag
              action="#"
              :http-request="customUpload"
              :show-file-list="false"
              accept=".pdf"
            >
              <el-icon class="el-icon--upload"><upload-filled /></el-icon>
              <div class="el-upload__text">
                将 PDF 文件拖到此处，或 <em>点击上传并转换</em>
              </div>
              <template #tip>
                <div class="el-upload__tip">
                  <el-icon><InfoFilled /></el-icon> 本功能完全离线运行于后端容器，100% 保护隐私。
                </div>
              </template>
            </el-upload>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { UploadFilled, Files, InfoFilled } from '@element-plus/icons-vue'
import axios from 'axios'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const loading = ref(false)
const forceOCR = ref(true)

const customUpload = async (options) => {
  const file = options.file
  const isPdf = file.name.toLowerCase().endsWith('.pdf')
  if (!isPdf) {
    ElMessage.error('只能上传 PDF 格式的文件！')
    return
  }

  const formData = new FormData()
  formData.append('file', file)
  formData.append('force_ocr', forceOCR.value ? 'true' : 'false')

  loading.value = true
  try {
    const res = await axios.post('/api/tools/pdf-to-word', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
        'Authorization': `Bearer ${auth.token}`
      },
      responseType: 'blob' 
    })
    
    const blob = new Blob([res.data], { 
      type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' 
    })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    
    const baseName = file.name.replace(/\.[^/.]+$/, "")
    link.setAttribute('download', `${baseName}.docx`)
    
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)

    ElMessage.success('🎉 转换完成，已自动触发下载！')
  } catch (error) {
    if (error.response && error.response.data instanceof Blob) {
      const text = await error.response.data.text()
      try {
        const errObj = JSON.parse(text)
        ElMessage.error(`转换失败: ${errObj.detail || '系统内部异常'}`)
      } catch (e) {
        ElMessage.error('转换失败并且服务器未返回明确错误原因。')
      }
    } else {
      ElMessage.error('转换失败，网络或服务器连接异常。')
    }
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.tools-container { animation: fadeIn 0.5s ease-out; }
.page-title { color: var(--text-primary); margin: 0 0 24px; font-size: 24px; font-weight: 700; }

.tool-card {
  background: var(--sidebar-bg);
  backdrop-filter: var(--sidebar-blur);
  border: 1px solid var(--border-color);
  border-radius: 20px;
  overflow: hidden;
  transition: all 0.3s ease;
}
.tool-card:hover { transform: translateY(-4px); box-shadow: 0 12px 32px rgba(0,0,0,0.1); border-color: var(--primary-color); }

.card-header { display: flex; align-items: center; gap: 10px; font-weight: 600; color: var(--text-primary); }
.header-icon { font-size: 20px; color: var(--primary-color); }

.settings-row { margin-bottom: 20px; padding: 12px; background: var(--input-bg); border-radius: 12px; border: 1px solid var(--border-color); }
.setting-item { display: flex; align-items: center; gap: 12px; }
.setting-label { font-size: 14px; color: var(--text-primary); font-weight: 500; }

.upload-area { border-radius: 16px; transition: all 0.2s; }
:deep(.el-upload-dragger) {
  background: var(--input-bg) !important;
  border-color: var(--border-color) !important;
  border-radius: 16px !important;
  height: 200px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
}
:deep(.el-upload-dragger:hover) { border-color: var(--primary-color) !important; }

.el-icon--upload { font-size: 54px; color: var(--primary-color); opacity: 0.8; margin-bottom: 12px; }
.el-upload__text { color: var(--text-secondary); font-size: 14px; }
.el-upload__text em { color: var(--primary-color); font-weight: 600; font-style: normal; }
.el-upload__tip { color: var(--text-secondary); font-size: 13px; display: flex; align-items: center; gap: 6px; justify-content: center; opacity: 0.8; }

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
