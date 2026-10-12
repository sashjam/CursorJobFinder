<script setup lang="ts">
import { RouterLink, RouterView, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const router = useRouter()

async function onLogout() {
  await auth.logout()
  router.push({ name: 'login' })
}
</script>

<template>
  <div class="app-shell">
    <header class="app-header">
      <div>
        <strong>JobDesk</strong>
        <span v-if="auth.user" style="margin-left: 8px; opacity: 0.8; font-size: 13px">
          {{ auth.user.name }}
        </span>
      </div>
      <nav>
        <RouterLink to="/vacancies">Вакансии</RouterLink>
        <RouterLink to="/desired">Желаемая работа</RouterLink>
        <RouterLink to="/subscriptions">Подписки</RouterLink>
        <button class="btn" type="button" @click="onLogout">Выйти</button>
      </nav>
    </header>
    <main class="app-main">
      <RouterView />
    </main>
  </div>
</template>
