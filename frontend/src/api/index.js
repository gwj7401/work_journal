import axios from 'axios'
import { ElMessage } from 'element-plus'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE || '/api',
  timeout: 120000  // AI生成可能需要较长时间
})

// 请求拦截：自动附加Token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('wj_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 响应拦截：统一错误处理
api.interceptors.response.use(
  (res) => res,
  (err) => {
    const msg = err.response?.data?.detail || err.message || '请求失败'
    if (err.response?.status === 401) {
      localStorage.removeItem('wj_token')
      localStorage.removeItem('wj_user')
      window.location.href = '/login'
    } else {
      ElMessage.error(msg)
    }
    return Promise.reject(err)
  }
)

export default api
