<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { http } from '../api/http'

type Source = { id: string; name: string; hint: string }
type Sub = {
  id: number
  name: string
  source: string
  query: string
  exclude_words: string
  enabled: boolean
  last_checked_at: string | null
}

const sources = ref<Source[]>([])
const items = ref<Sub[]>([])
const name = ref('')
const source = ref('habr_rss')
const query = ref('')
const exclude = ref('')
const status = ref('')

const queryHint = computed(() => sources.value.find((s) => s.id === source.value)?.hint || '')

async function load() {
  const [meta, subs] = await Promise.all([
    http.get<{ sources: Source[] }>('/meta/sources'),
    http.get<{ items: Sub[] }>('/subscriptions'),
  ])
  sources.value = meta.data.sources
  items.value = subs.data.items
  if (!sources.value.find((s) => s.id === source.value) && sources.value[0]) {
    source.value = sources.value[0].id
  }
}

async function add() {
  status.value = ''
  await http.post('/subscriptions', {
    name: name.value,
    source: source.value,
    query: query.value,
    exclude_words: exclude.value,
  })
  name.value = ''
  query.value = ''
  exclude.value = ''
  status.value = 'Подписка добавлена'
  await load()
}

async function toggleEnabled(sub: Sub) {
  await http.patch(`/subscriptions/${sub.id}`, { enabled: !sub.enabled })
  await load()
}

async function remove(id: number) {
  await http.delete(`/subscriptions/${id}`)
  await load()
}

onMounted(load)
</script>

<template>
  <div class="card">
    <h2 style="margin-top: 0">Подписки</h2>
    <div class="grid-2">
      <div class="form-row">
        <label>Название</label>
        <input v-model="name" class="input" placeholder="Python — Хабр" />
      </div>
      <div class="form-row">
        <label>Источник</label>
        <select v-model="source" class="select">
          <option v-for="s in sources" :key="s.id" :value="s.id">{{ s.name }}</option>
        </select>
      </div>
      <div class="form-row">
        <label>Запрос</label>
        <input v-model="query" class="input" placeholder="python remote" />
        <span class="status">{{ queryHint }}</span>
      </div>
      <div class="form-row">
        <label>Исключить слова</label>
        <input v-model="exclude" class="input" placeholder="стажёр, intern" />
      </div>
    </div>
    <button class="btn btn-primary" type="button" @click="add">Добавить</button>
    <p v-if="status" class="status">{{ status }}</p>

    <ul class="list" style="margin-top: 20px">
      <li v-for="sub in items" :key="sub.id">
        <strong>{{ sub.name }}</strong>
        ({{ sub.source }}) — «{{ sub.query || '—' }}»
        <div class="status">
          {{ sub.enabled ? 'вкл' : 'выкл' }}
          <span v-if="sub.last_checked_at"> · проверено {{ sub.last_checked_at }}</span>
        </div>
        <div class="toolbar">
          <button class="btn" type="button" @click="toggleEnabled(sub)">
            {{ sub.enabled ? 'Выключить' : 'Включить' }}
          </button>
          <button class="btn btn-danger" type="button" @click="remove(sub.id)">Удалить</button>
        </div>
      </li>
    </ul>
    <p v-if="!items.length" class="status">Подписок пока нет.</p>
  </div>
</template>
