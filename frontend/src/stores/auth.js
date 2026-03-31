import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/api'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('wj_token') || '')
  const user = ref(JSON.parse(localStorage.getItem('wj_user') || 'null'))

  const isLoggedIn = computed(() => !!token.value)

  function setAuth(data) {
    token.value = data.access_token
    user.value = data.user
    localStorage.setItem('wj_token', data.access_token)
    localStorage.setItem('wj_user', JSON.stringify(data.user))
  }

  function logout() {
    token.value = ''
    user.value = null
    localStorage.removeItem('wj_token')
    localStorage.removeItem('wj_user')
  }

  async function login(username, password) {
    const res = await api.post('/auth/login', { username, password })
    setAuth(res.data)
    return res.data
  }

  async function register(data) {
    const res = await api.post('/auth/register', data)
    return res.data
  }

  const theme = computed(() => user.value?.theme || 'indigo')
  const editorTheme = computed(() => {
    const t = theme.value
    return (t === 'indigo' || t === 'deep') ? 'dark' : 'light'
  })

  function setTheme(newTheme) {
    if (user.value) {
      user.value.theme = newTheme
      localStorage.setItem('wj_user', JSON.stringify(user.value))
      document.documentElement.setAttribute('data-theme', newTheme)
      api.put('/api/auth/theme?theme=' + newTheme) // 使用之前修复过的正确路径
    }
  }

  function applyTheme() {
    document.documentElement.setAttribute('data-theme', theme.value)
  }

  return { token, user, isLoggedIn, theme, editorTheme, login, logout, register, setTheme, applyTheme }
})
