<script setup lang="ts">
import { RouterLink } from 'vue-router'
</script>

<template>
  <div class="min-h-[100dvh] gradient-hero flex items-center justify-center p-4">
    <div class="text-center animate-fade-in">
      <span class="text-8xl">🐾</span>
      <h1 class="text-6xl font-extrabold tracking-tighter text-surface-900 mt-4">404</h1>
      <p class="text-xl text-surface-500 mt-4">页面走丢了，就像调皮的猫咪一样溜走了~</p>
      <RouterLink to="/" class="btn-primary mt-8 inline-flex">
        返回首页
      </RouterLink>
    </div>
  </div>
</template>
