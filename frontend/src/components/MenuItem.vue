<template>
  <a :href="href" :class="itemClass" @click="onClick">
    <i :class="['fa', icon, 'w-5 text-center']"></i>
    <span>{{ text }}</span>
  </a>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  icon: String,
  text: String,
  href: { type: String, default: '#' },
  active: Boolean
})

const emit = defineEmits(['click'])

const itemClass = computed(() => [
  'flex items-center gap-3 p-3 rounded-lg transition-all cursor-pointer',
  props.active
    ? 'bg-primary/10 text-primary font-medium'
    : 'hover:bg-gray-100'
])

function onClick(e) {
  emit('click', e)
}
</script>