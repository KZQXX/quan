import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/composables/api'

export interface User {
  id: string
  email: string
  display_name: string
}

export const useAuthStore = defineStore('auth', () => {
  const savedUser = localStorage.getItem('user')
  const user = ref<User | null>(savedUser ? JSON.parse(savedUser) as User : null)
  const token = ref<string | null>(localStorage.getItem('token'))
  const isAuthenticated = ref(Boolean(token.value))

  async function login(email: string, password: string) {
    // TODO: D6 — real API call
    const response = await api.post('/auth/login', { email, password })
    token.value = response.data.access_token
    user.value = response.data.user
    localStorage.setItem('token', token.value!)
    localStorage.setItem('user', JSON.stringify(user.value))
    isAuthenticated.value = true
    return response.data
  }

  async function register(email: string, password: string, displayName: string) {
    // TODO: D6 — real API call
    const response = await api.post('/auth/register', {
      email,
      password,
      display_name: displayName,
    })
    return response.data
  }

  function logout() {
    token.value = null
    user.value = null
    isAuthenticated.value = false
    localStorage.removeItem('token')
    localStorage.removeItem('user')
  }

  return {
    user,
    token,
    isAuthenticated,
    login,
    register,
    logout,
  }
})
