<script setup lang="ts">
import { ref } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const displayName = ref('')
const email = ref('')
const password = ref('')
const loading = ref(false)
const error = ref('')
const auth = useAuthStore()

async function handleRegister() {
  loading.value = true
  error.value = ''
  try {
    await auth.register(email.value, password.value, displayName.value)
    router.push('/login')
  } catch (err: any) {
    error.value = err.response?.data?.detail || '注册失败，请稍后重试。'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="min-h-[100dvh] gradient-hero flex items-center justify-center p-4">
    <div class="w-full max-w-md animate-fade-in">
      <RouterLink to="/" class="inline-flex items-center gap-2 text-surface-500 hover:text-primary-600 mb-8 transition-colors">
        <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
        </svg>
        返回首页
      </RouterLink>

      <div class="glass-card p-8 md:p-10">
        <div class="text-center mb-8">
          <span class="text-4xl">🐾</span>
          <h1 class="text-2xl font-extrabold tracking-tighter text-surface-900 mt-3">创建账号</h1>
          <p class="text-surface-500 mt-2">开始科学养宠之旅</p>
        </div>

        <form @submit.prevent="handleRegister" class="space-y-5">
          <p v-if="error" class="rounded-lg bg-red-50 p-3 text-sm text-red-700">{{ error }}</p>
          <div>
            <label class="block text-sm font-medium text-surface-700 mb-1.5">昵称</label>
            <input v-model="displayName" type="text" required
                   class="w-full rounded-xl border-surface-200 bg-white/80 focus:border-primary-500 focus:ring-primary-500"
                   placeholder="你的名字" />
          </div>
          <div>
            <label class="block text-sm font-medium text-surface-700 mb-1.5">邮箱</label>
            <input v-model="email" type="email" required
                   class="w-full rounded-xl border-surface-200 bg-white/80 focus:border-primary-500 focus:ring-primary-500"
                   placeholder="your@email.com" />
          </div>
          <div>
            <label class="block text-sm font-medium text-surface-700 mb-1.5">密码</label>
            <input v-model="password" type="password" required minlength="8"
                   class="w-full rounded-xl border-surface-200 bg-white/80 focus:border-primary-500 focus:ring-primary-500"
                   placeholder="至少 8 位" />
          </div>
          <button type="submit" :disabled="loading"
                  class="btn-primary w-full text-lg py-3 rounded-2xl">
            {{ loading ? '注册中...' : '注册' }}
          </button>
        </form>

        <p class="mt-6 text-center text-sm text-surface-500">
          已有账号？
          <RouterLink to="/login" class="text-primary-600 font-semibold hover:text-primary-700">立即登录</RouterLink>
        </p>
      </div>
    </div>
  </div>
</template>
