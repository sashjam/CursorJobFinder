<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { http } from '../api/http'

const text = ref('')
const useDesired = ref(true)
const usePostFilter = ref(false)
const locations = ref<string[]>([])
const cityOptions = ref<string[]>([])
const status = ref('')
const hint = ref('')

async function loadMeta() {
  const { data } = await http.get<{ city_options: string[] }>('/meta/sources')
  cityOptions.value = data.city_options || []
}

async function load() {
  const { data } = await http.get<{
    desired_vacancy: string
    use_desired_vacancy_search: boolean
    use_desired_post_filter: boolean
    desired_locations: string[]
  }>('/desired')
  text.value = data.desired_vacancy || ''
  useDesired.value = data.use_desired_vacancy_search
  usePostFilter.value = data.use_desired_post_filter
  locations.value = data.desired_locations || []
}

async function save() {
  status.value = 'Сохранение…'
  await http.put('/desired', {
    desired_vacancy: text.value,
    use_desired_vacancy_search: useDesired.value,
    use_desired_post_filter: usePostFilter.value,
    desired_locations: locations.value,
  })
  status.value = 'Сохранено'
}

async function saveAndFetch() {
  await save()
  await http.post('/fetch')
  status.value = 'Сохранено и запущен опрос сайтов'
}

function toggleCity(city: string) {
  if (locations.value.includes(city)) {
    locations.value = locations.value.filter((c) => c !== city)
  } else {
    locations.value = [...locations.value, city]
  }
}

onMounted(async () => {
  await loadMeta()
  await load()
})
</script>

<template>
  <div class="card">
    <h2 style="margin-top: 0">Желаемая работа</h2>
    <textarea v-model="text" placeholder="Описание идеальной вакансии…" />
    <div class="toolbar" style="margin-top: 12px">
      <label><input v-model="useDesired" type="checkbox" /> Искать по описанию</label>
      <label><input v-model="usePostFilter" type="checkbox" /> Жёсткий фильтр по тексту</label>
    </div>
    <p class="status">Города (фильтр после загрузки):</p>
    <div class="grid-2">
      <label v-for="city in cityOptions" :key="city" style="font-size: 14px">
        <input
          type="checkbox"
          :checked="locations.includes(city)"
          @change="toggleCity(city)"
        />
        {{ city }}
      </label>
    </div>
    <div class="toolbar" style="margin-top: 12px">
      <button class="btn btn-primary" type="button" @click="save">Сохранить</button>
      <button class="btn" type="button" @click="saveAndFetch">Сохранить и искать</button>
    </div>
    <p v-if="hint" class="status">{{ hint }}</p>
    <p v-if="status" class="status">{{ status }}</p>
  </div>
</template>
