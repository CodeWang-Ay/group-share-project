<template>
  <div v-if="visible" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
    <div class="bg-white rounded-xl shadow-xl w-full max-w-lg mx-4 overflow-hidden">
      <div class="p-4 border-b flex justify-between items-center">
        <h3 class="font-semibold text-lg">批量设置提交周期</h3>
        <button @click="close" class="p-2 hover:bg-gray-100 rounded-lg">
          <i class="fa fa-times text-gray-500"></i>
        </button>
      </div>

      <div class="p-4 space-y-4">
        <!-- 学生选择 -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">选择学生</label>
          <div class="border rounded-lg p-3 max-h-48 overflow-y-auto space-y-1">
            <label v-for="student in studentList" :key="student.user_id" class="flex items-center gap-2 p-2 hover:bg-gray-50 rounded cursor-pointer">
              <input type="checkbox" v-model="selectedIds" :value="student.user_id" class="rounded">
              <span class="text-gray-700">{{ student.username }}（{{ student.degree_type || '学生' }}）</span>
            </label>
          </div>
        </div>

        <!-- 周期类型 -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">提交周期</label>
          <select v-model="periodType" class="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/50">
            <option value="weekly">每周</option>
            <option value="biweekly">每两周</option>
            <option value="monthly">每月</option>
          </select>
        </div>

        <!-- 提醒天数 -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">提醒天数</label>
          <input v-model.number="reminderDays" type="number" min="1" max="7" class="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/50">
          <p class="text-xs text-gray-500 mt-1">在周期结束前多少天提醒</p>
        </div>

        <div class="flex justify-end gap-2 pt-4 border-t">
          <button @click="close" class="px-4 py-2 border rounded-lg hover:bg-gray-50">取消</button>
          <button @click="submit" class="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90" :disabled="selectedIds.length === 0">
            确认设置
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({
  visible: Boolean,
  studentList: Array
})

const emit = defineEmits(['update:modelValue', 'submit'])

const visible = defineModel()
const selectedIds = ref([])
const periodType = ref('weekly')
const reminderDays = ref(3)

const submit = () => {
  if (selectedIds.value.length === 0) return
  emit('submit', {
    user_ids: selectedIds.value,
    period_type: periodType.value,
    reminder_days: reminderDays.value
  })
  selectedIds.value = []
}

const close = () => {
  visible.value = false
  selectedIds.value = []
}
</script>