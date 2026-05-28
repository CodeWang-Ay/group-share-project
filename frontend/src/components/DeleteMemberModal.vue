<template>
  <div class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
    <div class="bg-white rounded-xl max-w-md w-full mx-4">
      <div class="p-6">
        <div class="flex items-center justify-center w-12 h-12 bg-red-100 rounded-full mx-auto mb-4">
          <i class="fa fa-exclamation-triangle text-red-600"></i>
        </div>
        <h3 class="text-lg font-semibold text-gray-800 text-center mb-2">确认删除成员</h3>
        <p class="text-gray-600 text-center mb-6">确定要删除成员 <span class="font-medium">{{ member?.username }}</span> 吗？此操作不可撤销。</p>
        <div class="flex justify-center gap-3">
          <button @click="$emit('close')" class="px-4 py-2 border rounded-lg hover:bg-gray-100">取消</button>
          <button @click="$emit('confirm')" class="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700" :disabled="deleting">
            <i v-if="deleting" class="fa fa-spinner fa-spin mr-1"></i>确认删除
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

defineProps({
  member: Object
})

defineEmits(['close', 'confirm'])

const deleting = ref(false)
</script>