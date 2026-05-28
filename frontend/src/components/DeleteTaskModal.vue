<template>
  <div v-if="visible" class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center">
    <div class="bg-white rounded-xl w-full max-w-md mx-4 p-6 relative">
      <button @click="close" class="absolute top-4 right-4 text-gray-400 hover:text-gray-600">
        <i class="fa fa-times"></i>
      </button>
      <h3 class="text-lg font-semibold mb-4 text-red-600">确认删除</h3>
      <p class="text-gray-600 mb-2">您确定要删除以下任务吗？</p>
      <p class="font-medium text-gray-800 mb-4">{{ taskTitle }}</p>
      <p class="text-sm text-gray-500 mb-4">此操作不可撤销。</p>
      <div class="flex justify-end gap-3">
        <button @click="close" class="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg">取消</button>
        <button @click="confirmDelete" class="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700">删除</button>
      </div>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  visible: Boolean,
  taskId: Number,
  taskTitle: String
})

const emit = defineEmits(['confirm', 'close'])

const visible = defineModel()

const close = () => {
  visible.value = false
  emit('close')
}

const confirmDelete = () => {
  emit('confirm')
}
</script>