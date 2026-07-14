<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { RouterLink } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import api from '@/composables/api'

// ── Types ───────────────────────────────────────────────────────────────────
interface Pet { id: string; name: string; species: string; breed?: string }

interface RecordItem {
  id: string
  pet_id: string
  recorded_at: string
  notes: string | null
  source: string
}

interface FeedingRecord extends RecordItem {
  food_type: string
  amount: number | null
}

interface ExcretionRecord extends RecordItem {
  type: string
  consistency: string | null
}

interface BehaviorRecord extends RecordItem {
  behavior_type: string
  duration_minutes: number | null
  mood: string | null
}

type RecordType = FeedingRecord | ExcretionRecord | BehaviorRecord
type TabKey = 'feeding' | 'excretion' | 'behavior'

const TAB_LABELS: Record<TabKey, string> = { feeding: '进食', excretion: '排便', behavior: '行为' }
const TAB_ENDPOINTS: Record<TabKey, string> = { feeding: 'feedings', excretion: 'excretions', behavior: 'behaviors' }
const FOOD_TYPE_OPTIONS = ['狗粮', '猫粮', '零食', '自制', '罐头', '生骨肉', '冻干', '处方粮', '其他']
const EXCRETION_TYPE_OPTIONS = ['正常', '腹泻', '便秘', '带血', '其他']
const CONSISTENCY_OPTIONS = ['正常', '软便', '硬便', '水样']
const BEHAVIOR_TYPE_OPTIONS = ['玩耍', '睡觉', '散步', '吠叫', '训练', '抓挠', '梳毛', '其他']
const MOOD_OPTIONS = ['开心', '平静', '焦虑', '萎靡']

// ── State ───────────────────────────────────────────────────────────────────
const auth = useAuthStore()
const pets = ref<Pet[]>([])
const selectedPetId = ref('')
const activeTab = ref<TabKey>('feeding')
const startDate = ref('')
const endDate = ref('')
const records = ref<RecordType[]>([])
const loading = ref(false)
const error = ref('')
const message = ref('')

// Create form state — feeding
const newFoodType = ref('狗粮')
const newAmount = ref<number | null>(null)
const newNotes = ref('')
const creating = ref(false)

// Create form state — excretion
const newExcretionType = ref('正常')
const newConsistency = ref('')
const newExcretionNotes = ref('')

// Create form state — behavior
const newBehaviorType = ref('玩耍')
const newDurationMinutes = ref<number | null>(null)
const newMood = ref('')
const newBehaviorNotes = ref('')

// Edit modal
const editing = ref<RecordType | null>(null)
const editForm = ref<Record<string, any>>({})

// Delete confirmation
const deleting = ref<RecordType | null>(null)

const hasRecords = computed(() => records.value.length > 0)
const currentEndpoint = computed(() => TAB_ENDPOINTS[activeTab.value])

const selectedPet = computed(() => pets.value.find((p) => p.id === selectedPetId.value))

// ── Form validation ─────────────────────────────────────────────────────────
const formErrors = ref<Record<string, string>>({})

function clearFormErrors() { formErrors.value = {} }

function validateFeeding(): boolean {
  const errs: Record<string, string> = {}
  if (!newFoodType.value) errs.food_type = '请选择食物类型'
  if (newAmount.value !== null && (newAmount.value <= 0 || !Number.isFinite(newAmount.value)))
    errs.amount = '食量必须大于 0'
  if (newAmount.value !== null && newAmount.value > 99999) errs.amount = '食量不能超过 99999g'
  formErrors.value = errs
  return Object.keys(errs).length === 0
}

function validateExcretion(): boolean {
  formErrors.value = {}
  return true
}

function validateBehavior(): boolean {
  const errs: Record<string, string> = {}
  if (newDurationMinutes.value !== null && (newDurationMinutes.value <= 0 || !Number.isFinite(newDurationMinutes.value)))
    errs.duration = '时长必须大于 0'
  if (newDurationMinutes.value !== null && newDurationMinutes.value > 1440) errs.duration = '时长不能超过 1440 分钟'
  formErrors.value = errs
  return Object.keys(errs).length === 0
}

// ── Card helpers ────────────────────────────────────────────────────────────
function recordIcon(r: RecordType): string {
  if (activeTab.value === 'feeding') {
    const m: Record<string, string> = { '狗粮': '🦴', '猫粮': '🐟', '零食': '🍪', '自制': '🍲', '罐头': '🥫', '生骨肉': '🥩', '冻干': '🧊', '处方粮': '💊', '其他': '🍽️' }
    return m[(r as FeedingRecord).food_type] || '🍽️'
  }
  if (activeTab.value === 'excretion') {
    const m: Record<string, string> = { '正常': '✅', '腹泻': '💧', '便秘': '🪨', '带血': '🩸', '其他': '💩' }
    return m[(r as ExcretionRecord).type] || '💩'
  }
  const m: Record<string, string> = { '玩耍': '🎾', '睡觉': '😴', '散步': '🚶', '吠叫': '🗣️', '训练': '🎓', '抓挠': '✋', '梳毛': '🪮', '其他': '🐕' }
  return m[(r as BehaviorRecord).behavior_type] || '🐕'
}

