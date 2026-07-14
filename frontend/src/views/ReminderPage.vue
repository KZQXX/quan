<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import ThemeToggle from '@/components/ThemeToggle.vue'
import api from '@/composables/api'
import { reminderApi, type Reminder, type ReminderCreate, type ReminderUpdate } from '@/composables/api'

interface Pet { id: string; name: string; species: string }

const auth = useAuthStore()
const reminders = ref<Reminder[]>([])
const pets = ref<Pet[]>([])
const loading = ref(true)
const error = ref('')

// Form state
const showForm = ref(false)
const editingId = ref<string | null>(null)
const formTitle = ref('')
const formType = ref('other')
const formPetId = ref('')
const formTime = ref('08:00')
const formRepeat = ref('none')
const formCron = ref('')
const formEnabled = ref(true)
const formError = ref('')
const submitting = ref(false)

// Delete confirmation
const deletingId = ref<string | null>(null)

const TYPE_LABELS: Record<string, string> = {
  feeding: '喂食',
  excretion: '排便',
  behavior: '行为',
  medication: '用药',
  other: '其他',
}
const REPEAT_LABELS: Record<string, string> = {
  none: '不重复',
  daily: '每天',
  weekly: '每周',
  custom: '自定义 cron',
}


async function fetchData() {
  loading.value = true
  error.value = ''
  try {
    const [rRes, pRes] = await Promise.all([reminderApi.list(), api.get('/pets')])
    reminders.value = rRes.data
    pets.value = pRes.data
  } catch (e: any) {
    error.value = e.response?.data?.detail || '加载失败，请稍后重试'
  } finally {
    loading.value = false
  }
}

function openCreate() {
  editingId.value = null
  formTitle.value = ''
  formType.value = 'other'
  formPetId.value = ''
  formTime.value = '08:00'
  formRepeat.value = 'none'
  formCron.value = ''
  formEnabled.value = true
  formError.value = ''
  showForm.value = true
}

function openEdit(reminder: Reminder) {
  editingId.value = reminder.id
  formTitle.value = reminder.title
  formType.value = reminder.reminder_type
  formPetId.value = reminder.pet_id ?? ''
  formTime.value = reminder.scheduled_time
  formRepeat.value = reminder.repeat_rule
  formCron.value = reminder.cron_expression ?? ''
  formEnabled.value = reminder.enabled
  formError.value = ''
  showForm.value = true
}

function closeForm() {
  showForm.value = false
  editingId.value = null
  formError.value = ''
}

async function submitForm() {
  if (!formTitle.value.trim()) return
  formError.value = ''
  submitting.value = true
  try {
    const payload: ReminderCreate | ReminderUpdate = {
      title: formTitle.value.trim(),
      reminder_type: formType.value,
      scheduled_time: formTime.value,
      repeat_rule: formRepeat.value,
      enabled: formEnabled.value,
    }
    if (formPetId.value) (payload as any).pet_id = formPetId.value
    if (formRepeat.value === 'custom') {
      ;(payload as any).cron_expression = formCron.value || undefined
    } else {
      ;(payload as any).cron_expression = null
    }

    if (editingId.value) {
      await reminderApi.update(editingId.value, payload)
    } else {
      await reminderApi.create(payload as ReminderCreate)
    }
    closeForm()
    await fetchData()
  } catch (e: any) {
    formError.value = e.response?.data?.detail || '操作失败，请重试'
  } finally {
    submitting.value = false
  }
}

async function toggleEnabled(reminder: Reminder) {
  try {
    await reminderApi.update(reminder.id, { enabled: !reminder.enabled })
    reminder.enabled = !reminder.enabled
  } catch {
    // silently ignore toggle errors
  }
}

async function confirmDelete() {
  if (!deletingId.value) return
  try {
    await reminderApi.delete(deletingId.value)
    reminders.value = reminders.value.filter((r) => r.id !== deletingId.value)
  } finally {
    deletingId.value = null
  }
}

