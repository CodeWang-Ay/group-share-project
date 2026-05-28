<template>
  <router-link v-if="to" :to="to" :class="itemClass">
    <i :class="['fa', icon, 'w-5 text-center']"></i>
    <span>{{ text }}</span>
  </router-link>
  <a v-else :href="href" :class="itemClass">
    <i :class="['fa', icon, 'w-5 text-center']"></i>
    <span>{{ text }}</span>
  </a>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const props = defineProps({
  icon: String,
  text: String,
  href: { type: String, default: '#' },
  to: String
})

const route = useRoute()

const isActive = computed(() => props.to && route.path === props.to)

const itemClass = computed(() => [
  'flex items-center gap-3 p-3 rounded-lg transition-all cursor-pointer',
  isActive.value
    ? 'bg-primary/10 text-primary font-medium'
    : 'hover:bg-gray-100'
])
</script>