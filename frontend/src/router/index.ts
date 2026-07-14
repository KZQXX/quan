import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'landing',
      component: () => import('@/views/LandingPage.vue'),
    },
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/LoginPage.vue'),
    },
    {
      path: '/register',
      name: 'register',
      component: () => import('@/views/RegisterPage.vue'),
    },
    {
      path: '/dashboard',
      name: 'dashboard',
      component: () => import('@/views/DashboardPage.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/records',
      name: 'records',
      component: () => import('@/views/RecordCenterPage.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/reminders',
      name: 'reminders',
      component: () => import('@/views/ReminderPage.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/stats',
      name: 'stats',
      component: () => import('@/views/StatsPage.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/report',
      name: 'report',
      component: () => import('@/views/ReportPage.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/:pathMatch(.*)*',
      name: 'not-found',
      component: () => import('@/views/NotFoundPage.vue'),
    },
  ],
})

router.beforeEach((to) => {
  const auth = useAuthStore()
  if (to.meta.requiresAuth && !auth.isAuthenticated) return { name: 'login' }
  if ((to.name === 'login' || to.name === 'register') && auth.isAuthenticated) return { name: 'dashboard' }
})

export default router
