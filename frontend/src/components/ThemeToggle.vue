<template>
  <button
    @click="theme.cycle()"
    class="relative rounded-xl p-2 text-lg transition-all duration-300 hover:scale-110 active:scale-95"
    :class="theme.resolvedTheme === 'dark' ? 'bg-surface-800 text-yellow-300 hover:bg-surface-700' : 'bg-surface-100 text-surface-600 hover:bg-surface-200'"
    :title="label"
  >
    <!-- Sun (light) -->
    <svg v-if="theme.resolvedTheme === 'light'" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
      <path stroke-linecap="round" stroke-linejoin="round" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
    </svg>
    <!-- Moon (dark) -->
    <svg v-else-if="theme.resolvedTheme === 'dark'" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
      <path stroke-linecap="round" stroke-linejoin="round" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
    </svg>
  </button>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useThemeStore } from '@/stores/theme'

const theme = useThemeStore()

const label = computed(() => {
  const labels: Record<string, string> = { light: '浅色模式', dark: '深色模式', system: '跟随系统' }
  return `${labels[theme.mode]} — 点击切换`
})
</script>
