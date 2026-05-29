<template>
  <div v-if="visible" class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
    <div class="bg-white rounded-xl shadow-xl w-full max-w-md overflow-hidden">
      <!-- 模态框头部 -->
      <div class="p-4 border-b border-gray-200 flex items-center justify-between">
        <h3 class="font-semibold text-gray-800">批量设置标签</h3>
        <button @click="close" class="p-2 hover:bg-gray-100 rounded-lg">
          <i class="fa fa-times text-gray-500"></i>
        </button>
      </div>

      <!-- 内容区 -->
      <div class="p-6">
        <p class="text-sm text-gray-600 mb-4">为 <span class="font-medium text-primary">{{ selectedCount }}</span> 篇文献设置标签</p>

        <!-- 快捷标签 -->
        <div class="flex flex-wrap gap-2 mb-4">
          <span v-for="tag in quickTags" :key="tag"
                @click="selectTag(tag)"
                :class="['tag-badge cursor-pointer px-2 py-1 rounded text-xs font-medium transition-colors',
                         selectedTag === tag ? 'ring-2 ring-primary' : '',
                         getTagClass(tag)]">
            {{ tag }}
          </span>
        </div>

        <!-- 新标签输入 -->
        <input v-model="selectedTag" type="text" placeholder="添加新标签"
               class="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-primary/30 focus:border-primary">
      </div>

      <!-- 底部操作 -->
      <div class="p-4 border-t border-gray-200 flex items-center justify-end gap-3">
        <button @click="close" class="px-4 py-2 border border-gray-200 rounded-lg hover:bg-gray-50">
          取消
        </button>
        <button @click="apply" :disabled="!selectedTag || applying"
                class="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 disabled:opacity-50">
          <i class="fa fa-check mr-1"></i>应用
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { paperApi } from '../api/paper'

const visible = defineModel()
const props = defineProps({
  selectedPapers: Array,
  libraryType: String
})

const emit = defineEmits(['applied', 'close'])

const selectedTag = ref('')
const applying = ref(false)

const quickTags = ['Transformer', 'BERT', 'CNN', '大模型', 'NLP', '计算机视觉']

const selectedCount = computed(() => props.selectedPapers?.length || 0)

const getTagClass = (tag) => {
  const classes = {
    'Transformer': 'bg-blue-100 text-blue-700',
    'BERT': 'bg-purple-100 text-purple-700',
    'CNN': 'bg-orange-100 text-orange-700',
    '大模型': 'bg-red-100 text-red-700',
    'NLP': 'bg-green-100 text-green-700',
    '计算机视觉': 'bg-gray-100 text-gray-700'
  }
  return classes[tag] || 'bg-gray-100 text-gray-700'
}

const selectTag = (tag) => {
  selectedTag.value = tag
}

const apply = async () => {
  if (!selectedTag.value || props.selectedPapers?.length === 0) return

  applying.value = true
  try {
    const res = await paperApi.batchSetTags(props.selectedPapers, selectedTag.value, props.libraryType)
    if (res.data.success) {
      emit('applied')
      close()
    } else {
      alert(res.data.message || '设置失败')
    }
  } catch (e) {
    console.error('批量设置标签失败:', e)
    alert('批量设置标签失败')
  } finally {
    applying.value = false
  }
}

const close = () => {
  visible.value = false
  selectedTag.value = ''
  emit('close')
}
</script>

<style scoped>
.tag-badge:hover {
  opacity: 80;
}
</style>