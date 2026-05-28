<template>
  <div class="fixed top-4 left-1/2 -translate-x-1/2 z-[100] flex flex-col gap-2">
    <TransitionGroup name="toast">
      <div v-for="toast in toasts" :key="toast.id"
           :class="toastClass(toast.type)"
           class="flex items-center gap-3 px-4 py-3 rounded-xl shadow-lg">
        <i :class="toastIcon(toast.type)"></i>
        <span>{{ toast.message }}</span>
      </div>
    </TransitionGroup>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

const toasts = ref([])
let toastId = 0

function toastClass(type) {
  const map = {
    success: 'bg-green-50 text-green-600 border border-green-100',
    error: 'bg-red-50 text-red-600 border border-red-100',
    warning: 'bg-yellow-50 text-yellow-600 border border-yellow-100',
    info: 'bg-blue-50 text-blue-600 border border-blue-100'
  }
  return map[type] || map.info
}

function toastIcon(type) {
  const map = {
    success: 'fa fa-check-circle',
    error: 'fa fa-times-circle',
    warning: 'fa fa-exclamation-circle',
    info: 'fa fa-info-circle'
  }
  return map[type] || map.info
}

function show(message, type = 'info', duration = 3000) {
  const id = ++toastId
  toasts.value.push({ id, message, type })

  setTimeout(() => {
    toasts.value = toasts.value.filter(t => t.id !== id)
  }, duration)
}

// 全局方法
onMounted(() => {
  window.$toast = show
})

onUnmounted(() => {
  window.$toast = null
})

defineExpose({ show })
</script>

<style scoped>
.toast-enter-active {
  animation: slideDown 0.3s ease-out;
}
.toast-leave-active {
  animation: slideUp 0.3s ease-out;
}

@keyframes slideDown {
  from { opacity: 0; transform: translateY(-20px); }
  to { opacity: 1; transform: translateY(0); }
}
@keyframes slideUp {
  from { opacity: 1; transform: translateY(0); }
  to { opacity: 0; transform: translateY(-20px); }
}
</style>