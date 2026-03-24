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

  return { token, user, isLoggedIn, login, logout, register }
})
