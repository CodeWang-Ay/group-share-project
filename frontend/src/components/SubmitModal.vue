<template>
  <div v-if="visible" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
    <div class="bg-white rounded-xl shadow-xl w-full max-w-lg mx-4 overflow-hidden">
      <div class="p-4 border-b flex justify-between items-center">
        <h3 class="font-semibold text-lg">{{ editingId ? '编辑研究进展' : '提交研究进展' }}</h3>
        <button @click="close" class="p-2 hover:bg-gray-100 rounded-lg">
          <i class="fa fa-times text-gray-500"></i>
        </button>
      </div>

      <form @submit.prevent="submitForm" class="p-4 space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">研究方向</label>
          <input v-model="form.research_direction" type="text" class="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/50" required>
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">本周进展</label>
          <textarea v-model="form.weekly_progress" rows="3" class="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/50" required></textarea>
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">下周计划</label>
          <textarea v-model="form.next_goal" rows="2" class="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/50"></textarea>
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">遇到的困难（可选）</label>
          <textarea v-model="form.difficulties" rows="2" class="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/50"></textarea>
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">完成度</label>
          <div class="flex items-center gap-3">
            <input v-model.number="form.completion_rate" type="range" min="0" max="100" class="w-full">
            <span class="text-sm text-gray-600 w-12">{{ form.completion_rate }}%</span>
          </div>
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">附件（可选）</label>
          <input type="file" @change="handleFileChange" multiple class="w-full px-3 py-2 border rounded-lg text-sm">
          <div v-if="form.attachments && form.attachments.length > 0" class="mt-2 flex flex-wrap gap-2">
            <span v-for="f in form.attachments" :key="f" class="text-xs bg-gray-100 px-2 py-1 rounded">{{ f }}</span>
          </div>
        </div>

        <div class="flex justify-end gap-2 pt-4 border-t">
          <button type="button" @click="close" class="px-4 py-2 border rounded-lg hover:bg-gray-50">取消</button>
          <button type="submit" class="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90">
            {{ editingId ? '更新' : '提交' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import * as api from '../api/research_progress'

const props = defineProps({
  visible: Boolean,
  editingId: Number,
  researchDirection: String,
  existingAttachments: Array,
  initialData: Object
})

const emit = defineEmits(['update:modelValue', 'submit', 'close'])

const visible = defineModel()

const form = ref({
  research_direction: '',
  weekly_progress: '',
  next_goal: '',
  difficulties: '',
  completion_rate: 50,
  attachments: []
})

const uploadedFiles = ref([])

// 监听visible变化，初始化表单
watch(visible, (val) => {
  if (val) {
    if (props.editingId && props.initialData) {
      // 编辑模式：使用initialData初始化
      form.value = {
        research_direction: props.initialData.research_direction || '',
        weekly_progress: props.initialData.weekly_progress || '',
        next_goal: props.initialData.next_goal || '',
        difficulties: props.initialData.difficulties || '',
        completion_rate: props.initialData.completion_rate || 50,
        attachments: props.initialData.attachments || props.existingAttachments || []
      }
    } else {
      // 新增模式
      form.value = {
        research_direction: props.researchDirection || '',
        weekly_progress: '',
        next_goal: '',
        difficulties: '',
        completion_rate: 50,
        attachments: []
      }
    }
    uploadedFiles.value = []
  }
})

const handleFileChange = async (e) => {
  const files = e.target.files
  console.log('选择文件:', files)
  if (files && files.length > 0) {
    for (const file of files) {
      try {
        console.log('上传文件:', file.name)
        const res = await api.uploadFile(file)
        console.log('上传响应:', res.data)
        if (res.data.success) {
          uploadedFiles.value.push(res.data.data.filename)
          form.value.attachments.push(res.data.data.filename)
          console.log('当前 attachments:', form.value.attachments)
        } else {
          console.error('上传失败:', res.data.message)
        }
      } catch (err) {
        console.error('文件上传失败:', err)
      }
    }
  }
}

const submitForm = () => {
  console.log('提交表单数据:', form.value)
  console.log('提交 attachments:', form.value.attachments)
  emit('submit', {
    research_direction: form.value.research_direction,
    weekly_progress: form.value.weekly_progress,
    next_goal: form.value.next_goal,
    difficulties: form.value.difficulties,
    completion_rate: form.value.completion_rate,
    attachments: form.value.attachments
  })
}

const close = () => {
  visible.value = false
  emit('close')
}
</script>