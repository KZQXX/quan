<script setup lang="ts">
import { RouterLink } from 'vue-router'
</script>

<template>
  <div class="min-h-[100dvh] bg-surface-50">
    <!-- Dashboard header bar -->
    <header class="bg-white/80 backdrop-blur-xl border-b border-surface-200 sticky top-0 z-40">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <RouterLink to="/" class="flex items-center gap-2">
          <span class="text-2xl">🐾</span>
          <span class="text-lg font-bold bg-gradient-to-r from-primary-600 to-primary-400 bg-clip-text text-transparent">
            Pet Tracker
          </span>
        </RouterLink>
        <div class="flex items-center gap-4">
          <span class="text-sm text-surface-500">控制面板</span>
        </div>
      </div>
    </header>

    <!-- Dashboard content -->
    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div class="glass-card p-12 text-center">
        <span class="text-6xl">🚧</span>
        <h1 class="text-2xl font-extrabold tracking-tighter text-surface-900 mt-4">仪表盘开发中</h1>
        <p class="text-surface-500 mt-2 max-w-md mx-auto">
          数据可视化、宠物管理、记录中心等功能将在后续里程碑中实现。
        </p>
        <div class="mt-8 grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div class="glass-card p-4">
            <div class="text-2xl font-bold text-primary-600">0</div>
            <div class="text-sm text-surface-500">我的宠物</div>
          </div>
          <div class="glass-card p-4">
            <div class="text-2xl font-bold text-primary-600">0</div>
            <div class="text-sm text-surface-500">今日记录</div>
          </div>
          <div class="glass-card p-4">
            <div class="text-2xl font-bold text-primary-600">0</div>
            <div class="text-sm text-surface-500">待办提醒</div>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>