function sourceBadge(source: string): string {
  return source === 'quick_checkin' ? '⚡ 快速打卡' : '✏️ 手动记录'
}

const todayRecords = computed(() => {
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const tomorrow = new Date(today)
  tomorrow.setDate(tomorrow.getDate() + 1)
  return records.value.filter((r) => {
    const d = new Date(r.recorded_at)
    return d >= today && d < tomorrow
  })
})

// ── API helpers ─────────────────────────────────────────────────────────────
function params() {
  const p: Record<string, string> = {}
  if (startDate.value) p.start_date = new Date(`${startDate.value}T00:00:00`).toISOString()
  if (endDate.value) p.end_date = new Date(`${endDate.value}T23:59:59.999`).toISOString()
  return p
}

async function refresh() {
  const [petRes] = await Promise.all([api.get('/pets')])
  pets.value = petRes.data
  if (!selectedPetId.value && pets.value.length) selectedPetId.value = pets.value[0].id
}

async function loadRecords() {
  if (!selectedPetId.value) return
  loading.value = true
  error.value = ''
  try {
    const { data } = await api.get(`/pets/${selectedPetId.value}/${currentEndpoint.value}`, { params: params() })
    records.value = data
  } catch (e: any) {
    error.value = e.response?.data?.detail || '加载失败，请重试。'
  } finally {
    loading.value = false
  }
}

// ── Create feeding record ────────────────────────────────────────────────
async function createFeedingRecord(source: 'manual' | 'quick_checkin' = 'manual') {
  if (!selectedPetId.value) return
  if (!validateFeeding()) return
  creating.value = true
  error.value = ''
  clearFormErrors()
  try {
    await api.post(`/pets/${selectedPetId.value}/feedings`, {
      food_type: newFoodType.value,
      amount: newAmount.value,
      notes: newNotes.value || undefined,
      source,
    })
    message.value = '已记录一餐！'
    newAmount.value = null
    newNotes.value = ''
    await loadRecords()
  } catch (e: any) {
    error.value = e.response?.data?.detail || '记录失败，请重试。'
  } finally {
    creating.value = false
  }
}

function quickFeedCheckin() {
  if (!selectedPet.value) return
  const species = selectedPet.value.species
  if (species === 'dog') newFoodType.value = '狗粮'
  else if (species === 'cat') newFoodType.value = '猫粮'
  else newFoodType.value = '零食'
  newAmount.value = 100
  newNotes.value = ''
  createFeedingRecord('quick_checkin')
}

// ── Create excretion record ────────────────────────────────────────────────
async function createExcretionRecord(source: 'manual' | 'quick_checkin' = 'manual') {
  if (!selectedPetId.value) return
  if (!validateExcretion()) return
  creating.value = true
  error.value = ''
  clearFormErrors()
  try {
    await api.post(`/pets/${selectedPetId.value}/excretions`, {
      type: newExcretionType.value,
      consistency: newConsistency.value || undefined,
      notes: newExcretionNotes.value || undefined,
      source,
    })
    message.value = '已记录排便！'
    newConsistency.value = ''
    newExcretionNotes.value = ''
    await loadRecords()
  } catch (e: any) {
    error.value = e.response?.data?.detail || '记录失败，请重试。'
  } finally {
    creating.value = false
  }
}

function quickExcretionCheckin() {
  newExcretionType.value = '正常'
  newConsistency.value = ''
  newExcretionNotes.value = ''
  createExcretionRecord('quick_checkin')
}

// ── Create behavior record ────────────────────────────────────────────────
async function createBehaviorRecord(source: 'manual' | 'quick_checkin' = 'manual') {
  if (!selectedPetId.value) return
  if (!validateBehavior()) return
  creating.value = true
  error.value = ''
  clearFormErrors()
  try {
    await api.post(`/pets/${selectedPetId.value}/behaviors`, {
      behavior_type: newBehaviorType.value,
      duration_minutes: newDurationMinutes.value,
      mood: newMood.value || undefined,
      notes: newBehaviorNotes.value || undefined,
      source,
    })
    message.value = '已记录行为！'
    newDurationMinutes.value = null
    newMood.value = ''
    newBehaviorNotes.value = ''
    await loadRecords()
  } catch (e: any) {
    error.value = e.response?.data?.detail || '记录失败，请重试。'
  } finally {
    creating.value = false
  }
}