onMounted(fetchData)
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
          <RouterLink to="/dashboard" class="hover:text-primary-600 transition-colors">面板</RouterLink>
          <RouterLink to="/records" class="hover:text-primary-600 transition-colors">记录中心</RouterLink>
          <RouterLink to="/reminders" class="text-primary-600 font-medium">提醒</RouterLink>
          <ThemeToggle />
          <span>{{ auth.user?.display_name || auth.user?.email }}</span>
          <button class="btn-ghost !px-3 !py-2" @click="auth.logout()">退出</button>
        </div>
      </div>
    </header>

    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      <!-- Page title -->
      <section class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 class="text-3xl font-extrabold text-surface-900">提醒管理</h1>
          <p class="mt-1 text-surface-500">定时提醒，不错过每一次照顾。</p>
        </div>
        <button class="btn-primary" @click="openCreate">+ 新建提醒</button>
      </section>

      <!-- Error banner -->
      <div v-if="error" class="glass-card p-4 text-red-700 text-sm">{{ error }}</div>

      <!-- Loading skeleton -->
      <div v-if="loading" class="glass-card p-12 text-center text-surface-400 text-sm">加载中...</div>

      <!-- Empty state -->
      <div v-else-if="!reminders.length" class="glass-card p-12 text-center space-y-4">
        <div class="text-5xl">⏰</div>
        <p class="text-surface-500">还没有提醒，点击上方按钮创建第一个。</p>
      </div>

      <!-- Reminder list -->
      <div v-else class="space-y-3">
        <div
          v-for="r in reminders"
          :key="r.id"
          class="glass-card p-5 flex flex-col sm:flex-row sm:items-center gap-4 transition-all duration-200"
          :class="{ 'opacity-60': !r.enabled }"
        >
          <!-- Icon + Info -->
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2">
              <span class="text-lg">{{ ['feeding','excretion','behavior','medication','other'].includes(r.reminder_type) ? { feeding:'🍽️', excretion:'💩', behavior:'🏃', medication:'💊', other:'📌' }[r.reminder_type] : '📌' }}</span>
              <span class="font-semibold text-surface-900 truncate">{{ r.title }}</span>
            </div>
            <div class="mt-1 flex flex-wrap gap-x-4 gap-y-1 text-sm text-surface-500">
              <span>{{ TYPE_LABELS[r.reminder_type] || r.reminder_type }}</span>
              <span>⏰ {{ r.scheduled_time }}</span>
              <span>{{ REPEAT_LABELS[r.repeat_rule] || r.repeat_rule }}</span>
              <span v-if="r.pet_id && pets.find(p => p.id === r.pet_id)" class="text-surface-400">
                {{ pets.find(p => p.id === r.pet_id)!.name }}
              </span>
            </div>
          </div>

          <!-- Actions -->
          <div class="flex items-center gap-3 shrink-0">
            <!-- Toggle switch -->
            <button
              class="relative w-11 h-6 rounded-full transition-colors duration-200"
              :class="r.enabled ? 'bg-primary-600' : 'bg-surface-300'"
              @click="toggleEnabled(r)"
              :title="r.enabled ? '点击关闭' : '点击启用'"
            >
              <span
                class="absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full shadow-sm transition-transform duration-200"
                :class="r.enabled ? 'translate-x-5' : ''"
              />
            </button>
            <button class="text-surface-400 hover:text-primary-600 transition-colors text-sm" @click="openEdit(r)">编辑</button>
            <button class="text-surface-400 hover:text-red-600 transition-colors text-sm" @click="deletingId = r.id">删除</button>
          </div>
        </div>
      </div>
    </main>

    <!-- Create / Edit Modal -->
    <Teleport to="body">
      <div
        v-if="showForm"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4"
        @click.self="closeForm"
      >
        <div class="glass-card w-full max-w-md max-h-[90vh] overflow-y-auto p-6 space-y-5" @click.stop>
          <h2 class="text-xl font-bold text-surface-900">{{ editingId ? '编辑提醒' : '新建提醒' }}</h2>

          <!-- Title -->
          <div>
            <label class="block text-sm font-medium text-surface-700 mb-1">提醒标题</label>
            <input
              v-model="formTitle"
              type="text"
              required
              maxlength="200"
              placeholder="例如：喂猫粮"
              class="w-full rounded-xl border-surface-200"
            />
          </div>

          <!-- Reminder type -->
          <div>
            <label class="block text-sm font-medium text-surface-700 mb-1">提醒类型</label>
            <select v-model="formType" class="w-full rounded-xl border-surface-200">
              <option v-for="(label, key) in TYPE_LABELS" :key="key" :value="key">{{ label }}</option>
            </select>
          </div>

          <!-- Pet selector -->
          <div>
            <label class="block text-sm font-medium text-surface-700 mb-1">关联宠物（可选）</label>
            <select v-model="formPetId" class="w-full rounded-xl border-surface-200">
              <option value="">不关联</option>
              <option v-for="pet in pets" :key="pet.id" :value="pet.id">{{ pet.name }} · {{ pet.species === 'cat' ? '猫' : pet.species === 'dog' ? '狗' : '其他' }}</option>
            </select>
          </div>

          <!-- Time picker (HH:MM) -->
          <div>
            <label class="block text-sm font-medium text-surface-700 mb-1">提醒时间</label>
            <input
              v-model="formTime"
              type="time"
              required
              class="w-full rounded-xl border-surface-200"
            />
          </div>

          <!-- Repeat rule -->
          <div>
            <label class="block text-sm font-medium text-surface-700 mb-1">重复规则</label>
            <select v-model="formRepeat" class="w-full rounded-xl border-surface-200">
              <option v-for="(label, key) in REPEAT_LABELS" :key="key" :value="key">{{ label }}</option>
            </select>
          </div>

          <!-- Custom cron -->
          <div v-if="formRepeat === 'custom'">
            <label class="block text-sm font-medium text-surface-700 mb-1">Cron 表达式</label>
            <input
              v-model="formCron"
              type="text"
              placeholder="例如：0 8 * * 1-5"
              class="w-full rounded-xl border-surface-200 font-mono text-sm"
            />
            <p class="mt-1 text-xs text-surface-400">格式：分 时 日 月 周</p>
          </div>

          <!-- Enabled -->
          <label class="flex items-center gap-3 cursor-pointer">
            <button
              class="relative w-11 h-6 rounded-full transition-colors duration-200"
              :class="formEnabled ? 'bg-primary-600' : 'bg-surface-300'"
              @click="formEnabled = !formEnabled"
            >
              <span
                class="absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full shadow-sm transition-transform duration-200"
                :class="formEnabled ? 'translate-x-5' : ''"
              />
            </button>
            <span class="text-sm text-surface-700">启用提醒</span>
          </label>

          <!-- Form error -->
          <div v-if="formError" class="text-sm text-red-600 bg-red-50 rounded-lg p-3">{{ formError }}</div>

          <!-- Actions -->
          <div class="flex gap-3 pt-2">
            <button class="btn-ghost flex-1" @click="closeForm">取消</button>
            <button
              class="btn-primary flex-1"
              :disabled="submitting || !formTitle.trim()"
              @click="submitForm"
            >
              {{ submitting ? '保存中...' : editingId ? '保存修改' : '创建提醒' }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Delete confirmation dialog -->
    <Teleport to="body">
      <div
        v-if="deletingId"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4"
        @click.self="deletingId = null"
      >
        <div class="glass-card w-full max-w-sm p-6 space-y-5 text-center" @click.stop>
          <div class="text-4xl">🗑️</div>
          <div>
            <h3 class="text-lg font-bold text-surface-900">确认删除？</h3>
            <p class="mt-1 text-sm text-surface-500">删除后无法恢复，确定要继续吗？</p>
          </div>
          <div class="flex gap-3">
            <button class="btn-ghost flex-1" @click="deletingId = null">取消</button>
            <button class="flex-1 rounded-xl bg-red-600 text-white px-4 py-2.5 font-medium hover:bg-red-700 transition-colors" @click="confirmDelete">确认删除</button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>
