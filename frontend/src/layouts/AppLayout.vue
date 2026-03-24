<template>
  <el-container class="app-layout">
    <!-- 侧边栏 -->
    <el-aside width="220px" class="sidebar">
      <div class="sidebar-header">
        <span class="sidebar-logo">📔</span>
        <div>
          <div class="sidebar-title">工作日志</div>
          <div class="sidebar-user">{{ auth.user?.display_name || auth.user?.username }}</div>
        </div>
      </div>

      <el-menu :default-active="route.path" router class="sidebar-menu">
        <el-menu-item index="/today">
          <el-icon><EditPen /></el-icon>
          <span>今日日志</span>
        </el-menu-item>
        <el-menu-item index="/calendar">
          <el-icon><Calendar /></el-icon>
          <span>日历视图</span>
        </el-menu-item>
        <el-menu-item index="/monthly">
          <el-icon><Document /></el-icon>
          <span>月度总结</span>
        </el-menu-item>
        <el-menu-item index="/aggregate">
          <el-icon><Memo /></el-icon>
          <span>季度/年度总结</span>
        </el-menu-item>
        <el-menu-item index="/stats">
          <el-icon><DataLine /></el-icon>
          <span>统计看板</span>
        </el-menu-item>
      </el-menu>

      <div class="sidebar-footer">
        <el-button text @click="handleLogout" class="logout-btn">
          <el-icon><SwitchButton /></el-icon> 退出登录
        </el-button>
      </div>
    </el-aside>

    <!-- 主内容 -->
    <el-main class="main-content">
      <router-view />
    </el-main>
  </el-container>
</template>

<script setup>
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { EditPen, Calendar, Document, DataLine, SwitchButton, Memo } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

function handleLogout() {
  auth.logout()
  router.push('/login')
}
</script>

<style scoped>
.app-layout { height: 100vh; background: #0f1117; }
.sidebar {
  background: #161b2e;
  border-right: 1px solid rgba(255,255,255,0.06);
  display: flex;
  flex-direction: column;
}
.sidebar-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 24px 20px 16px;
  border-bottom: 1px solid rgba(255,255,255,0.06);
}
.sidebar-logo { font-size: 28px; }
.sidebar-title { color: #fff; font-size: 15px; font-weight: 600; }
.sidebar-user { color: rgba(255,255,255,0.4); font-size: 12px; margin-top: 2px; }
.sidebar-menu {
  flex: 1;
  border: none;
  background: transparent;
  padding: 12px 0;
}
:deep(.el-menu-item) {
  color: rgba(255,255,255,0.5);
  border-radius: 8px;
  margin: 2px 8px;
  height: 44px;
}
:deep(.el-menu-item.is-active) {
  background: rgba(64,158,255,0.15) !important;
  color: #409eff !important;
}
:deep(.el-menu-item:hover) {
  background: rgba(255,255,255,0.05) !important;
  color: #fff !important;
}
.sidebar-footer {
  padding: 16px;
  border-top: 1px solid rgba(255,255,255,0.06);
}
.logout-btn { color: rgba(255,255,255,0.3); width: 100%; }
.logout-btn:hover { color: #f56c6c; }
.main-content {
  background: #0f1117;
  padding: 32px;
  overflow-y: auto;
}
</style>
