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
