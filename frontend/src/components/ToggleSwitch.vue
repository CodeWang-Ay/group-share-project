<template>
  <label class="relative inline-flex items-center cursor-pointer">
    <input type="checkbox" :checked="modelValue" @change="toggle" class="sr-only peer">
    <div class="w-9 h-5 bg-gray-200 peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-primary/30 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-primary"></div>
  </label>
</template>

<script setup>
const props = defineProps({
  modelValue: { type: Boolean, default: false }
})

const emit = defineEmits(['update:modelValue', 'change'])

function toggle() {
  emit('update:modelValue', !props.modelValue)
  emit('change')
}
</script>