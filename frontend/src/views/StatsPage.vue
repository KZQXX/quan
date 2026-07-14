<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { RouterLink } from 'vue-router'
import { use } from 'echarts/core'
import { BarChart, LineChart, PieChart } from 'echarts/charts'
import { GridComponent, LegendComponent, TitleComponent, TooltipComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import VChart from 'vue-echarts'
import { useAuthStore } from '@/stores/auth'
import api from '@/composables/api'

use([CanvasRenderer, LineChart, BarChart, PieChart, GridComponent, TooltipComponent, LegendComponent, TitleComponent])

interface Pet { id: string; name: string; species: string }
interface DailyStat { id: string; pet_id: string; date: string; feeding_count: number; excretion_count: number; behavior_count: number; total_duration_minutes: number }

const auth = useAuthStore()
const pets = ref<Pet[]>([])
const selectedPetId = ref('')
const rangeDays = ref(30)
const statsData = ref<DailyStat[]>([])
const loading = ref(false)
const error = ref('')

const petOptions = computed(() => pets.value.map((p) => ({ value: p.id, label: `${p.name} · ${p.species}` })))

async function loadPets() {
  const { data } = await api.get('/pets')
  pets.value = data
  if (!selectedPetId.value && pets.value.length) selectedPetId.value = pets.value[0].id
}

async function loadStats() {
  loading.value = true
  error.value = ''
  try {
    const today = new Date()
    const end = today.toISOString().slice(0, 10)
    const start = new Date(today.getTime() - (rangeDays.value - 1) * 86400000).toISOString().slice(0, 10)
    const params: Record<string, string> = { start_date: start, end_date: end }
    if (selectedPetId.value) params.pet_id = selectedPetId.value
    const { data } = await api.get('/stats/daily', { params })
    statsData.value = data
  } catch {
    error.value = '加载统计数据失败，请稍后重试。'
  } finally {
    loading.value = false
  }
}

// Trend chart (7/30 day feeding & excretion line chart)
const trendOption = computed(() => {
  const data = statsData.value.slice().sort((a, b) => a.date.localeCompare(b.date))
  const dates = data.map((d) => d.date.slice(5)) // MM-DD
  const feeding = data.map((d) => d.feeding_count)
  const excretion = data.map((d) => d.excretion_count)
  const behavior = data.map((d) => d.behavior_count)
  return {
    tooltip: { trigger: 'axis' },
    legend: { data: ['喂食', '排便', '行为'], bottom: 0 },
    grid: { left: 40, right: 20, top: 20, bottom: 40 },
    xAxis: { type: 'category', data: dates, axisLabel: { rotate: dates.length > 14 ? 45 : 0, fontSize: 11 } },
    yAxis: { type: 'value', minInterval: 1 },
    series: [
      { name: '喂食', type: 'line', data: feeding, smooth: true, color: '#2563eb', symbol: 'circle', symbolSize: 4 },
      { name: '排便', type: 'line', data: excretion, smooth: true, color: '#d97706', symbol: 'circle', symbolSize: 4 },
      { name: '行为', type: 'line', data: behavior, smooth: true, color: '#7c3aed', symbol: 'circle', symbolSize: 4 },
    ],
  }
})

// Behavior bar chart
const behaviorOption = computed(() => {
  const data = statsData.value.slice().sort((a, b) => a.date.localeCompare(b.date))
  const dates = data.map((d) => d.date.slice(5))
  const behavior = data.map((d) => d.behavior_count)
  return {
    tooltip: { trigger: 'axis' },
    grid: { left: 40, right: 20, top: 20, bottom: 40 },
    xAxis: { type: 'category', data: dates, axisLabel: { rotate: dates.length > 14 ? 45 : 0, fontSize: 11 } },
    yAxis: { type: 'value', minInterval: 1 },
    series: [{ name: '行为次数', type: 'bar', data: behavior, color: '#7c3aed', barMaxWidth: 20 }],
  }
})

// Duration line chart
const durationOption = computed(() => {
  const data = statsData.value.slice().sort((a, b) => a.date.localeCompare(b.date))
  const dates = data.map((d) => d.date.slice(5))
  const durations = data.map((d) => d.total_duration_minutes)
  return {
    tooltip: { trigger: 'axis', valueFormatter: (v: number) => `${v} 分钟` },
    grid: { left: 40, right: 20, top: 20, bottom: 40 },
    xAxis: { type: 'category', data: dates, axisLabel: { rotate: dates.length > 14 ? 45 : 0, fontSize: 11 } },
    yAxis: { type: 'value', minInterval: 1 },
    series: [{ name: '活动时长', type: 'line', data: durations, smooth: true, areaStyle: { opacity: 0.15, color: '#16a34a' }, color: '#16a34a', symbol: 'circle', symbolSize: 4 }],
  }
})

// Pie chart for today's type distribution
const pieOption = computed(() => {
  const totalFeeding = statsData.value.reduce((a, x) => a + x.feeding_count, 0)
  const totalExcretion = statsData.value.reduce((a, x) => a + x.excretion_count, 0)
  const totalBehavior = statsData.value.reduce((a, x) => a + x.behavior_count, 0)
  return {
    tooltip: { trigger: 'item' },
    legend: { bottom: 0 },
    series: [{
      name: '统计',
      type: 'pie',
      radius: ['45%', '75%'],
      avoidLabelOverlap: false,
      itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 2 },
      label: { show: false },
      emphasis: { label: { show: true, fontSize: 16, fontWeight: 'bold' } },
      data: [
        { value: totalFeeding, name: '喂食', itemStyle: { color: '#2563eb' } },
        { value: totalExcretion, name: '排便', itemStyle: { color: '#d97706' } },
        { value: totalBehavior, name: '行为', itemStyle: { color: '#7c3aed' } },
      ],
    }],
  }
})

