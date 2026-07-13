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
}

interface FeedingRecord extends RecordItem {
  food_type: string
  amount: number | null
  source: string
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
  if (startDate.value) p.start_date = startDate.value
  if (endDate.value) p.end_date = endDate.value + 'T23:59:59'
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
async function createFeedingRecord() {
  if (!selectedPetId.value || !newFoodType.value) return
  creating.value = true
  error.value = ''
  try {
    await api.post(`/pets/${selectedPetId.value}/feedings`, {
      food_type: newFoodType.value,
      amount: newAmount.value,
      notes: newNotes.value || undefined,
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
  createFeedingRecord()
}

// ── Create excretion record ────────────────────────────────────────────────
async function createExcretionRecord() {
  if (!selectedPetId.value || !newExcretionType.value) return
  creating.value = true
  error.value = ''
  try {
    await api.post(`/pets/${selectedPetId.value}/excretions`, {
      type: newExcretionType.value,
      consistency: newConsistency.value || undefined,
      notes: newExcretionNotes.value || undefined,
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
  createExcretionRecord()
}

// ── Create behavior record ────────────────────────────────────────────────
async function createBehaviorRecord() {
  if (!selectedPetId.value || !newBehaviorType.value) return
  creating.value = true
  error.value = ''
  try {
    await api.post(`/pets/${selectedPetId.value}/behaviors`, {
      behavior_type: newBehaviorType.value,
      duration_minutes: newDurationMinutes.value,
      mood: newMood.value || undefined,
      notes: newBehaviorNotes.value || undefined,
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
  createBehaviorRecord()
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
    if (v !== editing.value[k as keyof RecordType] && v !== '') body[k] = v === '' ? null : v
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
        <form class="flex flex-wrap gap-3 items-end" @submit.prevent="createFeedingRecord">
          <label class="flex flex-col gap-1 text-xs text-surface-500 min-w-[120px]">
            食物类型
            <select v-model="newFoodType" class="rounded-xl border-surface-200 text-sm">
              <option v-for="opt in FOOD_TYPE_OPTIONS" :key="opt" :value="opt">{{ opt }}</option>
            </select>
          </label>
          <label class="flex flex-col gap-1 text-xs text-surface-500 w-28">
            食量 (g)
            <input
              v-model.number="newAmount"
              type="number"
              min="0"
              placeholder="克数"
              class="rounded-xl border-surface-200 text-sm"
            />
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
        <form class="flex flex-wrap gap-3 items-end" @submit.prevent="createExcretionRecord">
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
        <form class="flex flex-wrap gap-3 items-end" @submit.prevent="createBehaviorRecord">
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
            />
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

      <!-- Empty state -->
      <div v-else-if="!hasRecords && selectedPetId" class="text-center py-16">
        <span class="text-5xl">📋</span>
        <p class="mt-4 text-lg text-surface-500">暂无{{ TAB_LABELS[activeTab] }}记录</p>
        <p class="text-sm text-surface-400 mt-1">前往控制面板添加第一条记录吧。</p>
        <RouterLink to="/dashboard" class="btn-primary mt-5 inline-block">前往控制面板</RouterLink>
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
            class="glass-card p-5 group relative border-l-4 border-primary-400"
          >
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
            <p v-if="record.notes" class="mt-1 text-sm text-surface-500">{{ record.notes }}</p>
            <div class="flex gap-2 mt-3 opacity-0 group-hover:opacity-100 transition-opacity">
              <button class="text-xs px-3 py-1.5 rounded-lg bg-primary-50 text-primary-700 hover:bg-primary-100 transition-colors" @click="openEdit(record)">编辑</button>
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
          class="glass-card p-5 group relative"
        >
          <!-- Time -->
          <p class="text-xs text-surface-400 mb-2">{{ formatTime(record.recorded_at) }}</p>

          <!-- Feeding card -->
          <template v-if="activeTab === 'feeding'">
            <p class="text-lg font-bold text-surface-900">{{ feedingDetail(record as FeedingRecord) }}</p>
            <p v-if="record.notes" class="mt-1 text-sm text-surface-500">{{ record.notes }}</p>
          </template>

          <!-- Excretion card -->
          <template v-else-if="activeTab === 'excretion'">
            <p class="text-lg font-bold text-surface-900">{{ excretionDetail(record as ExcretionRecord) }}</p>
            <p v-if="record.notes" class="mt-1 text-sm text-surface-500">{{ record.notes }}</p>
          </template>

          <!-- Behavior card -->
          <template v-else>
            <p class="text-lg font-bold text-surface-900">{{ behaviorDetail(record as BehaviorRecord) }}</p>
            <p v-if="record.notes" class="mt-1 text-sm text-surface-500">{{ record.notes }}</p>
          </template>

          <!-- Actions -->
          <div class="flex gap-2 mt-3 opacity-0 group-hover:opacity-100 transition-opacity">
            <button class="text-xs px-3 py-1.5 rounded-lg bg-primary-50 text-primary-700 hover:bg-primary-100 transition-colors" @click="openEdit(record)">编辑</button>
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
