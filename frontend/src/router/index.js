import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/LoginView.vue'),
    meta: { public: true }
  },
  {
    path: '/',
    component: () => import('@/layouts/AppLayout.vue'),
    children: [
      {
        path: '',
        redirect: '/today'
      },
      {
        path: 'today',
        name: 'Today',
        component: () => import('@/views/TodayView.vue'),
        meta: { title: '今日日志' }
      },
      {
        path: 'calendar',
        name: 'Calendar',
        component: () => import('@/views/CalendarView.vue'),
        meta: { title: '日历' }
      },
      {
        path: 'monthly',
        name: 'Monthly',
        component: () => import('@/views/MonthlyView.vue'),
        meta: { title: '月度总结' }
      },
      {
        path: 'aggregate',
        name: 'Aggregate',
        component: () => import('@/views/AggregateView.vue'),
        meta: { title: '季度/年度总结' }
      },
      {
        path: 'stats',
        name: 'Stats',
        component: () => import('@/views/StatsView.vue'),
        meta: { title: '统计' }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach((to) => {
  const auth = useAuthStore()
  if (!to.meta.public && !auth.token) {
    return '/login'
  }
  if (to.path === '/login' && auth.token) {
    return '/'
  }
})

export default router
