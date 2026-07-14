<template>
  <div class="min-h-screen bg-surface-50 px-4 py-8 sm:px-6 lg:px-8">
    <div class="mx-auto max-w-5xl">
      <!-- Header -->
      <div class="mb-8 flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 class="text-2xl font-bold text-content-900 sm:text-3xl">统计报表</h1>
          <p class="mt-1 text-sm text-content-500">按时间段查看聚合数据并导出 CSV</p>
        </div>
        <div class="flex gap-3">
          <RouterLink to="/stats" class="rounded-lg bg-surface-100 px-4 py-2 text-sm font-medium text-content-600 transition-colors hover:bg-surface-200">
            趋势图表
          </RouterLink>
          <RouterLink to="/dashboard" class="rounded-lg bg-surface-100 px-4 py-2 text-sm font-medium text-content-600 transition-colors hover:bg-surface-200">
            控制面板
          </RouterLink>
        </div>
      </div>

      <!-- Filters -->
      <div class="glass-card mb-6 rounded-2xl p-5">
        <div class="flex flex-wrap items-end gap-4">
          <div class="min-w-0 flex-1">
            <label class="block text-sm font-medium text-content-700">宠物</label>
            <select v-model="filters.petId" class="mt-1 w-full rounded-lg border border-surface-200 bg-white px-3 py-2 text-sm text-content-900 focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500">
              <option value="">全部宠物</option>
              <option v-for="p in pets" :key="p.id" :value="p.id">{{ p.name }}</option>
            </select>
          </div>
          <div class="min-w-0 flex-1">
            <label class="block text-sm font-medium text-content-700">开始日期</label>
            <input v-model="filters.startDate" type="date" class="mt-1 w-full rounded-lg border border-surface-200 bg-white px-3 py-2 text-sm text-content-900 focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500" />
          </div>
          <div class="min-w-0 flex-1">
            <label class="block text-sm font-medium text-content-700">结束日期</label>
            <input v-model="filters.endDate" type="date" class="mt-1 w-full rounded-lg border border-surface-200 bg-white px-3 py-2 text-sm text-content-900 focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500" />
          </div>
          <div class="flex gap-2">
            <button @click="fetchReport" :disabled="loading" class="rounded-lg bg-primary-600 px-5 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-primary-700 disabled:opacity-50">
              {{ loading ? '加载中...' : '查询' }}
            </button>
            <a :href="csvUrl" class="rounded-lg bg-emerald-600 px-5 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-emerald-700 inline-flex items-center gap-1.5">
              <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              导出 CSV
            </a>
          </div>
        </div>
      </div>

      <!-- Loading -->
      <div v-if="loading" class="flex items-center justify-center py-20">
        <div class="h-8 w-8 animate-spin rounded-full border-3 border-primary-200 border-t-primary-600"></div>
        <span class="ml-3 text-sm text-content-500">正在加载报表...</span>
      </div>

      <!-- Error -->
      <div v-else-if="error" class="glass-card rounded-2xl p-8 text-center">
        <div class="mx-auto mb-3 flex h-14 w-14 items-center justify-center rounded-full bg-red-100">
          <svg class="h-7 w-7 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
          </svg>
        </div>
        <p class="text-content-600">{{ error }}</p>
        <button @click="fetchReport" class="mt-4 rounded-lg bg-primary-600 px-4 py-2 text-sm font-semibold text-white hover:bg-primary-700">重试</button>
      </div>

      <!-- Report Content -->
      <template v-else-if="report">
        <!-- Totals Card -->
        <div class="glass-card mb-6 rounded-2xl p-6">
          <h2 class="mb-4 text-lg font-semibold text-content-900">汇总概览</h2>
          <div class="grid grid-cols-2 gap-4 sm:grid-cols-4">
            <div class="rounded-xl bg-blue-50 p-4 text-center">
              <p class="text-2xl font-bold text-blue-600">{{ report.totals.feeding_count }}</p>
              <p class="mt-1 text-xs text-blue-500">喂食总次数</p>
            </div>
            <div class="rounded-xl bg-amber-50 p-4 text-center">
              <p class="text-2xl font-bold text-amber-600">{{ report.totals.excretion_count }}</p>
              <p class="mt-1 text-xs text-amber-500">排便总次数</p>
            </div>
            <div class="rounded-xl bg-purple-50 p-4 text-center">
              <p class="text-2xl font-bold text-purple-600">{{ report.totals.behavior_count }}</p>
              <p class="mt-1 text-xs text-purple-500">行为总次数</p>
            </div>
            <div class="rounded-xl bg-emerald-50 p-4 text-center">
              <p class="text-2xl font-bold text-emerald-600">{{ report.totals.total_duration_minutes }}</p>
              <p class="mt-1 text-xs text-emerald-500">行为总时长(min)</p>
            </div>
          </div>
          <p class="mt-4 text-center text-sm text-content-500">
            统计跨度：<span class="font-medium text-content-700">{{ report.days }} 天</span>
          </p>
        </div>

        <!-- Per-Pet Breakdown -->
        <div v-if="report.per_pet.length" class="glass-card rounded-2xl p-6">
          <h2 class="mb-4 text-lg font-semibold text-content-900">按宠物明细</h2>

          <!-- Desktop Table -->
          <div class="hidden overflow-x-auto sm:block">
            <table class="w-full text-sm">
              <thead>
                <tr class="border-b border-surface-200 text-left text-content-500">
                  <th class="pb-3 font-medium">宠物</th>
                  <th class="pb-3 font-medium">跟踪天数</th>
                  <th class="pb-3 font-medium">喂食</th>
                  <th class="pb-3 font-medium">排便</th>
                  <th class="pb-3 font-medium">行为</th>
                  <th class="pb-3 font-medium">时长(min)</th>
                  <th class="pb-3 font-medium">日均喂食</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="p in report.per_pet" :key="p.pet_id" class="border-b border-surface-100 transition-colors hover:bg-surface-50">
                  <td class="py-3 font-medium text-content-900">{{ p.pet_name }}</td>
                  <td class="py-3 text-content-600">{{ p.days_tracked }} 天</td>
                  <td class="py-3">
                    <span class="rounded-full bg-blue-100 px-2.5 py-0.5 text-xs font-semibold text-blue-700">{{ p.feeding_count }}</span>
                  </td>
                  <td class="py-3">
                    <span class="rounded-full bg-amber-100 px-2.5 py-0.5 text-xs font-semibold text-amber-700">{{ p.excretion_count }}</span>
                  </td>
                  <td class="py-3">
                    <span class="rounded-full bg-purple-100 px-2.5 py-0.5 text-xs font-semibold text-purple-700">{{ p.behavior_count }}</span>
                  </td>
                  <td class="py-3 text-content-600">{{ p.total_duration_minutes }}</td>
                  <td class="py-3 text-content-600">
                    {{ (p.feeding_count / Math.max(p.days_tracked, 1)).toFixed(1) }}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- Mobile Cards -->
          <div class="space-y-3 sm:hidden">
            <div v-for="p in report.per_pet" :key="p.pet_id" class="rounded-xl border border-surface-200 p-4">
              <div class="mb-3 flex items-center justify-between">
                <span class="font-semibold text-content-900">{{ p.pet_name }}</span>
                <span class="text-xs text-content-500">{{ p.days_tracked }} 天</span>
              </div>
              <div class="grid grid-cols-3 gap-2 text-center text-xs">
                <div class="rounded-lg bg-blue-50 py-2">
                  <p class="font-bold text-blue-600">{{ p.feeding_count }}</p>
                  <p class="text-blue-500">喂食</p>
                </div>
                <div class="rounded-lg bg-amber-50 py-2">
                  <p class="font-bold text-amber-600">{{ p.excretion_count }}</p>
                  <p class="text-amber-500">排便</p>
                </div>
                <div class="rounded-lg bg-purple-50 py-2">
                  <p class="font-bold text-purple-600">{{ p.behavior_count }}</p>
                  <p class="text-purple-500">行为</p>
                </div>
              </div>
              <div class="mt-2 flex justify-between text-xs text-content-500">
                <span>时长 {{ p.total_duration_minutes }}min</span>
                <span>日均 {{ (p.feeding_count / Math.max(p.days_tracked, 1)).toFixed(1) }} 次</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Empty per-pet -->
        <div v-else class="glass-card rounded-2xl p-8 text-center">
          <p class="text-content-500">所选范围内无宠物数据</p>
        </div>
      </template>

      <!-- Initial empty (no query yet) -->
      <div v-else class="glass-card rounded-2xl p-12 text-center">
        <div class="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-surface-100">
          <svg class="h-8 w-8 text-content-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
        </div>
        <h3 class="text-lg font-semibold text-content-700">选择日期范围开始查询</h3>
        <p class="mt-2 text-sm text-content-500">设置筛选条件后点击"查询"查看统计报表</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { RouterLink } from 'vue-router'
