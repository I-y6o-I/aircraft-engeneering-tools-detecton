import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import AuthView from '@/views/AuthView.vue'
import HomeView from '@/views/HomeView.vue'
import RecognitionView from '@/views/RecognitionView.vue'
import SessionView from '@/views/SessionView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'Home',
      component: HomeView
    },
    {
      path: '/auth',
      name: 'Auth',
      component: AuthView
    },
    {
      path: '/dashboard',
      name: 'Dashboard',
      component: () => import('@/views/DashboardView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/recognition',
      name: 'Recognition',
      component: RecognitionView
    },
    {
      path: '/sessions/:id',
      name: 'Session',
      component: SessionView,
      meta: { requiresAuth: true }
    }
  ],
})

// Navigation guards
router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()
  
  // Initialize auth state (now async)
  await authStore.initializeAuth()
  
  if (to.meta.requiresAuth && !authStore.checkAuth()) {
    next('/auth')
  } else if (to.path === '/auth' && authStore.checkAuth()) {
    next('/dashboard')
  } else {
    next()
  }
})

export default router
