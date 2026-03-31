<template>
  <div class="app-wrapper">
    <!-- ====== Desktop Layout (PC 端原生布局) ====== -->
    <el-container v-if="!isMobile" class="app-layout desktop-layout">
      <el-aside width="220px" class="sidebar">
        <div class="sidebar-header">
          <span class="sidebar-logo">📔</span>
          <div>
            <div class="sidebar-title">工作日志</div>
            <div class="sidebar-user">{{ auth.user?.display_name || auth.user?.username }}</div>
          </div>
        </div>

        <el-menu :default-active="route.path" router class="sidebar-menu">
          <el-menu-item index="/today"><el-icon><EditPen /></el-icon><span>今日日志</span></el-menu-item>
          <el-menu-item index="/calendar"><el-icon><Calendar /></el-icon><span>日历视图</span></el-menu-item>
          <el-menu-item index="/monthly"><el-icon><Document /></el-icon><span>月度总结</span></el-menu-item>
          <el-menu-item index="/aggregate"><el-icon><Memo /></el-icon><span>季度/年度总结</span></el-menu-item>
          <el-menu-item index="/stats"><el-icon><DataLine /></el-icon><span>统计看板</span></el-menu-item>
          <el-menu-item index="/tools"><el-icon><Setting /></el-icon><span>实用小工具</span></el-menu-item>
        </el-menu>

        <div class="sidebar-footer">
          <div class="theme-selector-wrapper" v-if="auth.user">
            <el-select :model-value="auth.user.theme" @change="auth.setTheme" size="small" class="theme-select">
              <template #prefix>
                <el-icon><MagicStick /></el-icon>
              </template>
              <el-option label="🌌 Indigo 深蓝渐变" value="indigo" />
              <el-option label="☀️ Light 极简亮色" value="light" />
              <el-option label="🌑 Deep 深空纯黑" value="deep" />
              <el-option label="📜 Sepia 复古护眼" value="sepia" />
            </el-select>
          </div>
          <el-button text @click="handleLogout" class="logout-btn">
            <el-icon><SwitchButton /></el-icon> 退出登录
          </el-button>
        </div>
      </el-aside>

      <el-main class="main-content">
        <router-view />
      </el-main>
    </el-container>

    <!-- ====== Mobile Layout (移动端分离布局) ====== -->
    <el-container v-else class="app-layout mobile-layout" direction="vertical">
      <div class="mobile-header">
        <div class="mobile-header-left">
          <span class="sidebar-logo">📔</span>
          <span class="sidebar-title" style="margin-left:12px;">工作日志</span>
        </div>
        <el-button text @click="drawerVisible = true">
          <el-icon :size="24" class="mobile-menu-icon"><Menu /></el-icon>
        </el-button>
      </div>

      <el-main class="main-content">
        <router-view />
      </el-main>

      <!-- 移动端专供：侧滑抽屉导航 -->
      <el-drawer
        v-model="drawerVisible"
        direction="ltr"
        size="240px"
        :with-header="false"
        class="mobile-drawer"
      >
        <div class="sidebar mobile-sidebar-content">
          <div class="sidebar-header">
            <span class="sidebar-logo">📔</span>
            <div>
              <div class="sidebar-title">导航快连</div>
              <div class="sidebar-user">{{ auth.user?.display_name || auth.user?.username }}</div>
            </div>
          </div>
          <el-menu :default-active="route.path" router class="sidebar-menu" @select="drawerVisible = false">
            <el-menu-item index="/today"><el-icon><EditPen /></el-icon><span>今日日志</span></el-menu-item>
            <el-menu-item index="/calendar"><el-icon><Calendar /></el-icon><span>日历视图</span></el-menu-item>
            <el-menu-item index="/monthly"><el-icon><Document /></el-icon><span>月度总结</span></el-menu-item>
            <el-menu-item index="/aggregate"><el-icon><Memo /></el-icon><span>季度/年度总结</span></el-menu-item>
            <el-menu-item index="/stats"><el-icon><DataLine /></el-icon><span>统计看板</span></el-menu-item>
            <el-menu-item index="/tools"><el-icon><Setting /></el-icon><span>实用小工具</span></el-menu-item>
          </el-menu>
          <div class="sidebar-footer">
            <div class="theme-selector-wrapper" v-if="auth.user">
              <el-select :model-value="auth.user.theme" @change="auth.setTheme" size="small" class="theme-select">
                <template #prefix>
                  <el-icon><MagicStick /></el-icon>
                </template>
                <el-option label="🌌 Indigo 深蓝渐变" value="indigo" />
                <el-option label="☀️ Light 极简亮色" value="light" />
                <el-option label="🌑 Deep 深空纯黑" value="deep" />
                <el-option label="📜 Sepia 复古护眼" value="sepia" />
              </el-select>
            </div>
            <el-button text @click="handleLogout" class="logout-btn">
              <el-icon><SwitchButton /></el-icon> 退出登录
            </el-button>
          </div>
        </div>
      </el-drawer>
    </el-container>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { EditPen, Calendar, Document, DataLine, SwitchButton, Memo, Setting, Menu, MagicStick } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const drawerVisible = ref(false)
