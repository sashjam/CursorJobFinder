import { defineStore } from 'pinia'
import { ref } from 'vue'
import { ensureCsrf, http } from '../api/http'

export type AuthUser = {
  id: number
  name: string
  email: string
}

export const useAuthStore = defineStore('auth', () => {
  const user = ref<AuthUser | null>(null)
  const checked = ref(false)

  async function fetchUser(): Promise<boolean> {
    try {
      const { data } = await http.get<{ user: AuthUser }>('/user')
      user.value = data.user
      return true
    } catch {
      user.value = null
      return false
    } finally {
      checked.value = true
    }
  }

  async function login(email: string, password: string): Promise<void> {
    await ensureCsrf()
    const { data } = await http.post<{ user: AuthUser }>('/login', { email, password })
    user.value = data.user
    checked.value = true
  }

  async function register(name: string, email: string, password: string, password_confirmation: string): Promise<void> {
    await ensureCsrf()
    const { data } = await http.post<{ user: AuthUser }>('/register', {
      name,
      email,
      password,
      password_confirmation,
    })
    user.value = data.user
    checked.value = true
  }

  async function logout(): Promise<void> {
    await ensureCsrf()
    try {
      await http.post('/logout')
    } finally {
      user.value = null
    }
  }

  return { user, checked, fetchUser, login, register, logout }
})
