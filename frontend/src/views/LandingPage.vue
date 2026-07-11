<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { RouterLink } from 'vue-router'
import api from '@/composables/api'

const backendStatus = ref<'loading' | 'ok' | 'error'>('loading')
const apiVersion = ref('')

onMounted(async () => {
  try {
    const { data } = await api.get('/health')
    backendStatus.value = 'ok'
    apiVersion.value = data.version || ''
  } catch {
    backendStatus.value = 'error'
  }
})
</script>

<template>
  <div class="min-h-[100dvh] gradient-hero">
    <!-- Navigation -->
    <nav class="sticky top-0 z-50 bg-white/60 backdrop-blur-xl border-b border-white/20">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex items-center justify-between h-16">
          <!-- Logo -->
          <RouterLink to="/" class="flex items-center gap-2 group">
            <span class="text-3xl group-hover:scale-110 transition-transform duration-300">🐾</span>
            <span class="text-xl font-bold bg-gradient-to-r from-primary-600 to-primary-400 bg-clip-text text-transparent">
              Pet Tracker
            </span>
          </RouterLink>

          <!-- Nav links -->
          <div class="hidden md:flex items-center gap-6">
            <a href="#features" class="text-surface-600 hover:text-primary-600 transition-colors font-medium">功能</a>
            <a href="#tech" class="text-surface-600 hover:text-primary-600 transition-colors font-medium">技术栈</a>
            <RouterLink to="/login" class="btn-ghost">登录</RouterLink>
            <RouterLink to="/register" class="btn-primary">免费注册</RouterLink>
          </div>

          <!-- Mobile menu button -->
          <button class="md:hidden p-2 rounded-lg hover:bg-white/50 transition-colors">
            <svg class="w-6 h-6 text-surface-700" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </button>
        </div>
      </div>
    </nav>

    <!-- Hero Section -->
    <section class="relative overflow-hidden">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 md:py-32">
        <div class="grid md:grid-cols-2 gap-12 items-center">
          <!-- Text -->
          <div class="animate-fade-in">
            <div class="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/60 backdrop-blur-sm text-primary-700 text-sm font-medium mb-6">
              <span class="w-2 h-2 rounded-full bg-primary-500 animate-pulse"></span>
              宠物健康管理 · 云端 SaaS
            </div>
            <h1 class="text-4xl md:text-6xl font-extrabold tracking-tighter text-surface-900 leading-tight">
              守护毛孩子的
              <span class="bg-gradient-to-r from-primary-600 to-primary-400 bg-clip-text text-transparent">每一天</span>
            </h1>
            <p class="mt-6 text-lg md:text-xl text-surface-500 max-w-lg leading-relaxed">
              记录进食、排便与行为，生成健康趋势报告。定时提醒不错过每一餐，让科学养宠触手可及。
            </p>
            <div class="mt-8 flex flex-col sm:flex-row gap-4">
              <RouterLink to="/register" class="btn-primary text-lg px-8 py-4 rounded-2xl shadow-lg shadow-primary-200 hover:shadow-xl hover:shadow-primary-300 transition-shadow">
                免费开始使用
              </RouterLink>
              <a href="#features" class="btn-ghost text-lg">
                了解更多 →
              </a>
            </div>

            <!-- Backend status badge -->
            <div class="mt-6 flex items-center gap-2 text-sm">
              <span class="text-surface-400">API 状态:</span>
              <span v-if="backendStatus === 'ok'"
                    class="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-green-50 text-green-700 text-xs font-medium">
                <span class="w-1.5 h-1.5 rounded-full bg-green-500"></span>
                在线 {{ apiVersion }}
              </span>
              <span v-else-if="backendStatus === 'loading'"
                    class="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-surface-100 text-surface-500 text-xs font-medium">
                <span class="w-1.5 h-1.5 rounded-full bg-surface-400 animate-pulse"></span>
                检测中...
              </span>
              <span v-else
                    class="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-red-50 text-red-700 text-xs font-medium">
                <span class="w-1.5 h-1.5 rounded-full bg-red-500"></span>
                离线
              </span>
            </div>
          </div>

          <!-- Hero visual -->
          <div class="hidden md:flex justify-center animate-float">
            <div class="relative">
              <div class="w-80 h-80 rounded-[3rem] bg-white/40 backdrop-blur-xl border border-white/50 shadow-2xl flex items-center justify-center">
                <span class="text-9xl">🐱</span>
              </div>
              <div class="absolute -bottom-4 -right-4 w-24 h-24 rounded-2xl bg-white/60 backdrop-blur-xl border border-white/50 shadow-lg flex items-center justify-center">
                <span class="text-4xl">🐶</span>
              </div>
              <div class="absolute -top-4 -left-4 w-16 h-16 rounded-xl bg-white/50 backdrop-blur-xl border border-white/50 shadow-lg flex items-center justify-center">
                <span class="text-2xl">🐰</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Features Grid -->
    <section id="features" class="py-20 bg-white/40">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="text-center mb-16">
          <h2 class="text-3xl md:text-4xl font-extrabold tracking-tighter text-surface-900">
            五大核心功能
          </h2>
          <p class="mt-4 text-surface-500 max-w-xl mx-auto">
            从日常记录到健康分析，一站式管理宠物生活
          </p>
        </div>

        <div class="grid sm:grid-cols-2 lg:grid-cols-5 gap-6">
          <div v-for="feature in features" :key="feature.title"
               class="glass-card p-6 hover:scale-105 transition-transform duration-300 ease-out group">
            <div class="text-4xl mb-4 group-hover:scale-110 transition-transform duration-300">{{ feature.icon }}</div>
            <h3 class="text-lg font-bold text-surface-900 mb-2">{{ feature.title }}</h3>
            <p class="text-sm text-surface-500 leading-relaxed">{{ feature.desc }}</p>
          </div>
        </div>
      </div>
    </section>

    <!-- Tech Stack -->
    <section id="tech" class="py-20">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        <h2 class="text-3xl md:text-4xl font-extrabold tracking-tighter text-surface-900 mb-4">技术栈</h2>
        <p class="text-surface-500 mb-12 max-w-lg mx-auto">现代技术栈，高性能、可扩展、开发者友好</p>
        <div class="flex flex-wrap justify-center gap-4">
          <span v-for="tech in techStack" :key="tech"
                class="px-5 py-2.5 rounded-xl bg-white/60 backdrop-blur-sm border border-white/30 text-surface-700 font-medium shadow-sm hover:shadow-md transition-shadow">
            {{ tech }}
          </span>
        </div>
      </div>
    </section>

    <!-- Progress Bar -->
    <section class="py-20 bg-gradient-to-b from-white/40 to-transparent">
      <div class="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="glass-card p-8 md:p-12">
          <h2 class="text-2xl font-extrabold tracking-tighter text-surface-900 mb-6 text-center">开发进度</h2>
          <div class="space-y-4">
            <div v-for="m in milestones" :key="m.label">
              <div class="flex justify-between text-sm mb-1.5">
                <span class="font-medium text-surface-700">{{ m.label }}</span>
                <span :class="m.done ? 'text-green-600' : 'text-surface-400'">
                  {{ m.done ? '✅' : '⬜' }} {{ m.status }}
                </span>
              </div>
              <div class="h-2.5 rounded-full bg-surface-100 overflow-hidden">
                <div class="h-full rounded-full bg-gradient-to-r from-primary-500 to-primary-400 transition-all duration-700 ease-out"
                     :style="{ width: m.progress + '%' }"></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Footer -->
    <footer class="py-8 border-t border-white/20">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center text-surface-400 text-sm">
        <p>&copy; 2026 Pet Tracker — Built with FastAPI + Vue 3</p>
      </div>
    </footer>
  </div>
