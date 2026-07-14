import { defineStore } from 'pinia'
import { computed, ref, watch } from 'vue'

export type ThemeMode = 'light' | 'dark' | 'system'

export const useThemeStore = defineStore('theme', () => {
  const saved = localStorage.getItem('theme') as ThemeMode | null
  const mode = ref<ThemeMode>(saved || 'system')

  const systemDark = ref(window.matchMedia('(prefers-color-scheme: dark)').matches)
  const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
  mediaQuery.addEventListener('change', (e) => {
    systemDark.value = e.matches
  })

  const resolvedTheme = computed<'light' | 'dark'>(() => {
    if (mode.value === 'system') return systemDark.value ? 'dark' : 'light'
    return mode.value
  })

  function setTheme(newMode: ThemeMode) {
    mode.value = newMode
    localStorage.setItem('theme', newMode)
  }

  function cycle() {
    const order: ThemeMode[] = ['light', 'dark', 'system']
    const idx = order.indexOf(mode.value)
    setTheme(order[(idx + 1) % order.length])
  }

  // Apply theme class to <html>
  watch(resolvedTheme, (theme) => {
    document.documentElement.classList.toggle('dark', theme === 'dark')
  }, { immediate: true })

  return { mode, resolvedTheme, setTheme, cycle }
})
