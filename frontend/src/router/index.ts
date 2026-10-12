import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('../views/LoginView.vue'),
      meta: { guest: true },
    },
    {
      path: '/register',
      name: 'register',
      component: () => import('../views/RegisterView.vue'),
      meta: { guest: true },
    },
    {
      path: '/',
      component: () => import('../layouts/AppLayout.vue'),
      meta: { requiresAuth: true },
      children: [
        { path: '', redirect: '/vacancies' },
        {
          path: 'vacancies',
          name: 'vacancies',
          component: () => import('../views/VacanciesView.vue'),
        },
        {
          path: 'desired',
          name: 'desired',
          component: () => import('../views/DesiredView.vue'),
        },
        {
          path: 'subscriptions',
          name: 'subscriptions',
          component: () => import('../views/SubscriptionsView.vue'),
        },
      ],
    },
    { path: '/:pathMatch(.*)*', redirect: '/vacancies' },
  ],
})

router.beforeEach(async (to) => {
  const auth = useAuthStore()
  if (!auth.checked) {
    await auth.fetchUser()
  }

  if (to.meta.requiresAuth && !auth.user) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }

  if (to.meta.guest && auth.user) {
    return { name: 'vacancies' }
  }

  return true
})

export default router
