<template>
  <div class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
    <div class="bg-white rounded-xl max-w-md w-full mx-4">
      <div class="p-4 border-b flex justify-between items-center">
        <h3 class="text-lg font-semibold text-gray-800">留言</h3>
        <button @click="$emit('close')" class="text-gray-400 hover:text-gray-600"><i class="fa fa-times text-xl"></i></button>
      </div>
      <div class="p-6">
        <form class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">接收者</label>
            <p class="text-base font-medium text-gray-800">{{ member?.username }}</p>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">留言标题 *</label>
            <input v-model="form.title" type="text" required placeholder="请输入留言标题" class="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-primary/30 focus:border-primary">
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">留言内容 *</label>
            <textarea v-model="form.content" required rows="4" placeholder="请输入留言内容" class="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-primary/30 focus:border-primary resize-none"></textarea>
          </div>
        </form>
      </div>
      <div class="p-4 border-t flex justify-end gap-3 bg-white">
        <button @click="$emit('close')" class="px-4 py-2 border rounded-lg hover:bg-gray-100">取消</button>
        <button @click="submitForm" class="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90" :disabled="sending">
          <i v-if="sending" class="fa fa-spinner fa-spin mr-1"></i><i class="fa fa-comment mr-1"></i>提交留言
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

defineProps({
  member: Object
})

const emit = defineEmits(['close', 'send'])

const form = ref({
  title: '',
  content: ''
})

const sending = ref(false)

function submitForm() {
  if (!form.value.title || !form.value.content) {
    window.$toast?.('请填写留言标题和内容', 'error')
    return
  }
  emit('send', { ...form.value })
}
</script>