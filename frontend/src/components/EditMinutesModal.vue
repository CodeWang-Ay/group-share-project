<template>
  <div class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
    <div class="bg-white rounded-xl max-w-3xl w-full mx-4 max-h-[85vh] overflow-y-auto">
      <div class="p-6">
        <div class="flex justify-between items-center mb-4">
          <h2 class="text-xl font-bold text-gray-800">编辑会议纪要</h2>
          <button @click="$emit('close')" class="text-gray-400 hover:text-gray-600">
            <i class="fa fa-times text-xl"></i>
          </button>
        </div>

        <div class="mb-4">
          <p class="text-sm text-gray-600">组会：<span class="font-medium text-gray-800">{{ meetingTitle }}</span></p>
        </div>

        <!-- 编辑/预览切换 -->
        <div class="flex items-center gap-2 mb-3">
          <button @click="editMode = 'edit'" :class="modeBtnClass('edit')"><i class="fa fa-edit mr-1"></i>编辑</button>
          <button @click="editMode = 'preview'" :class="modeBtnClass('preview')"><i class="fa fa-eye mr-1"></i>预览</button>
          <button @click="editMode = 'split'" :class="modeBtnClass('split')"><i class="fa fa-columns mr-1"></i>分屏</button>
          <span class="text-xs text-gray-400 ml-2">支持Markdown格式</span>
        </div>

        <!-- Markdown工具栏 -->
        <div v-if="editMode !== 'preview'" class="flex items-center gap-1 mb-2 p-2 bg-gray-50 rounded-lg border">
          <button @click="insertMarkdown('heading')" class="p-1.5 text-gray-600 hover:bg-gray-200 rounded" title="标题"><i class="fa fa-header"></i></button>
          <button @click="insertMarkdown('bold')" class="p-1.5 text-gray-600 hover:bg-gray-200 rounded" title="粗体"><i class="fa fa-bold"></i></button>
          <button @click="insertMarkdown('italic')" class="p-1.5 text-gray-600 hover:bg-gray-200 rounded" title="斜体"><i class="fa fa-italic"></i></button>
          <span class="text-gray-300 mx-1">|</span>
          <button @click="insertMarkdown('list')" class="p-1.5 text-gray-600 hover:bg-gray-200 rounded" title="无序列表"><i class="fa fa-list-ul"></i></button>
          <button @click="insertMarkdown('list-number')" class="p-1.5 text-gray-600 hover:bg-gray-200 rounded" title="有序列表"><i class="fa fa-list-ol"></i></button>
          <span class="text-gray-300 mx-1">|</span>
          <button @click="insertMarkdown('quote')" class="p-1.5 text-gray-600 hover:bg-gray-200 rounded" title="引用"><i class="fa fa-quote-left"></i></button>
          <button @click="insertMarkdown('code')" class="p-1.5 text-gray-600 hover:bg-gray-200 rounded" title="代码"><i class="fa fa-code"></i></button>
          <button @click="insertMarkdown('link')" class="p-1.5 text-gray-600 hover:bg-gray-200 rounded" title="链接"><i class="fa fa-link"></i></button>
          <span class="text-gray-300 mx-1">|</span>
          <button @click="insertMarkdown('checkbox')" class="p-1.5 text-gray-600 hover:bg-gray-200 rounded" title="待办事项"><i class="fa fa-check-square-o"></i></button>
          <button @click="insertMarkdown('table')" class="p-1.5 text-gray-600 hover:bg-gray-200 rounded" title="表格"><i class="fa fa-table"></i></button>
        </div>

        <!-- 编辑区域 -->
        <div class="mb-4">
          <!-- 编辑模式 -->
          <div v-if="editMode === 'edit'">
            <textarea ref="editTextarea" v-model="content" rows="12"
                      class="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-primary/30 font-mono text-sm"
                      placeholder="请填写会议纪要，支持Markdown格式"></textarea>
          </div>

          <!-- 预览模式 -->
          <div v-if="editMode === 'preview'">
            <div class="w-full min-h-[300px] px-4 py-3 border rounded-lg bg-gray-50 prose prose-sm max-w-none" v-html="renderedContent"></div>
          </div>

          <!-- 分屏模式 -->
          <div v-if="editMode === 'split'" class="grid grid-cols-2 gap-4">
            <textarea ref="splitTextarea" v-model="content" rows="12"
                      class="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-primary/30 font-mono text-sm"
                      placeholder="编辑区域"></textarea>
            <div class="w-full min-h-[300px] px-4 py-3 border rounded-lg bg-gray-50 prose prose-sm max-w-none overflow-y-auto" v-html="renderedContent"></div>
          </div>
        </div>

        <!-- 提示信息 -->
        <div class="bg-blue-50 rounded-lg p-3 mb-4">
          <p class="text-sm text-gray-600"><i class="fa fa-info-circle text-primary mr-1"></i>
            Markdown格式：<strong>**粗体**</strong>、<em>*斜体*</em>、`代码`、[链接](url)、- 列表、> 引用、## 标题</p>
        </div>

        <div class="pt-4 border-t flex justify-end gap-3">
          <button @click="$emit('close')" class="px-4 py-2 bg-gray-100 text-gray-600 rounded-lg hover:bg-gray-200">取消</button>
          <button @click="save" :disabled="saving" class="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 disabled:opacity-50">
            <i :class="saving ? 'fa fa-spinner fa-spin' : 'fa fa-check'" class="mr-1"></i>保存纪要
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { marked } from 'marked'

