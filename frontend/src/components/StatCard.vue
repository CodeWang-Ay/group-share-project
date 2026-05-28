<template>
  <div class="bg-white rounded-xl shadow-sm p-6 border border-gray-100">
    <div class="flex items-center justify-between">
      <div>
        <p class="text-gray-500 text-sm">{{ title }}</p>
        <h3 class="text-2xl font-bold mt-1">
          <span v-if="loading">-</span>
          <span v-else>{{ value }}</span>
        </h3>
      </div>
      <div :class="['w-12 h-12 rounded-full flex items-center justify-center', bgColorClass]">
        <i :class="['fa', icon, 'text-xl', textColorClass]"></i>
      </div>
    </div>
    <div class="mt-4 text-sm">
      <slot name="trend" />
      <slot name="footer" />
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  title: String,
  value: { type: [Number, String], default: 0 },
  icon: String,
  color: { type: String, default: 'primary' },
  loading: { type: Boolean, default: false }
})

const colorMap = {
  primary: { bg: 'bg-primary/10', text: 'text-primary' },
  secondary: { bg: 'bg-secondary/10', text: 'text-secondary' },
  accent: { bg: 'bg-accent/10', text: 'text-accent' },
  orange: { bg: 'bg-orange-100', text: 'text-orange-500' }
}

const bgColorClass = computed(() => colorMap[props.color]?.bg || 'bg-primary/10')
const textColorClass = computed(() => colorMap[props.color]?.text || 'text-primary')
</script>