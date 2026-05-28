<template>
  <div class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
    <div class="bg-white rounded-xl max-w-md w-full mx-4">
      <div class="p-6">
        <div class="flex items-center justify-center w-12 h-12 bg-yellow-100 rounded-full mx-auto mb-4">
          <i class="fa fa-key text-yellow-600"></i>
        </div>
        <h3 class="text-lg font-semibold text-gray-800 text-center mb-2">重置密码</h3>
        <p class="text-gray-600 text-center mb-4">确定要重置成员 <span class="font-medium">{{ member?.username }}</span> 的密码吗？</p>
        <div class="bg-gray-50 rounded-lg p-4 mb-4">
          <label class="block text-sm font-medium text-gray-700 mb-2">新密码</label>
          <div class="flex items-center gap-2">
            <input type="text" value="123456" readonly class="flex-1 px-3 py-2 border rounded-lg bg-gray-100 text-gray-600">
            <button @click="copyPassword" class="px-3 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600">
              <i :class="copied ? 'fa fa-check' : 'fa fa-copy'"></i>
            </button>
          </div>
          <p class="text-xs text-gray-500 mt-2">默认密码为 "123456"，可以复制后告知用户</p>
        </div>
        <div class="flex justify-center gap-3">
          <button @click="$emit('close')" class="px-4 py-2 border rounded-lg hover:bg-gray-100">取消</button>
          <button @click="$emit('confirm')" class="px-4 py-2 bg-yellow-500 text-white rounded-lg hover:bg-yellow-600" :disabled="resetting">
            <i v-if="resetting" class="fa fa-spinner fa-spin mr-1"></i>确认重置
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

const copied = ref(false)
const resetting = ref(false)

async function copyPassword() {
  try {
    await navigator.clipboard.writeText('123456')
    copied.value = true
    setTimeout(() => copied.value = false, 2000)
  } catch (e) {
    window.$toast?.('复制失败', 'error')
  }
}
</script>