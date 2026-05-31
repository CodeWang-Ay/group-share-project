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
          <p class="text-xs text-gray-500 mt-1">支持上传多个文件，点击文件名右侧按钮可删除</p>

          <!-- 附件列表 -->
          <div v-if="form.attachments && form.attachments.length > 0" class="mt-3 space-y-2">
            <div v-for="(f, index) in form.attachments" :key="f"
                 class="flex items-center justify-between p-2 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
              <div class="flex items-center gap-2">
                <div :class="getFileIconClass(f)" class="w-8 h-8 rounded flex items-center justify-center">
                  <i class="fa fa-file-o"></i>
                </div>
                <span class="text-sm text-gray-700 truncate max-w-[250px]">{{ f }}</span>
                <span v-if="!isExistingFile(f)" class="text-xs text-green-600">(新上传)</span>
              </div>
              <button type="button" @click="removeAttachment(index, f)"
                      class="px-2 py-1 text-red-500 hover:bg-red-50 rounded text-xs transition-colors">
                <i class="fa fa-trash-o mr-1"></i>删除
              </button>
            </div>
          </div>
          <div v-else class="mt-2 text-sm text-gray-400 italic">暂无附件</div>
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
const existingFileList = ref([]) // 已存在的附件列表（编辑模式）

// 监听visible变化，初始化表单
watch(visible, (val) => {
  if (val) {
    // 记录已存在的附件（用于区分新增和原有的）
    existingFileList.value = props.existingAttachments || []

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

// 判断是否是已存在的文件（编辑模式下的原有附件）
const isExistingFile = (filename) => {
  return existingFileList.value.includes(filename)
}

// 根据文件类型返回图标样式
const getFileIconClass = (filename) => {
  const ext = filename.split('.').pop()?.toLowerCase() || ''
  const typeMap = {
    pdf: 'text-red-500 bg-red-50',
    doc: 'text-blue-500 bg-blue-50',
    docx: 'text-blue-500 bg-blue-50',
    ppt: 'text-orange-500 bg-orange-50',
    pptx: 'text-orange-500 bg-orange-50',
    xls: 'text-green-500 bg-green-50',
    xlsx: 'text-green-500 bg-green-50',
    zip: 'text-purple-500 bg-purple-50',
    rar: 'text-purple-500 bg-purple-50',
    jpg: 'text-yellow-500 bg-yellow-50',
    jpeg: 'text-yellow-500 bg-yellow-50',
    png: 'text-yellow-500 bg-yellow-50',
    mp4: 'text-pink-500 bg-pink-50'
  }
  return typeMap[ext] || 'text-gray-500 bg-gray-50'
}

// 删除附件
const removeAttachment = async (index, filename) => {
  // 先尝试删除服务器上的文件
  try {
    const res = await api.deleteFileByName(filename)
    if (res.data.success) {
      console.log('文件删除成功:', filename)
    } else {
      console.error('文件删除失败:', res.data.message)
      // 即使服务器删除失败，也从列表中移除（可能文件已经不存在）
    }
  } catch (err) {
    console.error('删除文件请求失败:', err)
  }

  // 从 attachments 数组中移除
  form.value.attachments.splice(index, 1)

  // 如果是本次新上传的文件，也从 uploadedFiles 中移除
  const uploadedIndex = uploadedFiles.value.indexOf(filename)
  if (uploadedIndex > -1) {
    uploadedFiles.value.splice(uploadedIndex, 1)
  }

  console.log('剩余 attachments:', form.value.attachments)
}

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