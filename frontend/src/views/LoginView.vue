<template>
  <div class="login-page">
    <div class="login-card">
      <div class="logo">
        <span class="logo-icon">📔</span>
        <h1>工作日志</h1>
        <p>Work Journal</p>
      </div>

      <el-tabs v-model="tab" class="login-tabs">
        <el-tab-pane label="登 录" name="login">
          <el-form :model="loginForm" @submit.prevent="handleLogin">
            <el-form-item>
              <el-input v-model="loginForm.username" placeholder="用户名" prefix-icon="User" size="large" />
            </el-form-item>
            <el-form-item>
              <el-input v-model="loginForm.password" type="password" placeholder="密码" prefix-icon="Lock" size="large" show-password />
            </el-form-item>
            <el-button type="primary" native-type="submit" size="large" :loading="loading" class="submit-btn">
              登 录
            </el-button>
          </el-form>
        </el-tab-pane>

        <el-tab-pane label="注 册" name="register">
          <el-form :model="regForm" @submit.prevent="handleRegister">
            <el-form-item>
              <el-input v-model="regForm.username" placeholder="用户名" prefix-icon="User" size="large" />
            </el-form-item>
            <el-form-item>
              <el-input v-model="regForm.display_name" placeholder="显示名称（如：张三）" prefix-icon="Avatar" size="large" />
            </el-form-item>
            <el-form-item>
              <el-input v-model="regForm.dept" placeholder="部门（如：质量技术部）" prefix-icon="OfficeBuilding" size="large" />
            </el-form-item>
            <el-form-item>
              <el-input v-model="regForm.password" type="password" placeholder="密码" prefix-icon="Lock" size="large" show-password />
            </el-form-item>
            <el-button type="primary" native-type="submit" size="large" :loading="loading" class="submit-btn">
              注 册
            </el-button>
          </el-form>
        </el-tab-pane>
      </el-tabs>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'

const router = useRouter()
const auth = useAuthStore()
const tab = ref('login')
const loading = ref(false)
const loginForm = ref({ username: '', password: '' })
const regForm = ref({ username: '', display_name: '', dept: '', password: '' })

async function handleLogin() {
  if (!loginForm.value.username || !loginForm.value.password) {
    return ElMessage.warning('请填写用户名和密码')
  }
  loading.value = true
  try {
    await auth.login(loginForm.value.username, loginForm.value.password)
    router.push('/today')
  } finally {
    loading.value = false
  }
}

async function handleRegister() {
  if (!regForm.value.username || !regForm.value.password) {
    return ElMessage.warning('请填写用户名和密码')
  }
  loading.value = true
  try {
    await auth.register(regForm.value)
    ElMessage.success('注册成功，请登录')
    tab.value = 'login'
    loginForm.value.username = regForm.value.username
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #1a1f36 0%, #2d3561 50%, #1a1f36 100%);
}
.login-card {
  width: 400px;
  background: rgba(255,255,255,0.05);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 20px;
  padding: 40px;
}
.logo {
  text-align: center;
  margin-bottom: 32px;
}
.logo-icon { font-size: 48px; }
.logo h1 {
  color: #fff;
  font-size: 24px;
  margin: 8px 0 4px;
}
.logo p { color: rgba(255,255,255,0.4); font-size: 13px; margin: 0; }
.submit-btn { width: 100%; margin-top: 8px; }
:deep(.el-tabs__nav-wrap::after) { display: none; }
:deep(.el-tabs__item) { color: rgba(255,255,255,0.5); }
:deep(.el-tabs__item.is-active) { color: #fff; }
:deep(.el-tabs__active-bar) { background: #409eff; }
</style>