function quickBehaviorCheckin() {
  newBehaviorType.value = '玩耍'
  newDurationMinutes.value = null
  newMood.value = '开心'
  newBehaviorNotes.value = ''
  createBehaviorRecord('quick_checkin')
}

// ── Actions ─────────────────────────────────────────────────────────────────
function openEdit(record: RecordType) {
  editing.value = { ...record }
  editForm.value = { ...record }
}

function cancelEdit() {
  editing.value = null
  editForm.value = {}
}

async function saveEdit() {
  if (!editing.value || !selectedPetId.value) return
  const ep = currentEndpoint.value
  const id = editing.value.id
  const body: Record<string, any> = {}
  for (const [k, v] of Object.entries(editForm.value)) {
    if (['id', 'pet_id', 'source'].includes(k)) continue
    if (v !== editing.value[k as keyof RecordType] && v !== '') {
      body[k] = k === 'recorded_at' ? new Date(String(v)).toISOString() : v === '' ? null : v
    }
  }
  try {
    await api.patch(`/pets/${selectedPetId.value}/${ep}/${id}`, body)
    message.value = '已更新。'
    editing.value = null
    await loadRecords()
  } catch (e: any) {
    error.value = e.response?.data?.detail || '更新失败。'
  }
}

function confirmDelete(record: RecordType) {
  deleting.value = record
}

async function executeDelete() {
  if (!deleting.value || !selectedPetId.value) return
  const ep = currentEndpoint.value
  const id = deleting.value.id
  try {
    await api.delete(`/pets/${selectedPetId.value}/${ep}/${id}`)
    message.value = '已删除。'
    deleting.value = null
    await loadRecords()
  } catch (e: any) {
    error.value = e.response?.data?.detail || '删除失败。'
  }
}

async function copyRecord(record: RecordType) {
  if (!selectedPetId.value) return
  const ep = currentEndpoint.value
  const body: Record<string, any> = {}
  for (const [k, v] of Object.entries(record)) {
    if (['id', 'pet_id', 'recorded_at', 'source'].includes(k)) continue
    if (v !== null && v !== '') body[k] = v
  }
  try {
    await api.post(`/pets/${selectedPetId.value}/${ep}`, body)
    message.value = '已复制记录！'
    await loadRecords()
  } catch (e: any) {
    error.value = e.response?.data?.detail || '复制失败。'
  }
}

