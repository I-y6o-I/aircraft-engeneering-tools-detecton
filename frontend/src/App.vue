<script setup lang="ts">
import { RouterView } from 'vue-router'
import NotificationSystem from '@/components/NotificationSystem.vue'
</script>

<template>
  <RouterView />
  <NotificationSystem />
</template>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  line-height: 1.5;
  color: #1f2937;
  background: #0f172a;
}

#app {
  min-height: 100vh;
}
</style>