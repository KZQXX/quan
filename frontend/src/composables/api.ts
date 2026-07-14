import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const message = error.response?.data?.detail || error.message || 'Something went wrong'
    console.error(`[API Error] ${message}`)
    return Promise.reject(error)
  },
)

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

export default api

// ── Reminder API ──────────────────────────────────────────────────────────

export interface Reminder {
  id: string
  pet_id: string | null
  title: string
  reminder_type: string
  scheduled_time: string  // HH:MM
  repeat_rule: string
  cron_expression: string | null
  enabled: boolean
  last_triggered_at: string | null
}

export interface ReminderCreate {
  pet_id?: string | null
  title: string
  reminder_type?: string
  scheduled_time: string
  repeat_rule?: string
  cron_expression?: string | null
  enabled?: boolean
}

export interface ReminderUpdate {
  pet_id?: string | null
  title?: string
  reminder_type?: string
  scheduled_time?: string
  repeat_rule?: string
  cron_expression?: string | null
  enabled?: boolean
}

export const reminderApi = {
  list: () => api.get<Reminder[]>('/reminders'),
  get: (id: string) => api.get<Reminder>(`/reminders/${id}`),
  create: (data: ReminderCreate) => api.post<Reminder>('/reminders', data),
  update: (id: string, data: ReminderUpdate) => api.patch<Reminder>(`/reminders/${id}`, data),
  delete: (id: string) => api.delete(`/reminders/${id}`),
}

// ── Notification API ──────────────────────────────────────────────────────

export interface Notification {
  id: string
  type: string
  title: string
  message: string | null
  is_read: boolean
  created_at_ts: string
}

export const notificationApi = {
  list: (unreadOnly = false) =>
    api.get<Notification[]>('/notifications', { params: { unread_only: unreadOnly } }),
  markRead: (id: string) => api.patch(`/notifications/${id}/read`),
  markAllRead: () => api.post('/notifications/read-all'),
  unreadCount: () => api.get<{ count: number }>('/notifications/unread-count'),
}

// ── User Preferences API ──────────────────────────────────────────────────

export const preferencesApi = {
  update: (data: { notify_email?: boolean; webhook_url?: string | null }) =>
    api.patch('/auth/preferences', data),
}

// ── Statistics API ─────────────────────────────────────────────────────────

export interface DailyStat {
  pet_id: string
  date: string
  feeding_count: number
  excretion_count: number
  behavior_count: number
  total_duration_minutes: number
}

export interface StatsReport {
  date_range: { start: string | null; end: string | null }
  days: number
  totals: { feeding_count: number; excretion_count: number; behavior_count: number; total_duration_minutes: number }
  per_pet: Array<{
    pet_id: string
    pet_name: string
    feeding_count: number
    excretion_count: number
    behavior_count: number
    total_duration_minutes: number
    days_tracked: number
  }>
}

export const statsApi = {
  daily: (params?: { pet_id?: string; start_date?: string; end_date?: string }) =>
    api.get<DailyStat[]>('/stats/daily', { params }),
  report: (params?: { pet_id?: string; start_date?: string; end_date?: string }) =>
    api.get<StatsReport>('/stats/report', { params }),
  exportCsvUrl: (params?: { pet_id?: string; start_date?: string; end_date?: string }) => {
    const qs = new URLSearchParams()
    if (params?.pet_id) qs.set('pet_id', params.pet_id)
    if (params?.start_date) qs.set('start_date', params.start_date)
    if (params?.end_date) qs.set('end_date', params.end_date)
    return `/api/stats/export?${qs.toString()}`
  },
}