import api, { statsApi, type StatsReport } from '@/composables/api'

interface Pet {
  id: string
  name: string
}

const pets = ref<Pet[]>([])
const report = ref<StatsReport | null>(null)
const loading = ref(false)
const error = ref('')
const hasQueried = ref(false)

const today = new Date().toISOString().slice(0, 10)
const weekAgo = new Date(Date.now() - 7 * 86400000).toISOString().slice(0, 10)

const filters = reactive({
  petId: '',
  startDate: weekAgo,
  endDate: today,
})

const csvParams = computed(() => {
  const p: Record<string, string> = {}
  if (filters.petId) p.pet_id = filters.petId
  if (filters.startDate) p.start_date = filters.startDate
  if (filters.endDate) p.end_date = filters.endDate
  return p
})

const csvUrl = computed(() => statsApi.exportCsvUrl(csvParams.value))

onMounted(async () => {
  try {
    const { data } = await api.get<Pet[]>('/pets')
    pets.value = data
  } catch {
    // Pets aren't critical for the report page
  }
})

async function fetchReport() {
  loading.value = true
  error.value = ''
  hasQueried.value = true
  try {
    const { data } = await statsApi.report({
      pet_id: filters.petId || undefined,
      start_date: filters.startDate || undefined,
      end_date: filters.endDate || undefined,
    })
    report.value = data
  } catch (e: any) {
    error.value = e?.response?.data?.detail || e?.message || '加载报表失败'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.glass-card {
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(0, 0, 0, 0.06);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
}
.border-3 {
  border-width: 3px;
}
</style>
