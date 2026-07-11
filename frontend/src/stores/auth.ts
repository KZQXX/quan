import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/composables/api'

export interface User {
  id: string
  email: string
  display_name: string
}

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const token = ref<string | null>(localStorage.getItem('token'))
  const isAuthenticated = ref(false)

  async function login(email: string, password: string) {
    // TODO: D6 — real API call
    const response = await api.post('/auth/login', { email, password })
    token.value = response.data.access_token
    localStorage.setItem('token', token.value!)
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
