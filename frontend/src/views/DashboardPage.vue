<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import api from '@/composables/api'

interface Pet { id: string; name: string; species: string; breed?: string }
const auth = useAuthStore()
const pets = ref<Pet[]>([])
const selectedPetId = ref('')
const stats = ref({ pets: 0, feedings: 0, excretions: 0, behaviors: 0 })
const newPetName = ref('')
const newPetSpecies = ref('cat')
const FOOD_TYPE_OPTIONS = ['狗粮', '猫粮', '零食', '自制', '罐头', '生骨肉', '冻干', '处方粮', '其他']
const foodType = ref('')
const amount = ref<number | null>(null)
const activeTab = ref<'feeding' | 'excretion' | 'behavior'>('feeding')
const message = ref('')
const selectedPet = computed(() => pets.value.find((pet) => pet.id === selectedPetId.value))

async function refresh() {
  const [petResponse, dashboardResponse] = await Promise.all([api.get('/pets'), api.get('/dashboard')])
  pets.value = petResponse.data
  if (!selectedPetId.value && pets.value.length) selectedPetId.value = pets.value[0].id
  stats.value = dashboardResponse.data
}

async function addPet() {
  if (!newPetName.value.trim()) return
  const { data } = await api.post('/pets', { name: newPetName.value, species: newPetSpecies.value })
  pets.value.push(data)
  selectedPetId.value = data.id
  newPetName.value = ''
  await refresh()
}

async function quickFeed() {
  if (!selectedPetId.value || !foodType.value.trim()) return
  await api.post(`/pets/${selectedPetId.value}/feedings`, { food_type: foodType.value, amount: amount.value })
  foodType.value = ''
  amount.value = null
  message.value = '已记录一餐。'
  await refresh()
}

async function quickRecord() {
  if (!selectedPetId.value) return
  const endpoints = { excretion: 'excretions', behavior: 'behaviors' }
  const payload = activeTab.value === 'excretion'
    ? { type: 'normal', consistency: 'normal' }
    : { behavior_type: 'daily activity', mood: 'normal' }
  await api.post(`/pets/${selectedPetId.value}/${endpoints[activeTab.value as 'excretion' | 'behavior']}`, payload)
  message.value = activeTab.value === 'excretion' ? '已记录排便。' : '已记录行为。'
  await refresh()
}

onMounted(refresh)
</script>

<template>
  <div class="min-h-[100dvh] bg-surface-50">
    <header class="bg-white/80 backdrop-blur-xl border-b border-surface-200 sticky top-0 z-40">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <RouterLink to="/" class="flex items-center gap-2"><span class="text-2xl">🐾</span><span class="text-lg font-bold text-primary-600">Pet Tracker</span></RouterLink>
        <div class="flex items-center gap-4 text-sm text-surface-500">
          <RouterLink to="/records" class="hover:text-primary-600 transition-colors">记录中心</RouterLink>
          <span>{{ auth.user?.display_name || auth.user?.email }}</span><button class="btn-ghost !px-3 !py-2" @click="auth.logout()">退出</button></div>
      </div>
    </header>
    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      <section class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div><h1 class="text-3xl font-extrabold text-surface-900">宠物控制面板</h1><p class="mt-1 text-surface-500">记录日常，读懂每一次变化。</p></div>
        <select v-model="selectedPetId" class="rounded-xl border-surface-200 bg-white" :disabled="!pets.length"><option v-for="pet in pets" :key="pet.id" :value="pet.id">{{ pet.name }} · {{ pet.species }}</option><option v-if="!pets.length" value="">先添加一只宠物</option></select>
      </section>
      <section class="grid grid-cols-2 gap-4 lg:grid-cols-4"><div v-for="item in [{ label: '我的宠物', value: stats.pets, icon: '🐾' }, { label: '进食记录', value: stats.feedings, icon: '🍽️' }, { label: '排便记录', value: stats.excretions, icon: '💩' }, { label: '行为记录', value: stats.behaviors, icon: '🏃' }]" :key="item.label" class="glass-card p-5"><span class="text-2xl">{{ item.icon }}</span><p class="mt-3 text-3xl font-bold text-primary-600">{{ item.value }}</p><p class="text-sm text-surface-500">{{ item.label }}</p></div></section>
      <section class="grid gap-6 lg:grid-cols-2">
        <div class="glass-card p-6"><h2 class="text-xl font-bold text-surface-900">添加宠物</h2><form class="mt-4 flex flex-col gap-3 sm:flex-row" @submit.prevent="addPet"><input v-model="newPetName" required placeholder="宠物名字" class="flex-1 rounded-xl border-surface-200" /><select v-model="newPetSpecies" class="rounded-xl border-surface-200"><option value="cat">猫</option><option value="dog">狗</option><option value="other">其他</option></select><button class="btn-primary" type="submit">添加</button></form><p v-if="selectedPet" class="mt-4 text-sm text-surface-500">当前正在记录：<strong>{{ selectedPet.name }}</strong></p></div>
        <div class="glass-card p-6"><h2 class="text-xl font-bold text-surface-900">快速打卡</h2><div class="mt-4 flex gap-2"><button v-for="tab in [['feeding','进食'], ['excretion','排便'], ['behavior','行为']] as const" :key="tab[0]" class="rounded-lg px-3 py-2 text-sm" :class="activeTab === tab[0] ? 'bg-primary-600 text-white' : 'bg-surface-100 text-surface-500'" @click="activeTab = tab[0]">{{ tab[1] }}</button></div><form v-if="activeTab === 'feeding'" class="mt-4 flex flex-col gap-3 sm:flex-row" @submit.prevent="quickFeed"><select v-model="foodType" required class="flex-1 rounded-xl border-surface-200"><option value="" disabled>选择食物类型</option><option v-for="opt in FOOD_TYPE_OPTIONS" :key="opt" :value="opt">{{ opt }}</option></select><input v-model.number="amount" type="number" min="0" placeholder="克数（可选）" class="w-36 rounded-xl border-surface-200"/><button :disabled="!selectedPetId" class="btn-primary">记录</button></form><button v-else :disabled="!selectedPetId" class="btn-primary mt-4" @click="quickRecord">一键记录{{ activeTab === 'excretion' ? '正常排便' : '日常行为' }}</button><p v-if="message" class="mt-3 text-sm text-green-700">{{ message }}</p></div>
      </section>
    </main>
  </div>
</template>
