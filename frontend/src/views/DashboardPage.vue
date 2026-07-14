<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import api from '@/composables/api'

interface Pet { id: string; name: string; species: string; breed?: string }
interface TodayStat { id: string; pet_id: string; date: string; feeding_count: number; excretion_count: number; behavior_count: number; total_duration_minutes: number }
interface DashboardStats { pets: number; feedings: number; excretions: number; behaviors: number; reminders: number; unread_notifications: number; today_stats: TodayStat[] }

const auth = useAuthStore()
const pets = ref<Pet[]>([])
const selectedPetId = ref('')
const stats = ref<DashboardStats>({ pets: 0, feedings: 0, excretions: 0, behaviors: 0, reminders: 0, unread_notifications: 0, today_stats: [] })
const newPetName = ref('')
const newPetSpecies = ref('cat')
const FOOD_TYPE_OPTIONS = ['狗粮', '猫粮', '零食', '自制', '罐头', '生骨肉', '冻干', '处方粮', '其他']
const foodType = ref('')
const amount = ref<number | null>(null)
const activeTab = ref<'feeding' | 'excretion' | 'behavior'>('feeding')
const message = ref('')
const selectedPet = computed(() => pets.value.find((pet) => pet.id === selectedPetId.value))

// Compute today's totals across all pets
const todayTotal = computed(() => {
  const s = stats.value.today_stats
  if (!s.length) return null
  return {
    feedings: s.reduce((a, x) => a + x.feeding_count, 0),
    excretions: s.reduce((a, x) => a + x.excretion_count, 0),
    behaviors: s.reduce((a, x) => a + x.behavior_count, 0),
    duration: s.reduce((a, x) => a + x.total_duration_minutes, 0),
  }
})

