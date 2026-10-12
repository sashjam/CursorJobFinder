<script setup lang="ts">
import { ref } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()

const email = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

async function submit() {
  error.value = ''
  loading.value = true
  try {
    await auth.login(email.value, password.value)
    const redirect = (route.query.redirect as string) || '/vacancies'
    router.push(redirect)
  } catch (e: unknown) {
    const msg =
      (e as { response?: { data?: { message?: string; errors?: Record<string, string[]> } } })
        .response?.data?.errors?.email?.[0] ||
      (e as { response?: { data?: { message?: string } } }).response?.data?.message ||
      'Не удалось войти'
    error.value = msg
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="auth-page">
    <div class="card auth-card">
      <h1 style="margin-top: 0">Вход</h1>
      <p class="status">Без авторизации интерфейс недоступен.</p>
      <form @submit.prevent="submit">
        <div class="form-row">
          <label>Email</label>
          <input v-model="email" class="input" type="email" required autocomplete="username" />
        </div>
        <div class="form-row">
          <label>Пароль</label>
          <input
            v-model="password"
            class="input"
            type="password"
            required
            autocomplete="current-password"
          />
        </div>
        <p v-if="error" class="error">{{ error }}</p>
        <button class="btn btn-primary" type="submit" :disabled="loading">
          {{ loading ? '…' : 'Войти' }}
        </button>
      </form>
      <p class="status" style="margin-top: 16px">
        Нет аккаунта?
        <RouterLink to="/register">Регистрация</RouterLink>
      </p>
    </div>
  </div>
</template>
