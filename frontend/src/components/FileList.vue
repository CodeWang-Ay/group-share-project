<template>
  <div class="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
    <div class="p-6 border-b flex justify-between items-center">
      <h2 class="font-bold text-lg">{{ title }}</h2>
      <router-link to="/report-materials" class="text-primary text-sm hover:underline">查看全部</router-link>
    </div>
    <div class="divide-y divide-gray-100">
      <div v-if="loading" class="p-4 text-center text-gray-500">
        <i class="fa fa-spinner fa-spin mr-2"></i>加载中...
      </div>
      <div v-else-if="!files.length" class="p-4 text-center text-gray-500">暂无最近提交的材料</div>
      <template v-else>
        <div v-for="f in files" :key="f.id" class="p-4 hover:bg-gray-50">
          <div class="flex items-start gap-3">
            <div :class="['w-10 h-10 rounded flex items-center justify-center', iconBgClass(f.file_type)]">
              <i :class="['fa', iconClass(f.file_type), 'text-xl']"></i>
            </div>
            <div class="flex-1">
              <div class="flex flex-wrap justify-between gap-2">
                <h3 class="font-medium">{{ f.filename }}</h3>
                <span class="text-xs bg-blue-100 text-blue-800 px-2 py-0.5 rounded">{{ f.uploader_name || '未知' }}</span>
              </div>
              <p class="text-sm text-gray-500 mt-1">{{ f.meeting_title || '研究材料' }} · {{ formatDate(f.uploaded_at) }}</p>
            </div>
          </div>
        </div>
      </template>
    </div>
    <div class="p-4 border-t text-center">
      <router-link to="/share-file" class="text-primary text-sm hover:underline">浏览更多资料</router-link>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  title: String,
  files: { type: Array, default: [] },
  loading: { type: Boolean, default: false }
})

function iconClass(type) {
  if (type?.includes('pdf')) return 'fa-file-pdf-o text-red-500'
  if (type?.includes('ppt')) return 'fa-file-powerpoint-o text-orange-500'
  if (type?.includes('excel') || type?.includes('xls')) return 'fa-file-excel-o text-green-500'
  return 'fa-file-o text-gray-500'
}

function iconBgClass(type) {
  if (type?.includes('pdf')) return 'bg-red-100'
  if (type?.includes('ppt')) return 'bg-orange-100'
  if (type?.includes('excel') || type?.includes('xls')) return 'bg-green-100'
  return 'bg-gray-100'
}

function formatDate(d) {
  return d ? new Date(d).toLocaleDateString('zh-CN') : ''
}
</script>