function petName(pid: string) {
  return pets.value.find((p) => p.id === pid)?.name ?? '未知'
}

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
    ? { type: '正常', consistency: '正常' }
    : { behavior_type: '玩耍', mood: '开心' }
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
          <RouterLink to="/reminders" class="hover:text-primary-600 transition-colors">提醒</RouterLink>
          <RouterLink to="/stats" class="hover:text-primary-600 transition-colors">统计</RouterLink>
          <span>{{ auth.user?.display_name || auth.user?.email }}</span><button class="btn-ghost !px-3 !py-2" @click="auth.logout()">退出</button></div>
      </div>
    </header>
    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      <!-- Title Row -->
      <section class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div><h1 class="text-3xl font-extrabold text-surface-900">宠物控制面板</h1><p class="mt-1 text-surface-500">记录日常，读懂每一次变化。</p></div>
        <select v-model="selectedPetId" class="rounded-xl border-surface-200 bg-white" :disabled="!pets.length"><option v-for="pet in pets" :key="pet.id" :value="pet.id">{{ pet.name }} · {{ pet.species }}</option><option v-if="!pets.length" value="">先添加一只宠物</option></select>
      </section>

      <!-- All-time Stats -->
      <section class="grid grid-cols-2 gap-4 lg:grid-cols-6">
        <div v-for="item in [
          { label: '我的宠物', value: stats.pets, icon: '🐾', color: 'text-primary-600' },
          { label: '提醒', value: stats.reminders, icon: '⏰', color: 'text-amber-500' },
          { label: '进食总次数', value: stats.feedings, icon: '🍽️', color: 'text-blue-600' },
          { label: '排便总次数', value: stats.excretions, icon: '💩', color: 'text-amber-700' },
          { label: '行为总次数', value: stats.behaviors, icon: '🏃', color: 'text-purple-600' },
          { label: '未读通知', value: stats.unread_notifications, icon: '🔔', color: 'text-red-500' },
        ]" :key="item.label" class="glass-card p-4">
          <span class="text-2xl">{{ item.icon }}</span>
          <p class="mt-2 text-2xl font-bold" :class="item.color">{{ item.value }}</p>
          <p class="text-sm text-surface-500">{{ item.label }}</p>
        </div>
      </section>

      <!-- Today's Overview -->
      <section v-if="todayTotal" class="glass-card p-5">
        <h2 class="text-lg font-bold text-surface-900 flex items-center gap-2">📊 今日概览</h2>
        <div class="mt-3 grid grid-cols-2 gap-3 sm:grid-cols-4">
          <div class="rounded-xl bg-blue-50 p-3 text-center">
            <p class="text-sm text-surface-500">今日喂食</p>
            <p class="text-2xl font-bold text-blue-600">{{ todayTotal.feedings }}</p>
          </div>
          <div class="rounded-xl bg-amber-50 p-3 text-center">
            <p class="text-sm text-surface-500">今日排便</p>
            <p class="text-2xl font-bold text-amber-600">{{ todayTotal.excretions }}</p>
          </div>
          <div class="rounded-xl bg-purple-50 p-3 text-center">
            <p class="text-sm text-surface-500">今日行为</p>
            <p class="text-2xl font-bold text-purple-600">{{ todayTotal.behaviors }}</p>
          </div>
          <div class="rounded-xl bg-green-50 p-3 text-center">
            <p class="text-sm text-surface-500">活动时长</p>
            <p class="text-2xl font-bold text-green-600">{{ todayTotal.duration }}<span class="text-sm font-normal">分钟</span></p>
          </div>
        </div>
        <!-- Per-pet breakdown -->
        <div v-if="stats.today_stats.length" class="mt-4 space-y-2">
          <p class="text-sm font-medium text-surface-500">按宠物明细</p>
          <div v-for="ts in stats.today_stats" :key="ts.pet_id" class="flex items-center gap-3 rounded-lg bg-surface-100 px-3 py-2 text-sm">
            <span class="font-semibold text-surface-700">{{ petName(ts.pet_id) }}</span>
            <span class="text-blue-600">喂{{ ts.feeding_count }}</span>
            <span class="text-surface-300">|</span>
            <span class="text-amber-600">便{{ ts.excretion_count }}</span>
            <span class="text-surface-300">|</span>
            <span class="text-purple-600">行{{ ts.behavior_count }}</span>
            <span class="text-surface-300">|</span>
            <span class="text-green-600">{{ ts.total_duration_minutes }}分</span>
          </div>
        </div>
      </section>
      <section v-else class="glass-card p-5 text-center text-surface-400">
        <p class="text-lg">📊 今日概览</p>
        <p class="text-sm mt-1">今天还没有记录数据，开始记录吧。</p>
      </section>

      <!-- Add Pet + Quick Check-in -->
      <section class="grid gap-6 lg:grid-cols-2">
        <div class="glass-card p-6"><h2 class="text-xl font-bold text-surface-900">添加宠物</h2><form class="mt-4 flex flex-col gap-3 sm:flex-row" @submit.prevent="addPet"><input v-model="newPetName" required placeholder="宠物名字" class="flex-1 rounded-xl border-surface-200" /><select v-model="newPetSpecies" class="rounded-xl border-surface-200"><option value="cat">猫</option><option value="dog">狗</option><option value="other">其他</option></select><button class="btn-primary" type="submit">添加</button></form><p v-if="selectedPet" class="mt-4 text-sm text-surface-500">当前正在记录：<strong>{{ selectedPet.name }}</strong></p></div>
        <div class="glass-card p-6"><h2 class="text-xl font-bold text-surface-900">快速打卡</h2><div class="mt-4 flex gap-2"><button v-for="tab in [['feeding','进食'], ['excretion','排便'], ['behavior','行为']] as const" :key="tab[0]" class="rounded-lg px-3 py-2 text-sm" :class="activeTab === tab[0] ? 'bg-primary-600 text-white' : 'bg-surface-100 text-surface-500'" @click="activeTab = tab[0]">{{ tab[1] }}</button></div><form v-if="activeTab === 'feeding'" class="mt-4 flex flex-col gap-3 sm:flex-row" @submit.prevent="quickFeed"><select v-model="foodType" required class="flex-1 rounded-xl border-surface-200"><option value="" disabled>选择食物类型</option><option v-for="opt in FOOD_TYPE_OPTIONS" :key="opt" :value="opt">{{ opt }}</option></select><input v-model.number="amount" type="number" min="0" placeholder="克数（可选）" class="w-36 rounded-xl border-surface-200"/><button :disabled="!selectedPetId" class="btn-primary">记录</button></form><button v-else :disabled="!selectedPetId" class="btn-primary mt-4" @click="quickRecord">一键记录{{ activeTab === 'excretion' ? '正常排便' : '日常行为' }}</button><p v-if="message" class="mt-3 text-sm text-green-700">{{ message }}</p></div>
      </section>
    </main>
  </div>
</template>
