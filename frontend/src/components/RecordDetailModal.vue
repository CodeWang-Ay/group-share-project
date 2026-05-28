<template>
  <div class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
    <div class="bg-white rounded-xl max-w-4xl w-full mx-4 max-h-[85vh] flex flex-col overflow-hidden">
      <!-- 头部 -->
      <div class="p-6 border-b flex-shrink-0">
        <div class="flex justify-between items-start mb-2">
          <div>
            <span class="bg-green-100 text-green-700 text-xs px-3 py-1 rounded-full font-medium">已召开</span>
            <span class="bg-gray-100 text-gray-600 text-xs px-3 py-1 rounded-full font-medium ml-2">{{ typeText }}</span>
          </div>
          <button @click="$emit('close')" class="text-gray-400 hover:text-gray-600">
            <i class="fa fa-times text-xl"></i>
          </button>
        </div>
        <h2 class="text-xl font-bold text-gray-800">{{ meeting?.title }}</h2>
      </div>

      <!-- 内容 -->
      <div class="flex-1 overflow-y-auto p-6">
        <!-- 基本信息 -->
        <div class="bg-gray-50 rounded-lg p-4 mb-4">
          <div class="grid grid-cols-2 gap-3 text-sm">
            <div class="flex items-center gap-2"><i class="fa fa-calendar text-gray-400 w-5"></i><span>{{ formattedDate }}</span></div>
            <div class="flex items-center gap-2"><i class="fa fa-clock-o text-gray-400 w-5"></i><span>{{ meeting?.duration_total || 0 }}分钟</span></div>
            <div class="flex items-center gap-2"><i class="fa fa-map-marker text-gray-400 w-5"></i><span>{{ meeting?.location || '待定' }}</span></div>
            <div class="flex items-center gap-2"><i class="fa fa-users text-gray-400 w-5"></i><span>{{ presenters.length }} 位汇报人</span></div>
          </div>
          <div v-if="presenters.length > 0" class="mt-3 pt-3 border-t border-gray-200">
            <div class="text-sm text-gray-600 mb-1">汇报人：</div>
            <div>
              <span v-for="p in presenters" :key="p.id" class="inline-block px-2 py-1 bg-gray-100 rounded text-sm mr-2">
                {{ p.real_name || p.username }} ({{ p.duration_minutes }}分钟)
              </span>
            </div>
          </div>
        </div>

        <!-- 会议纪要 -->
        <div class="bg-blue-50 rounded-lg p-4 mb-4">
          <div class="flex justify-between items-center mb-2">
            <div class="flex items-center gap-2">
              <i class="fa fa-file-text-o text-primary"></i>
              <span class="font-medium text-gray-800">会议纪要</span>
              <span v-if="meeting?.minutes" class="text-green-600 text-xs"><i class="fa fa-check-circle"></i> 已填写</span>
              <span v-else class="text-orange-500 text-xs"><i class="fa fa-exclamation-circle"></i> 待填写</span>
            </div>
            <button @click="$emit('edit', meeting)" class="text-sm text-primary hover:text-primary/80"><i class="fa fa-edit"></i> 编辑</button>
          </div>
          <div class="max-h-[400px] overflow-y-auto">
            <div v-if="meeting?.minutes" class="prose prose-sm max-w-none" v-html="renderedMinutes"></div>
            <p v-else class="text-gray-400 italic">暂无会议纪要，点击"编辑"按钮填写</p>
          </div>
        </div>

        <!-- 汇报材料区域 -->
        <div class="bg-purple-50 rounded-lg p-4 mb-4">
          <div class="flex justify-between items-center mb-2">
            <div class="flex items-center gap-2">
              <i class="fa fa-file-powerpoint-o text-purple-600"></i>
              <span class="font-medium text-gray-800">汇报材料</span>
            </div>
            <button @click="loadMaterials" class="text-sm text-primary hover:text-primary/80"><i class="fa fa-refresh"></i> 刷新</button>
          </div>
          <div v-if="loadingMaterials" class="text-sm text-gray-400"><i class="fa fa-spinner fa-spin"></i> 加载中...</div>
          <div v-else-if="materials.length === 0" class="text-sm text-gray-400">暂无材料</div>
          <div v-else class="space-y-2">
            <div v-for="f in materials" :key="f.id" class="flex items-center justify-between p-2 bg-white rounded">
              <span class="text-sm"><i class="fa fa-file-o mr-1 text-gray-400"></i>{{ f.filename }}</span>
              <button @click="downloadFile(f.id, f.filename)" class="text-xs text-primary hover:underline"><i class="fa fa-download"></i></button>
            </div>
          </div>
        </div>

        <!-- 会议描述 -->
        <div class="border-t border-gray-100 pt-4">
          <p class="text-gray-600 font-medium mb-2">会议描述：</p>
          <p class="text-gray-800">{{ meeting?.description || '无描述' }}</p>
        </div>
      </div>

      <!-- 底部 -->
      <div class="p-4 border-t flex justify-end gap-3 flex-shrink-0 bg-white">
        <button @click="$emit('close')" class="px-4 py-2 bg-gray-100 text-gray-600 rounded-lg hover:bg-gray-200">关闭</button>
        <button @click="$emit('edit', meeting)" class="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90"><i class="fa fa-edit mr-1"></i>编辑纪要</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { marked } from 'marked'
import { recordApi } from '../api/record'

const props = defineProps({
  meeting: Object
})

defineEmits(['close', 'edit'])

const materials = ref([])
const loadingMaterials = ref(false)

const typeMap = { regular: '常规组会', paper_reading: '论文研读', discussion: '专题讨论' }

const typeText = computed(() => typeMap[props.meeting?.meeting_type] || '常规组会')

const formattedDate = computed(() => {
  if (!props.meeting?.scheduled_at) return ''
  const d = new Date(props.meeting.scheduled_at)
  return `${d.getFullYear()}年${d.getMonth()+1}月${d.getDate()}日 ${String(d.getHours()).padStart(2,'0')}:${String(d.getMinutes()).padStart(2,'0')}`
})

const presenters = computed(() => props.meeting?.presenters || [])

const renderedMinutes = computed(() => {
  if (!props.meeting?.minutes) return ''
  marked.setOptions({ breaks: true, gfm: true })
  return marked.parse(props.meeting.minutes)
})

async function loadMaterials() {
  loadingMaterials.value = true
  materials.value = []
  for (const p of presenters.value) {
    try {
      const res = await recordApi.getPresenterFiles(p.id)
      if (res.data.files) {
        materials.value.push(...res.data.files)
      }
    } catch (e) {
      console.error('加载材料失败:', e)
    }
  }
  loadingMaterials.value = false
}

async function downloadFile(fileId, filename) {
  try {
    const res = await recordApi.downloadFile(fileId)
    const blob = res.data
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    document.body.appendChild(a)
    a.click()
    window.URL.revokeObjectURL(url)
    a.remove()
  } catch (e) {
    console.error('下载失败:', e)
    window.$toast?.('下载失败', 'error')
  }
}

onMounted(() => {
  loadMaterials()
})
</script>