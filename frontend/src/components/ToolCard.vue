<template>
  <div class="border border-gray-100 rounded-lg p-4 transition-all duration-300 hover:shadow-lg hover:-translate-y-1">
    <div v-if="tag" class="flex justify-between items-start mb-2">
      <h4 class="font-semibold">{{ title }}</h4>
      <span :class="tagClass">{{ tag }}</span>
    </div>
    <h4 v-else class="font-semibold mb-2">{{ title }}</h4>
    <p class="text-gray-600 text-sm mb-3">{{ desc }}</p>
    <a :href="url" target="_blank" :class="linkClass" class="inline-flex items-center text-sm font-medium hover:underline">
      访问网站 <i class="fa fa-external-link ml-1"></i>
    </a>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  title: String,
  desc: String,
  url: String,
  tag: String,
  tagClass: String,
  color: String
})

const colorMap = {
  primary: 'text-primary',
  secondary: 'text-secondary',
  accent: 'text-accent',
  green: 'text-green-600',
  orange: 'text-orange-500',
  red: 'text-red-500',
  teal: 'text-teal-600',
  purple: 'text-purple-600'
}

const linkClass = computed(() => colorMap[props.color] || 'text-primary')
</script>