onMounted(async () => {
  await loadPets()
  await loadStats()
})

watch([selectedPetId, rangeDays], () => loadStats())
</script>

<template>
  <div class="min-h-[100dvh] bg-surface-50">
    <header class="bg-white/80 backdrop-blur-xl border-b border-surface-200 sticky top-0 z-40">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <RouterLink to="/" class="flex items-center gap-2"><span class="text-2xl">🐾</span><span class="text-lg font-bold text-primary-600">Pet Tracker</span></RouterLink>
        <div class="flex items-center gap-4 text-sm text-surface-500">
          <RouterLink to="/dashboard" class="hover:text-primary-600 transition-colors">控制面板</RouterLink>
          <RouterLink to="/records" class="hover:text-primary-600 transition-colors">记录中心</RouterLink>
          <RouterLink to="/reminders" class="hover:text-primary-600 transition-colors">提醒</RouterLink>
          <span>{{ auth.user?.display_name || auth.user?.email }}</span>
          <button class="btn-ghost !px-3 !py-2" @click="auth.logout()">退出</button>
        </div>
      </div>
    </header>

    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      <section class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 class="text-3xl font-extrabold text-surface-900">数据统计</h1>
          <p class="mt-1 text-surface-500">趋势变化与行为分析。</p>
        </div>
        <div class="flex items-center gap-3">
          <select v-model="selectedPetId" class="rounded-xl border-surface-200 bg-white text-sm" :disabled="!pets.length">
            <option value="">全部宠物</option>
            <option v-for="opt in petOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
          </select>
          <select v-model="rangeDays" class="rounded-xl border-surface-200 bg-white text-sm">
            <option :value="7">最近 7 天</option>
            <option :value="30">最近 30 天</option>
          </select>
        </div>
      </section>

      <!-- Loading / Error -->
      <section v-if="loading" class="glass-card p-12 text-center text-surface-400">
        <p class="text-lg">⏳ 加载中...</p>
      </section>
      <section v-else-if="error" class="glass-card p-12 text-center text-red-500">
        <p>{{ error }}</p>
        <button class="btn-primary mt-4" @click="loadStats">重试</button>
      </section>

      <template v-else>
        <!-- Trend Line Chart -->
        <section class="glass-card p-5">
          <h2 class="text-lg font-bold text-surface-900 mb-1">📈 {{ rangeDays }}天趋势</h2>
          <VChart v-if="statsData.length" :option="trendOption" style="height:350px" autoresize />
          <p v-else class="py-12 text-center text-surface-400">暂无数据。</p>
        </section>

        <!-- Charts Row -->
        <section class="grid gap-6 lg:grid-cols-2">
          <!-- Pie: Type Distribution -->
          <div class="glass-card p-5">
            <h2 class="text-lg font-bold text-surface-900 mb-1">🍩 类型分布</h2>
            <VChart v-if="statsData.length" :option="pieOption" style="height:300px" autoresize />
            <p v-else class="py-12 text-center text-surface-400">暂无数据。</p>
          </div>

          <!-- Bar: Behavior Daily -->
          <div class="glass-card p-5">
            <h2 class="text-lg font-bold text-surface-900 mb-1">📊 行为每日统计</h2>
            <VChart v-if="statsData.length" :option="behaviorOption" style="height:300px" autoresize />
            <p v-else class="py-12 text-center text-surface-400">暂无数据。</p>
          </div>
        </section>

        <!-- Duration Trend -->
        <section class="glass-card p-5">
          <h2 class="text-lg font-bold text-surface-900 mb-1">⏱️ 活动时长趋势</h2>
          <VChart v-if="statsData.length" :option="durationOption" style="height:300px" autoresize />
          <p v-else class="py-12 text-center text-surface-400">暂无数据。</p>
        </section>
      </template>
    </main>
  </div>
</template>
