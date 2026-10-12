<script setup lang="ts">
import { ref } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const router = useRouter()

const name = ref('')
const email = ref('')
const password = ref('')
const passwordConfirmation = ref('')
const error = ref('')
const loading = ref(false)

async function submit() {
  error.value = ''
  loading.value = true
  try {
    await auth.register(name.value, email.value, password.value, passwordConfirmation.value)
    router.push('/vacancies')
  } catch (e: unknown) {
    const data = (e as { response?: { data?: { errors?: Record<string, string[]>; message?: string } } })
      .response?.data
    error.value =
      data?.errors?.email?.[0] ||
      data?.errors?.password?.[0] ||
      data?.message ||
      'Не удалось зарегистрироваться'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="auth-page">
    <div class="card auth-card">
      <h1 style="margin-top: 0">Регистрация</h1>
      <form @submit.prevent="submit">
        <div class="form-row">
          <label>Имя</label>
          <input v-model="name" class="input" required autocomplete="name" />
        </div>
        <div class="form-row">
          <label>Email</label>
          <input v-model="email" class="input" type="email" required autocomplete="username" />
        </div>
        <div class="form-row">
          <label>Пароль (мин. 8 символов)</label>
          <input v-model="password" class="input" type="password" required autocomplete="new-password" />
        </div>
        <div class="form-row">
          <label>Повтор пароля</label>
          <input
            v-model="passwordConfirmation"
            class="input"
            type="password"
            required
            autocomplete="new-password"
          />
        </div>
        <p v-if="error" class="error">{{ error }}</p>
        <button class="btn btn-primary" type="submit" :disabled="loading">
          {{ loading ? '…' : 'Создать аккаунт' }}
        </button>
      </form>
      <p class="status" style="margin-top: 16px">
        Уже есть аккаунт?
        <RouterLink to="/login">Войти</RouterLink>
      </p>
    </div>
  </div>
</template>
