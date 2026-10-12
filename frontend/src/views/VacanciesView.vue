<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { http } from '../api/http'

type Vacancy = {
  id: number
  title: string
  company: string
  url: string
  source: string
  city: string
  is_new: boolean
}

const items = ref<Vacancy[]>([])
const newCount = ref(0)
const newOnly = ref(true)
const status = ref('')
const loading = ref(false)

async function load() {
  loading.value = true
  status.value = ''
  try {
    const { data } = await http.get<{ items: Vacancy[]; new_count: number }>('/vacancies', {
      params: { new_only: newOnly.value ? 1 : 0 },
    })
    items.value = data.items
    newCount.value = data.new_count
  } catch {
    status.value = 'Не удалось загрузить список'
  } finally {
    loading.value = false
  }
}

async function fetchFromSites() {
  loading.value = true
  status.value = 'Опрос сайтов…'
  try {
    const { data } = await http.post<{
      ok: boolean
      message?: string
      errors?: string[]
      new_count?: number
    }>('/fetch')
    if (!data.ok) {
      status.value = data.message || 'Ошибка опроса'
    } else {
      const errText = (data.errors || []).filter(Boolean).join(' · ')
      status.value = errText
        ? `Готово. Новых: ${data.new_count ?? 0}. ${errText}`
        : `Готово. Новых: ${data.new_count ?? 0}`
    }
    await load()
  } catch (e: unknown) {
    status.value =
      (e as { response?: { data?: { message?: string } } }).response?.data?.message ||
      'Ошибка опроса'
  } finally {
    loading.value = false
  }
}

async function markSeen(id: number) {
  await http.post(`/vacancies/${id}/seen`)
  await load()
}

async function markAllSeen() {
  await http.post('/vacancies/mark-all-seen')
  await load()
}

onMounted(load)
</script>

<template>
  <div class="card">
    <h2 style="margin-top: 0">Вакансии</h2>
    <div class="toolbar">
      <button class="btn btn-primary" type="button" :disabled="loading" @click="fetchFromSites">
        Обновить с сайтов
      </button>
      <button class="btn" type="button" :disabled="loading" @click="load">Обновить список</button>
      <button class="btn" type="button" :disabled="loading" @click="markAllSeen">Отметить все просмотренными</button>
      <label style="font-size: 14px">
        <input v-model="newOnly" type="checkbox" @change="load" />
        Только новые
      </label>
      <span class="status">Новых: {{ newCount }}</span>
    </div>
    <p v-if="status" class="status">{{ status }}</p>
    <ul v-if="items.length" class="list">
      <li v-for="v in items" :key="v.id" :class="{ muted: !v.is_new }">
        <div>
          <span v-if="v.is_new">🆕 </span>
          <strong>{{ v.title }}</strong>
          <span v-if="v.company"> — {{ v.company }}</span>
        </div>
        <div class="status">
          {{ v.source }}
          <span v-if="v.city"> · {{ v.city }}</span>
          ·
          <a :href="v.url" target="_blank" rel="noopener">Открыть</a>
          ·
          <button v-if="v.is_new" class="btn" type="button" @click="markSeen(v.id)">Просмотрено</button>
        </div>
      </li>
    </ul>
    <p v-else-if="!loading" class="status">Список пуст. Добавьте подписки и нажмите «Обновить с сайтов».</p>
  </div>
</template>