</template>

<script lang="ts">
const features = [
  { icon: '🍽️', title: '进食记录', desc: '记录每餐的食量、种类与时间，追踪饮食习惯' },
  { icon: '💩', title: '排便记录', desc: '记录排便频率与状态，及时发现异常' },
  { icon: '🏃', title: '行为观察', desc: '记录日常行为变化，掌握健康状况' },
  { icon: '📊', title: '数据仪表盘', desc: '可视化趋势图表，一目了然' },
  { icon: '🔔', title: '智能提醒', desc: '定时提醒喂食、驱虫、体检，不再遗忘' },
]

const techStack = [
  'FastAPI', 'Vue 3', 'TypeScript', 'Tailwind CSS',
  'SQLAlchemy 2.0', 'Alembic', 'SQLite / PostgreSQL',
  'Docker', 'GitHub Actions', 'pytest',
]

const milestones = [
  { label: 'M1 — 脚手架', done: true, progress: 100, status: '已完成' },
  { label: 'M2 — 账号 + 宠物管理', done: false, progress: 0, status: '待开始' },
  { label: 'M3 — 三大记录 + 快速打卡', done: false, progress: 0, status: '待开始' },
  { label: 'M4 — 提醒 + 仪表盘', done: false, progress: 0, status: '待开始' },
  { label: 'M5 — 打磨与上线', done: false, progress: 0, status: '待开始' },
]
</script>