// ── Helpers ─────────────────────────────────────────────────────────────────
function formatTime(iso: string) {
  return new Date(iso).toLocaleString('zh-CN', {
    month: 'numeric', day: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}

function feedingDetail(r: FeedingRecord) {
  const parts = [r.food_type]
  if (r.amount != null) parts.push(`${r.amount}g`)
  return parts.join(' · ')
}

function excretionDetail(r: ExcretionRecord) {
  const parts = [r.type]
  if (r.consistency) parts.push(r.consistency)
  return parts.join(' · ')
}

function behaviorDetail(r: BehaviorRecord) {
  const parts = [r.behavior_type]
  if (r.duration_minutes != null) parts.push(`${r.duration_minutes} 分钟`)
  if (r.mood) parts.push(r.mood)
  return parts.join(' · ')
}

// ── Lifecycle ───────────────────────────────────────────────────────────────
onMounted(async () => {
  await refresh()
  await loadRecords()
})

watch([selectedPetId, activeTab, startDate, endDate], () => {
  loadRecords()
})
</script>

<template>
  <div class="min-h-[100dvh] bg-surface-50">
    <!-- Header -->
    <header class="bg-white/80 backdrop-blur-xl border-b border-surface-200 sticky top-0 z-40">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <RouterLink to="/" class="flex items-center gap-2">
          <span class="text-2xl">🐾</span>
          <span class="text-lg font-bold text-primary-600">Pet Tracker</span>
        </RouterLink>
        <div class="flex items-center gap-4 text-sm text-surface-500">
          <RouterLink to="/dashboard" class="hover:text-primary-600 transition-colors">控制面板</RouterLink>
          <RouterLink to="/reminders" class="hover:text-primary-600 transition-colors">提醒</RouterLink>
          <span>{{ auth.user?.display_name || auth.user?.email }}</span>
          <button class="btn-ghost !px-3 !py-2" @click="auth.logout()">退出</button>
        </div>
      </div>
    </header>

    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      <!-- Title + Pet selector -->
      <section class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 class="text-3xl font-extrabold text-surface-900">记录中心</h1>
          <p class="mt-1 text-surface-500">查看与管理宠物日常记录。</p>
        </div>
        <select
          v-model="selectedPetId"
          class="rounded-xl border-surface-200 bg-white"
          :disabled="!pets.length"
        >
          <option v-for="pet in pets" :key="pet.id" :value="pet.id">
            {{ pet.name }} · {{ pet.species }}
          </option>
          <option v-if="!pets.length" value="">先添加一只宠物</option>
        </select>
      </section>

      <!-- Tabs -->
      <nav class="flex gap-2 border-b border-surface-200 pb-1">
        <button
          v-for="(label, key) in TAB_LABELS"
          :key="key"
          class="rounded-t-lg px-5 py-2.5 text-sm font-medium transition-colors"
          :class="activeTab === key
            ? 'bg-primary-600 text-white shadow-sm'
            : 'bg-surface-100 text-surface-500 hover:text-surface-700'"
          @click="activeTab = key as TabKey"
        >
          {{ label }}
        </button>
      </nav>

      <!-- ── Create Feeding Form (D15) ────────────────────────────────────── -->
      <section v-if="activeTab === 'feeding' && selectedPetId" class="glass-card p-6 space-y-4">
        <h2 class="text-xl font-bold text-surface-900 flex items-center gap-2">
          <span>🍽️</span> 记录喂食
        </h2>
        <form class="flex flex-wrap gap-3 items-end" @submit.prevent="createFeedingRecord()">
          <label class="flex flex-col gap-1 text-xs text-surface-500 min-w-[120px]">
            食物类型
            <select v-model="newFoodType" class="rounded-xl border-surface-200 text-sm" :class="{ '!border-red-400': formErrors.food_type }" @change="clearFormErrors">
              <option v-for="opt in FOOD_TYPE_OPTIONS" :key="opt" :value="opt">{{ opt }}</option>
            </select>
            <span v-if="formErrors.food_type" class="text-red-500 text-[11px]">{{ formErrors.food_type }}</span>
          </label>
          <label class="flex flex-col gap-1 text-xs text-surface-500 w-28">
            食量 (g)
            <input
              v-model.number="newAmount"
              type="number"
              min="0"
              placeholder="克数"
              class="rounded-xl border-surface-200 text-sm"
              :class="{ '!border-red-400': formErrors.amount }"
              @input="clearFormErrors"
            />
            <span v-if="formErrors.amount" class="text-red-500 text-[11px]">{{ formErrors.amount }}</span>
          </label>
          <label class="flex flex-col gap-1 text-xs text-surface-500 flex-1 min-w-[150px]">
            备注
            <input v-model="newNotes" placeholder="可选" class="rounded-xl border-surface-200 text-sm" />
          </label>
          <button
            type="submit"
            class="btn-primary text-sm"
            :disabled="creating || !selectedPetId"
          >
            <span v-if="creating" class="animate-pulse">记录中…</span>
            <span v-else>✅ 记录</span>
          </button>
          <button
            type="button"
            class="rounded-xl px-4 py-2 text-sm font-medium bg-amber-500 text-white hover:bg-amber-600 transition-colors disabled:opacity-50"
            :disabled="creating || !selectedPetId"
            @click="quickFeedCheckin"
          >
            ⚡ 快速打卡
          </button>
        </form>
      </section>

      <!-- ── Create Excretion Form ────────────────────────────────────────── -->
      <section v-if="activeTab === 'excretion' && selectedPetId" class="glass-card p-6 space-y-4">
        <h2 class="text-xl font-bold text-surface-900 flex items-center gap-2">
          <span>💩</span> 记录排便
        </h2>
        <form class="flex flex-wrap gap-3 items-end" @submit.prevent="createExcretionRecord()">
          <label class="flex flex-col gap-1 text-xs text-surface-500 min-w-[120px]">
            类型
            <select v-model="newExcretionType" class="rounded-xl border-surface-200 text-sm">
              <option v-for="opt in EXCRETION_TYPE_OPTIONS" :key="opt" :value="opt">{{ opt }}</option>
            </select>
          </label>
          <label class="flex flex-col gap-1 text-xs text-surface-500 min-w-[120px]">
            性状
            <select v-model="newConsistency" class="rounded-xl border-surface-200 text-sm">
              <option value="">不指定</option>
              <option v-for="opt in CONSISTENCY_OPTIONS" :key="opt" :value="opt">{{ opt }}</option>
            </select>
          </label>
          <label class="flex flex-col gap-1 text-xs text-surface-500 flex-1 min-w-[150px]">
            备注
            <input v-model="newExcretionNotes" placeholder="可选" class="rounded-xl border-surface-200 text-sm" />
          </label>
          <button
            type="submit"
            class="btn-primary text-sm"
            :disabled="creating || !selectedPetId"
          >
            <span v-if="creating" class="animate-pulse">记录中…</span>
            <span v-else>✅ 记录</span>
          </button>
          <button
            type="button"
            class="rounded-xl px-4 py-2 text-sm font-medium bg-amber-500 text-white hover:bg-amber-600 transition-colors disabled:opacity-50"
            :disabled="creating || !selectedPetId"
            @click="quickExcretionCheckin"
          >
            ⚡ 快速打卡
          </button>
        </form>
      </section>

      <!-- ── Create Behavior Form ─────────────────────────────────────────── -->
      <section v-if="activeTab === 'behavior' && selectedPetId" class="glass-card p-6 space-y-4">
        <h2 class="text-xl font-bold text-surface-900 flex items-center gap-2">
          <span>🐕</span> 记录行为
        </h2>
        <form class="flex flex-wrap gap-3 items-end" @submit.prevent="createBehaviorRecord()">
          <label class="flex flex-col gap-1 text-xs text-surface-500 min-w-[120px]">
            行为类型
            <select v-model="newBehaviorType" class="rounded-xl border-surface-200 text-sm">
              <option v-for="opt in BEHAVIOR_TYPE_OPTIONS" :key="opt" :value="opt">{{ opt }}</option>
            </select>
          </label>
          <label class="flex flex-col gap-1 text-xs text-surface-500 w-28">
            时长 (分钟)
            <input
              v-model.number="newDurationMinutes"
              type="number"
              min="0"
              placeholder="分钟数"
              class="rounded-xl border-surface-200 text-sm"
              :class="{ '!border-red-400': formErrors.duration }"
              @input="clearFormErrors"
            />
            <span v-if="formErrors.duration" class="text-red-500 text-[11px]">{{ formErrors.duration }}</span>
          </label>
          <label class="flex flex-col gap-1 text-xs text-surface-500 min-w-[100px]">
            情绪
            <select v-model="newMood" class="rounded-xl border-surface-200 text-sm">
              <option value="">不指定</option>
              <option v-for="opt in MOOD_OPTIONS" :key="opt" :value="opt">{{ opt }}</option>
            </select>
          </label>
          <label class="flex flex-col gap-1 text-xs text-surface-500 flex-1 min-w-[150px]">
            备注
            <input v-model="newBehaviorNotes" placeholder="可选" class="rounded-xl border-surface-200 text-sm" />
          </label>
          <button
            type="submit"
            class="btn-primary text-sm"
            :disabled="creating || !selectedPetId"
          >
            <span v-if="creating" class="animate-pulse">记录中…</span>
            <span v-else>✅ 记录</span>
          </button>
          <button
            type="button"
            class="rounded-xl px-4 py-2 text-sm font-medium bg-amber-500 text-white hover:bg-amber-600 transition-colors disabled:opacity-50"
            :disabled="creating || !selectedPetId"
            @click="quickBehaviorCheckin"
          >
            ⚡ 快速打卡
          </button>
        </form>
      </section>

      <!-- Date filters -->
      <div class="flex flex-wrap gap-3 items-end">
        <label class="flex flex-col gap-1 text-xs text-surface-500">
          起始日期
          <input v-model="startDate" type="date" class="rounded-xl border-surface-200 text-sm" />
        </label>
        <label class="flex flex-col gap-1 text-xs text-surface-500">
          结束日期
          <input v-model="endDate" type="date" class="rounded-xl border-surface-200 text-sm" />
        </label>
        <button
          v-if="startDate || endDate"
          class="btn-ghost text-sm !py-2"
          @click="startDate = ''; endDate = ''"
        >
          清除筛选
        </button>
      </div>

      <!-- Message -->
      <p v-if="message" class="text-sm text-green-700 bg-green-50 rounded-xl px-4 py-2">{{ message }}</p>
      <p v-if="error" class="text-sm text-red-700 bg-red-50 rounded-xl px-4 py-2">{{ error }}</p>

      <!-- Loading -->
      <div v-if="loading" class="text-center py-16 text-surface-400">
        <span class="animate-pulse text-4xl">⏳</span>
        <p class="mt-3">加载记录中…</p>
      </div>

      <!-- Empty state with illustration -->
      <div v-else-if="!hasRecords && selectedPetId" class="py-16">
        <div class="max-w-sm mx-auto text-center space-y-5">
          <!-- Inline SVG illustration per tab -->
          <div class="mx-auto w-40 h-40 flex items-center justify-center">
            <!-- Feeding empty -->
            <svg v-if="activeTab === 'feeding'" viewBox="0 0 160 160" class="w-full h-full">
              <defs>
                <linearGradient id="bowlGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" style="stop-color: #3b82f6; stop-opacity:0.15"/>
                  <stop offset="100%" style="stop-color: #6366f1; stop-opacity:0.08"/>
                </linearGradient>
              </defs>
              <circle cx="80" cy="75" r="55" fill="url(#bowlGrad)" stroke="#93c5fd" stroke-width="2" stroke-dasharray="8,4"/>
              <ellipse cx="80" cy="72" rx="38" ry="18" fill="#dbeafe" stroke="#93c5fd" stroke-width="2"/>
              <circle cx="65" cy="65" r="4" fill="#f59e0b"/>
              <circle cx="80" cy="60" r="3" fill="#f59e0b"/>
              <circle cx="92" cy="63" r="3.5" fill="#f59e0b"/>
              <circle cx="75" cy="70" r="2.5" fill="#f59e0b"/>
              <text x="80" y="135" text-anchor="middle" font-size="11" fill="#94a3b8">碗是空的…</text>
            </svg>
            <!-- Excretion empty -->
            <svg v-else-if="activeTab === 'excretion'" viewBox="0 0 160 160" class="w-full h-full">
              <defs>
                <linearGradient id="excreteGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" style="stop-color: #f59e0b; stop-opacity:0.15"/>
                  <stop offset="100%" style="stop-color: #f97316; stop-opacity:0.08"/>
                </linearGradient>
              </defs>
              <circle cx="80" cy="75" r="55" fill="url(#excreteGrad)" stroke="#fbbf24" stroke-width="2" stroke-dasharray="8,4"/>
              <circle cx="80" cy="70" r="15" fill="#fef3c7" stroke="#f59e0b" stroke-width="2.5"/>
              <circle cx="74" cy="67" r="3" fill="#f59e0b"/>
              <circle cx="86" cy="67" r="3" fill="#f59e0b"/>
              <ellipse cx="80" cy="74" rx="5" ry="2.5" fill="#d97706"/>
              <text x="80" y="135" text-anchor="middle" font-size="11" fill="#94a3b8">还没记录过…</text>
            </svg>
            <!-- Behavior empty -->
            <svg v-else viewBox="0 0 160 160" class="w-full h-full">
              <defs>
                <linearGradient id="behaveGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" style="stop-color: #a855f7; stop-opacity:0.15"/>
                  <stop offset="100%" style="stop-color: #ec4899; stop-opacity:0.08"/>
                </linearGradient>
              </defs>
              <circle cx="80" cy="75" r="55" fill="url(#behaveGrad)" stroke="#c084fc" stroke-width="2" stroke-dasharray="8,4"/>
              <circle cx="80" cy="72" r="20" fill="#f3e8ff" stroke="#a855f7" stroke-width="2"/>
              <text x="80" y="68" text-anchor="middle" font-size="28" fill="#a855f7">🐕</text>
              <text x="80" y="135" text-anchor="middle" font-size="11" fill="#94a3b8">什么也没做…</text>
            </svg>
          </div>
          <div>
            <p class="text-lg font-bold text-surface-700">暂无{{ TAB_LABELS[activeTab] }}记录</p>
            <p class="text-sm text-surface-400 mt-1">让每一天都被好好记录。</p>
          </div>
          <!-- Step guide -->
          <div class="flex items-center justify-center gap-2 text-xs text-surface-400 pt-2">
            <span class="bg-surface-100 rounded-full w-5 h-5 flex items-center justify-center font-bold text-surface-500">1</span>
            <span>选择宠物</span>
            <span class="text-surface-300">→</span>
            <span class="bg-surface-100 rounded-full w-5 h-5 flex items-center justify-center font-bold text-surface-500">2</span>
            <span>选日期范围</span>
            <span class="text-surface-300">→</span>
            <span class="bg-surface-100 rounded-full w-5 h-5 flex items-center justify-center font-bold text-surface-500">3</span>
            <span>填上方表单</span>
          </div>
        </div>
      </div>

      <!-- ── Today's Records (all tabs) ──────────────────────────────────── -->
      <section
        v-if="todayRecords.length && selectedPetId"
        class="space-y-3"
      >
        <div class="flex items-center gap-3">
          <h3 class="text-lg font-bold text-surface-900">
            📅 今日{{ TAB_LABELS[activeTab] }}
          </h3>
          <span
            class="text-sm rounded-full px-3 py-0.5 font-medium"
            :class="activeTab === 'feeding'
              ? 'bg-primary-100 text-primary-700'
              : activeTab === 'excretion'
                ? 'bg-amber-100 text-amber-700'
                : 'bg-purple-100 text-purple-700'"
          >
            {{ todayRecords.length }} {{ activeTab === 'feeding' ? '餐' : activeTab === 'excretion' ? '次' : '条' }}
          </span>
        </div>
        <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <article
            v-for="record in todayRecords"
            :key="record.id"
            class="glass-card p-5 group relative border-l-4"
            :class="activeTab === 'feeding' ? 'border-l-primary-400' : activeTab === 'excretion' ? 'border-l-amber-400' : 'border-l-purple-400'"
          >
            <!-- Top row: icon + time + source badge -->
            <div class="flex items-center justify-between mb-2">
              <span class="text-2xl leading-none">{{ recordIcon(record) }}</span>
              <span
                class="text-[10px] px-2 py-0.5 rounded-full font-medium"
                :class="record.source === 'quick_checkin'
                  ? 'bg-amber-50 text-amber-600 border border-amber-200'
                  : 'bg-surface-100 text-surface-400 border border-surface-200'"
              >
                {{ sourceBadge(record.source) }}
              </span>
            </div>
            <p class="text-xs text-surface-400 mb-2">
              {{ new Date(record.recorded_at).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }) }}
            </p>
            <!-- Feeding -->
            <template v-if="activeTab === 'feeding'">
              <p class="text-lg font-bold text-surface-900">{{ feedingDetail(record as FeedingRecord) }}</p>
            </template>
            <!-- Excretion -->
            <template v-else-if="activeTab === 'excretion'">
              <p class="text-lg font-bold text-surface-900">{{ excretionDetail(record as ExcretionRecord) }}</p>
            </template>
            <!-- Behavior -->
            <template v-else>
              <p class="text-lg font-bold text-surface-900">{{ behaviorDetail(record as BehaviorRecord) }}</p>
            </template>
            <p v-if="record.notes" class="mt-1 text-sm text-surface-500 line-clamp-2">{{ record.notes }}</p>
            <div class="flex gap-2 mt-3 opacity-0 group-hover:opacity-100 transition-opacity">
              <button class="text-xs px-3 py-1.5 rounded-lg bg-primary-50 text-primary-700 hover:bg-primary-100 transition-colors" @click="openEdit(record)">编辑</button>
              <button class="text-xs px-3 py-1.5 rounded-lg bg-teal-50 text-teal-700 hover:bg-teal-100 transition-colors" @click="copyRecord(record)">复制</button>
              <button class="text-xs px-3 py-1.5 rounded-lg bg-red-50 text-red-700 hover:bg-red-100 transition-colors" @click="confirmDelete(record)">删除</button>
            </div>
          </article>
        </div>
      </section>

      <!-- Record list -->
      <div v-else class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <article
          v-for="record in records"
          :key="record.id"
          class="glass-card p-5 group relative border-l-4"
          :class="activeTab === 'feeding' ? 'border-l-primary-300' : activeTab === 'excretion' ? 'border-l-amber-300' : 'border-l-purple-300'"
        >
          <!-- Top row -->
          <div class="flex items-center justify-between mb-2">
            <span class="text-2xl leading-none">{{ recordIcon(record) }}</span>
            <span
              class="text-[10px] px-2 py-0.5 rounded-full font-medium"
              :class="record.source === 'quick_checkin'
                ? 'bg-amber-50 text-amber-600 border border-amber-200'
                : 'bg-surface-100 text-surface-400 border border-surface-200'"
            >
              {{ sourceBadge(record.source) }}
            </span>
          </div>
          <!-- Time -->
          <p class="text-xs text-surface-400 mb-2">{{ formatTime(record.recorded_at) }}</p>

          <!-- Feeding card -->
          <template v-if="activeTab === 'feeding'">
            <p class="text-lg font-bold text-surface-900">{{ feedingDetail(record as FeedingRecord) }}</p>
            <p v-if="record.notes" class="mt-1 text-sm text-surface-500 line-clamp-2">{{ record.notes }}</p>
          </template>

          <!-- Excretion card -->
          <template v-else-if="activeTab === 'excretion'">
            <p class="text-lg font-bold text-surface-900">{{ excretionDetail(record as ExcretionRecord) }}</p>
            <p v-if="record.notes" class="mt-1 text-sm text-surface-500 line-clamp-2">{{ record.notes }}</p>
          </template>

          <!-- Behavior card -->
          <template v-else>
            <p class="text-lg font-bold text-surface-900">{{ behaviorDetail(record as BehaviorRecord) }}</p>
            <p v-if="record.notes" class="mt-1 text-sm text-surface-500 line-clamp-2">{{ record.notes }}</p>
          </template>

          <!-- Actions -->
          <div class="flex gap-2 mt-3 opacity-0 group-hover:opacity-100 transition-opacity">
            <button class="text-xs px-3 py-1.5 rounded-lg bg-primary-50 text-primary-700 hover:bg-primary-100 transition-colors" @click="openEdit(record)">编辑</button>
            <button class="text-xs px-3 py-1.5 rounded-lg bg-teal-50 text-teal-700 hover:bg-teal-100 transition-colors" @click="copyRecord(record)">复制</button>
            <button class="text-xs px-3 py-1.5 rounded-lg bg-red-50 text-red-700 hover:bg-red-100 transition-colors" @click="confirmDelete(record)">删除</button>
          </div>
        </article>
      </div>
    </main>

    <!-- ── Edit Modal ──────────────────────────────────────────────────────── -->
    <Teleport to="body">
      <div
        v-if="editing"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4"
        @click.self="cancelEdit"
      >
        <div class="bg-white rounded-2xl shadow-2xl w-full max-w-md p-6 space-y-4 max-h-[90vh] overflow-y-auto">
          <h2 class="text-xl font-bold text-surface-900">编辑{{ TAB_LABELS[activeTab] }}记录</h2>

          <!-- Feeding form -->
          <template v-if="activeTab === 'feeding'">
            <label class="flex flex-col gap-1 text-sm text-surface-600">
              食物类型
              <select v-model="editForm.food_type" class="rounded-xl border-surface-200">
                <option v-for="opt in FOOD_TYPE_OPTIONS" :key="opt" :value="opt">{{ opt }}</option>
              </select>
            </label>
            <label class="flex flex-col gap-1 text-sm text-surface-600">
              食量 (g)
              <input v-model.number="editForm.amount" type="number" min="0" class="rounded-xl border-surface-200" />
            </label>
          </template>

          <!-- Excretion form -->
          <template v-else-if="activeTab === 'excretion'">
            <label class="flex flex-col gap-1 text-sm text-surface-600">
              类型
              <select v-model="editForm.type" class="rounded-xl border-surface-200">
                <option v-for="opt in EXCRETION_TYPE_OPTIONS" :key="opt" :value="opt">{{ opt }}</option>
              </select>
            </label>
            <label class="flex flex-col gap-1 text-sm text-surface-600">
              性状
              <select v-model="editForm.consistency" class="rounded-xl border-surface-200">
                <option value="">不指定</option>
                <option v-for="opt in CONSISTENCY_OPTIONS" :key="opt" :value="opt">{{ opt }}</option>
              </select>
            </label>
          </template>

          <!-- Behavior form -->
          <template v-else>
            <label class="flex flex-col gap-1 text-sm text-surface-600">
              行为类型
              <select v-model="editForm.behavior_type" class="rounded-xl border-surface-200">
                <option v-for="opt in BEHAVIOR_TYPE_OPTIONS" :key="opt" :value="opt">{{ opt }}</option>
              </select>
            </label>
            <label class="flex flex-col gap-1 text-sm text-surface-600">
              时长 (分钟)
              <input v-model.number="editForm.duration_minutes" type="number" min="0" class="rounded-xl border-surface-200" />
            </label>
            <label class="flex flex-col gap-1 text-sm text-surface-600">
              情绪
              <select v-model="editForm.mood" class="rounded-xl border-surface-200">
                <option value="">不指定</option>
                <option v-for="opt in MOOD_OPTIONS" :key="opt" :value="opt">{{ opt }}</option>
              </select>
            </label>
          </template>

          <!-- Common fields -->
          <label class="flex flex-col gap-1 text-sm text-surface-600">
            备注
            <input v-model="editForm.notes" class="rounded-xl border-surface-200" />
          </label>
          <label class="flex flex-col gap-1 text-sm text-surface-600">
            记录时间
            <input
              v-model="editForm.recorded_at"
              type="datetime-local"
              class="rounded-xl border-surface-200"
            />
          </label>

          <div class="flex gap-3 justify-end pt-2">
            <button class="btn-ghost" @click="cancelEdit">取消</button>
            <button class="btn-primary" @click="saveEdit">保存</button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- ── Delete Confirmation Modal ───────────────────────────────────────── -->
    <Teleport to="body">
      <div
        v-if="deleting"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4"
        @click.self="deleting = null"
      >
        <div class="bg-white rounded-2xl shadow-2xl w-full max-w-sm p-6 space-y-4">
          <span class="text-4xl block text-center">⚠️</span>
          <h3 class="text-lg font-bold text-center text-surface-900">确认删除这条记录？</h3>
          <p class="text-sm text-surface-500 text-center">此操作不可撤销。</p>
          <div class="flex gap-3 justify-center">
            <button class="btn-ghost" @click="deleting = null">取消</button>
            <button class="bg-red-600 text-white rounded-xl px-5 py-2.5 text-sm font-medium hover:bg-red-700 transition-colors" @click="executeDelete">确认删除</button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>
