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
  to: String,
  active: { type: Boolean, default: false }
})

const route = useRoute()

const isActive = computed(() => {
  // 如果传递了 active prop，优先使用它
  if (props.active) return true
  // 否则根据路由判断
  return props.to && route.path === props.to
})

const itemClass = computed(() => [
  'flex items-center gap-3 p-3 rounded-lg transition-all cursor-pointer',
  isActive.value
    ? 'bg-primary/10 text-primary font-medium'
    : 'hover:bg-gray-100'
])
</script>