const isMobile = ref(false)

const checkMobile = () => {
  isMobile.value = window.innerWidth <= 768
}

onMounted(() => {
  auth.applyTheme()
  checkMobile()
  window.addEventListener('resize', checkMobile)
})

onUnmounted(() => {
  window.removeEventListener('resize', checkMobile)
})

function handleLogout() {
  auth.logout()
  router.push('/login')
}
</script>

<style>
.mobile-drawer .el-drawer__body {
  padding: 0;
  background-color: var(--bg-color-main);
}
</style>

<style scoped>
.app-wrapper { width: 100%; height: 100vh; }
.app-layout { height: 100vh; background: transparent; }

.sidebar {
  background: var(--sidebar-bg);
  backdrop-filter: var(--sidebar-blur);
  -webkit-backdrop-filter: var(--sidebar-blur);
  border-right: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
}
.mobile-sidebar-content { height: 100%; border-right: none; }

.sidebar-header {
  display: flex; align-items: center; gap: 12px;
  padding: 24px 20px 16px;
  border-bottom: 1px solid var(--border-color);
}
.sidebar-logo { font-size: 28px; }
.sidebar-title { color: var(--sidebar-text-main); font-size: 15px; font-weight: 600; }
.sidebar-user { color: var(--sidebar-text-item); font-size: 12px; margin-top: 2px; opacity: 0.8; }

.sidebar-menu {
  flex: 1; border: none; background: transparent; padding: 12px 0; overflow-y: auto;
}
:deep(.el-menu-item) {
  color: var(--sidebar-text-item) !important; 
  border-radius: 8px; 
  margin: 2px 8px; 
  height: 44px;
  transition: all 0.2s ease;
}
:deep(.el-menu-item.is-active) {
  background: rgba(99, 102, 241, 0.12) !important; 
  color: var(--sidebar-text-active) !important;
  font-weight: 600;
}
:deep(.el-menu-item:hover) {
  background: rgba(255,255,255,0.05) !important; 
  color: var(--sidebar-text-main) !important;
}

.sidebar-footer { padding: 16px; border-top: 1px solid var(--border-color); }
.theme-selector-wrapper { margin-bottom: 10px; }
.logout-btn { color: var(--sidebar-text-item); width: 100%; justify-content: flex-start; }
.logout-btn:hover { color: #f56c6c; background: rgba(245, 108, 108, 0.05) !important; }

.mobile-header {
  display: flex; 
  background: var(--sidebar-bg);
  backdrop-filter: var(--sidebar-blur);
  -webkit-backdrop-filter: var(--sidebar-blur);
  border-bottom: 1px solid var(--border-color); 
  align-items: center; 
  justify-content: space-between; 
  padding: 10px 16px;
}
.mobile-header-left { display: flex; align-items: center; }
.mobile-menu-icon { color: var(--sidebar-text-main); }

.main-content {
  background: transparent;
  padding: 32px;
  overflow-y: auto;
}

@media screen and (max-width: 768px) {
  .main-content { padding: 16px !important; }
}
</style>