const props = defineProps({
  meetingId: Number,
  meetingTitle: String,
  initialContent: String
})

const emit = defineEmits(['close', 'save'])

const content = ref(props.initialContent || '')
const editMode = ref('edit')
const saving = ref(false)
const editTextarea = ref(null)
const splitTextarea = ref(null)

marked.setOptions({ breaks: true, gfm: true })

const renderedContent = computed(() => {
  return marked.parse(content.value || '')
})

function modeBtnClass(mode) {
  return editMode.value === mode
    ? 'px-3 py-1 text-sm bg-primary text-white rounded-lg'
    : 'px-3 py-1 text-sm bg-gray-100 text-gray-600 rounded-lg hover:bg-gray-200'
}

function insertMarkdown(type) {
  const textarea = editMode.value === 'split' ? splitTextarea.value : editTextarea.value
  if (!textarea) return

  const start = textarea.selectionStart
  const end = textarea.selectionEnd
  const selectedText = content.value.substring(start, end)
  let insertText = ''

  switch (type) {
    case 'heading': insertText = selectedText ? `## ${selectedText}` : '## 标题'; break
    case 'bold': insertText = selectedText ? `**${selectedText}**` : '**粗体文本**'; break
    case 'italic': insertText = selectedText ? `*${selectedText}*` : '*斜体文本*'; break
    case 'list': insertText = selectedText ? `- ${selectedText}` : '- 列表项'; break
    case 'list-number': insertText = selectedText ? `1. ${selectedText}` : '1. 列表项'; break
    case 'quote': insertText = selectedText ? `> ${selectedText}` : '> 引用内容'; break
    case 'code': insertText = selectedText ? `\`${selectedText}\`` : '`代码`'; break
    case 'link': insertText = selectedText ? `[${selectedText}](url)` : '[链接文字](url)'; break
    case 'checkbox': insertText = selectedText ? `- [ ] ${selectedText}` : '- [ ] 待办事项'; break
    case 'table': insertText = '| 列1 | 列2 | 列3 |\n|-----|-----|-----|\n| 内容1 | 内容2 | 内容3 |'; break
  }

  content.value = content.value.substring(0, start) + insertText + content.value.substring(end)
}

async function save() {
  saving.value = true
  emit('save', content.value.trim())
  saving.value = false
}

onMounted(() => {
  content.value = props.initialContent || ''
})
</script>